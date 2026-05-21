from aiogram import Bot

from ..db.repository import Repository
from .ai import AIService
from .dnd import DNDService
from .filter import is_spam


class Responder:
    def __init__(self, bot: Bot, repo: Repository, ai: AIService, dnd: DNDService) -> None:
        self._bot = bot
        self._repo = repo
        self._ai = ai
        self._dnd = dnd

    async def handle(self, message, user_id: int) -> None:
        conn_id: str = message.business_connection_id
        chat_id: int = message.chat.id
        text: str = message.text or ""

        await self._repo.log_message(conn_id, chat_id, "incoming", text)

        conn = await self._repo.get_connection(conn_id)
        if not conn or not conn.can_reply:
            return

        if not await self._dnd.is_enabled(user_id):
            return

        recent = await self._repo.get_recent_messages(conn_id, chat_id)
        if is_spam(text, recent):
            return

        settings = await self._repo.get_settings(user_id)
        reply = await self._ai.generate_reply(text, settings.ai_context, recent)
        if not reply:
            return

        await self._bot.send_message(
            chat_id=chat_id,
            text=reply,
            business_connection_id=conn_id,
        )
        await self._repo.log_message(conn_id, chat_id, "outgoing", reply)
