from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..db.repository import Repository
from ..services.dnd import DNDService


def setup(dnd: DNDService, repo: Repository, owner_user_id: int) -> Router:
    router = Router()

    def _is_owner(message: Message) -> bool:
        return bool(message.from_user and message.from_user.id == owner_user_id)

    @router.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        if not _is_owner(message):
            return
        await message.answer(
            "Secretary bot is active.\n\n"
            "/dnd on — enable auto-reply\n"
            "/dnd off — disable auto-reply\n"
            "/status — current status\n"
            "/rules <text> — set AI context for replies"
        )

    @router.message(Command("dnd"))
    async def cmd_dnd(message: Message) -> None:
        if not _is_owner(message):
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2 or parts[1] not in ("on", "off"):
            await message.answer("Usage: /dnd on|off")
            return
        if parts[1] == "on":
            await dnd.enable(message.from_user.id)
            await message.answer("DND enabled. I will reply automatically to your messages.")
        else:
            await dnd.disable(message.from_user.id)
            await message.answer("DND disabled. Auto-reply is off.")

    @router.message(Command("status"))
    async def cmd_status(message: Message) -> None:
        if not _is_owner(message):
            return
        settings = await repo.get_settings(message.from_user.id)
        state = "ON" if settings.dnd_enabled else "OFF"
        context = settings.ai_context or "(not set)"
        await message.answer(f"DND: {state}\nAI context: {context}")

    @router.message(Command("rules"))
    async def cmd_rules(message: Message) -> None:
        if not _is_owner(message):
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Usage: /rules <context for AI, e.g. 'I am a developer, reply briefly'>")
            return
        await repo.update_ai_context(message.from_user.id, parts[1])
        await message.answer("AI context updated.")

    return router
