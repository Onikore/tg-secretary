from aiogram import Router
from aiogram.types import BusinessConnection

from ..db.repository import Repository


def setup(repo: Repository) -> Router:
    router = Router()

    @router.business_connection()
    async def on_business_connection(update: BusinessConnection) -> None:
        await repo.upsert_connection(
            conn_id=update.id,
            user_id=update.user.id,
            can_reply=update.can_reply,
            is_active=update.is_enabled,
        )

    return router
