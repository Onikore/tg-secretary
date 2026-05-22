from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..db.repository import Repository
from ..services.dnd import DNDService


def _parse_hhmm(value: str) -> int | None:
    parts = value.split(":")
    if len(parts) != 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if 0 <= h < 24 and 0 <= m < 60:
        return h * 60 + m
    return None


def _fmt_min(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"


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
            "/quiet HH:MM HH:MM — auto-reply only in this window\n"
            "/quiet off — auto-reply any time (when /dnd on)\n"
            "/status — current status\n"
            "/rules <text> — set global AI context\n"
            "/here <text> — set AI context for the active chat\n"
            "/here off — clear the active chat's context"
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
        if settings.quiet_start_min is not None and settings.quiet_end_min is not None:
            window = f"{_fmt_min(settings.quiet_start_min)}-{_fmt_min(settings.quiet_end_min)}"
        else:
            window = "any time"
        if settings.active_chat_id is not None:
            chat_ctx = await repo.get_chat_context(
                settings.active_conn_id, settings.active_chat_id
            )
            active = f"{settings.active_chat_id}"
            active += " (custom context)" if chat_ctx else " (uses global)"
        else:
            active = "(none yet)"
        await message.answer(
            f"DND: {state}\nQuiet hours: {window}\n"
            f"Active chat: {active}\nGlobal AI context: {context}"
        )

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

    @router.message(Command("quiet"))
    async def cmd_quiet(message: Message) -> None:
        if not _is_owner(message):
            return
        parts = (message.text or "").split()
        if len(parts) == 2 and parts[1] == "off":
            await repo.update_quiet_hours(message.from_user.id, None, None)
            await message.answer("Quiet hours cleared. Auto-reply any time (when /dnd on).")
            return
        if len(parts) == 3:
            start = _parse_hhmm(parts[1])
            end = _parse_hhmm(parts[2])
            if start is not None and end is not None:
                await repo.update_quiet_hours(message.from_user.id, start, end)
                await message.answer(
                    f"Quiet hours set: {parts[1]}-{parts[2]}. Auto-reply only in this window."
                )
                return
        await message.answer("Usage: /quiet HH:MM HH:MM | /quiet off")

    @router.message(Command("here"))
    async def cmd_here(message: Message) -> None:
        if not _is_owner(message):
            return
        settings = await repo.get_settings(message.from_user.id)
        if settings.active_conn_id is None or settings.active_chat_id is None:
            await message.answer("No active chat yet. It's set when someone messages you.")
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) == 2 and parts[1].strip() == "off":
            await repo.clear_chat_context(settings.active_conn_id, settings.active_chat_id)
            await message.answer("Active chat context cleared. Falls back to /rules.")
            return
        if len(parts) < 2:
            await message.answer("Usage: /here <context for the active chat> | /here off")
            return
        await repo.set_chat_context(
            settings.active_conn_id, settings.active_chat_id, parts[1]
        )
        await message.answer("Context set for the active chat.")

    return router
