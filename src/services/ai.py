import logging

import google.generativeai as genai

from ..db.models import MessageLog

logger = logging.getLogger(__name__)

_SYSTEM_DEFAULT = (
    "You are a secretary assistant. Reply briefly and naturally on behalf of the user. "
    "Use the same language as the incoming message."
)


class AIService:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    async def generate_reply(
        self,
        incoming_text: str,
        user_context: str,
        history: list[MessageLog],
    ) -> str | None:
        try:
            system = user_context.strip() if user_context.strip() else _SYSTEM_DEFAULT

            chat_history = []
            for msg in history[:-1]:  # exclude the latest incoming (added below)
                role = "user" if msg.direction == "incoming" else "model"
                chat_history.append({"role": role, "parts": [msg.text]})

            prompt = f"{system}\n\nMessage to reply to: {incoming_text}"
            response = await self._model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini error: %s", exc)
            return None
