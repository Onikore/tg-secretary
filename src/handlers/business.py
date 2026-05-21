from aiogram import Router
from aiogram.types import Message

from ..services.responder import Responder


def setup(responder: Responder, owner_user_id: int) -> Router:
    router = Router()

    @router.business_message()
    async def on_business_message(message: Message) -> None:
        await responder.handle(message, user_id=owner_user_id)

    @router.edited_business_message()
    async def on_edited_business_message(message: Message) -> None:
        pass  # No action on edits

    return router
