from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import Base, Connection, MessageLog, Settings


class Repository:
    def __init__(self, db_path: str) -> None:
        self._engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        self._session = async_sessionmaker(self._engine, expire_on_commit=False)

    async def init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def upsert_connection(
        self, conn_id: str, user_id: int, can_reply: bool, is_active: bool
    ) -> None:
        async with self._session() as session:
            existing = await session.get(Connection, conn_id)
            if existing:
                existing.can_reply = can_reply
                existing.is_active = is_active
            else:
                session.add(
                    Connection(
                        business_connection_id=conn_id,
                        user_id=user_id,
                        can_reply=can_reply,
                        is_active=is_active,
                    )
                )
            await session.commit()

    async def get_connection(self, conn_id: str) -> Connection | None:
        async with self._session() as session:
            return await session.get(Connection, conn_id)

    async def get_settings(self, user_id: int) -> Settings:
        async with self._session() as session:
            s = await session.get(Settings, user_id)
            if not s:
                s = Settings(user_id=user_id)
                session.add(s)
                await session.commit()
            return s

    async def update_dnd(self, user_id: int, enabled: bool) -> None:
        async with self._session() as session:
            s = await session.get(Settings, user_id)
            if s:
                s.dnd_enabled = enabled
            else:
                session.add(Settings(user_id=user_id, dnd_enabled=enabled))
            await session.commit()

    async def update_ai_context(self, user_id: int, context: str) -> None:
        async with self._session() as session:
            s = await session.get(Settings, user_id)
            if s:
                s.ai_context = context
            else:
                session.add(Settings(user_id=user_id, ai_context=context))
            await session.commit()

    async def log_message(
        self, conn_id: str, chat_id: int, direction: str, text: str
    ) -> None:
        async with self._session() as session:
            session.add(
                MessageLog(
                    business_connection_id=conn_id,
                    chat_id=chat_id,
                    direction=direction,
                    text=text,
                )
            )
            await session.commit()

    async def get_recent_messages(
        self, conn_id: str, chat_id: int, limit: int = 10
    ) -> list[MessageLog]:
        async with self._session() as session:
            result = await session.execute(
                select(MessageLog)
                .where(MessageLog.business_connection_id == conn_id)
                .where(MessageLog.chat_id == chat_id)
                .order_by(MessageLog.created_at.asc())
                .limit(limit)
            )
            return list(result.scalars().all())
