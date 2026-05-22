import logging

from google import genai
from google.genai import types

from ..db.models import MessageLog

logger = logging.getLogger(__name__)

_SYSTEM_DEFAULT = (
    "You are a secretary assistant. Reply briefly and naturally on behalf of the user. "
    "Use the same language as the incoming message."
)


class AIService:
    def __init__(
        self, api_key: str, model: str = "gemini-2.0-flash", proxy: str | None = None
    ) -> None:
        http_options = (
            types.HttpOptions(async_client_args={"proxy": proxy}) if proxy else None
        )
        self._client = genai.Client(api_key=api_key, http_options=http_options)
        self._model = model

    async def generate_reply(
        self,
        incoming_text: str,
        user_context: str,
        history: list[MessageLog],
    ) -> str | None:
        try:
            system = user_context.strip() if user_context.strip() else _SYSTEM_DEFAULT

            history_lines = []
            for msg in history:
                role = "User" if msg.direction == "incoming" else "You"
                history_lines.append(f"{role}: {msg.text}")

            history_block = "\n".join(history_lines)
            if history_block:
                prompt = f"{system}\n\nConversation:\n{history_block}\n\nReply to the last user message:"
            else:
                prompt = f"{system}\n\nMessage to reply to: {incoming_text}"

            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini error: %s", exc)
            return None
