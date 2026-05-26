import logging
from collections.abc import Callable
from datetime import UTC, datetime

from aiogram import Bot

logger = logging.getLogger(__name__)

from ..db.repository import Repository
from .ai import AIService
from .dnd import DNDService
from .filter import is_spam

_MEDIA_LABELS = [
    ("voice", "voice message"),
    ("video_note", "video note"),
    ("audio", "audio"),
    ("photo", "photo"),
    ("video", "video"),
    ("animation", "GIF"),
    ("document", "document"),
    ("sticker", "sticker"),
    ("contact", "contact"),
    ("location", "location"),
]


def describe_message(message) -> str:
    text = message.text or getattr(message, "caption", None)
    if text:
        return text
    for attr, label in _MEDIA_LABELS:
        if getattr(message, attr, None):
            return f"[{label}]"
    return ""


class Responder:
    def __init__(
        self,
        bot: Bot,
        repo: Repository,
        ai: AIService,
        dnd: DNDService,
        cooldown_min: int = 0,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._bot = bot
        self._repo = repo
        self._ai = ai
        self._dnd = dnd
        self._cooldown_min = cooldown_min
        self._now = now or (lambda: datetime.now(UTC).replace(tzinfo=None))

    async def handle(self, message, user_id: int) -> None:
        conn_id: str = message.business_connection_id
        chat_id: int = message.chat.id
        text: str = describe_message(message)

        await self._repo.log_message(conn_id, chat_id, "incoming", text)
        await self._repo.set_active_chat(user_id, conn_id, chat_id)

        logger.info("Incoming: conn=%s chat=%s text=%r", conn_id, chat_id, text[:80])

        conn = await self._repo.get_connection(conn_id)
        if not conn:
            logger.warning("Skip: connection %s not in DB (reconnect bot in Telegram settings)", conn_id)
            return
        if not conn.is_active:
            logger.warning("Skip: connection %s is_active=False", conn_id)
            return
        if not conn.can_reply:
            logger.warning("Skip: connection %s can_reply=False (Telegram Settings → Business → Chatbots → enable Reply)", conn_id)
            return

        if not await self._dnd.is_enabled(user_id):
            logger.info("Skip: DND is off for user %s (send /dnd on)", user_id)
            return

        recent = await self._repo.get_recent_messages(conn_id, chat_id)
        if is_spam(text, recent):
            logger.info("Skip: spam filter triggered for chat %s", chat_id)
            return

        if self._cooldown_min > 0 and await self._in_cooldown(conn_id, chat_id):
            logger.info("Skip: cooldown active for chat %s", chat_id)
            return

        settings = await self._repo.get_settings(user_id)
        chat_context = await self._repo.get_chat_context(conn_id, chat_id)
        context = chat_context or settings.ai_context
        reply = await self._ai.generate_reply(text, context, recent)
        if not reply:
            logger.warning("No reply generated for chat %s (Gemini returned empty)", chat_id)
            return

        await self._bot.send_message(
            chat_id=chat_id,
            text=reply,
            business_connection_id=conn_id,
        )
        await self._repo.log_message(conn_id, chat_id, "outgoing", reply)

    async def _in_cooldown(self, conn_id: str, chat_id: int) -> bool:
        last = await self._repo.get_last_outgoing(conn_id, chat_id)
        if last is None:
            return False
        elapsed = (self._now() - last.created_at).total_seconds()
        return elapsed < self._cooldown_min * 60
