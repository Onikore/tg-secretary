import re

from ..db.models import MessageLog

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


def is_spam(text: str, recent_messages: list[MessageLog]) -> bool:
    if len(text.strip()) < 3:
        return True
    if _URL_RE.search(text):
        return True
    incoming_texts = [m.text for m in recent_messages if m.direction == "incoming"]
    if incoming_texts.count(text) >= 3:
        return True
    return False
