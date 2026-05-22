from aiogram import Router
from aiogram.types import BusinessConnection

from ..db.repository import Repository


def can_reply(update: BusinessConnection) -> bool:
    # API 9.0+ delivers rights.can_reply; the top-level can_reply is deprecated
    # and arrives as None, so prefer rights and fall back for older payloads.
    if update.rights is not None:
        return bool(update.rights.can_reply)
    return bool(update.can_reply)


def setup(repo: Repository) -> Router:
    router = Router()

    @router.business_connection()
    async def on_business_connection(update: BusinessConnection) -> None:
        await repo.upsert_connection(
            conn_id=update.id,
            user_id=update.user.id,
            can_reply=can_reply(update),
            is_active=update.is_enabled,
        )

    return router
