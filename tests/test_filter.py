from src.db.models import MessageLog
from src.services.filter import is_spam


def make_msg(text: str, direction: str = "incoming") -> MessageLog:
    m = MessageLog()
    m.text = text
    m.direction = direction
    return m


def test_empty_message_is_spam():
    assert is_spam("", []) is True


def test_very_short_message_is_spam():
    assert is_spam("hi", []) is True


def test_url_message_is_spam():
    assert is_spam("check https://example.com for deals", []) is True


def test_www_url_is_spam():
    assert is_spam("visit www.example.com", []) is True


def test_flood_is_spam():
    history = [make_msg("hello") for _ in range(3)]
    assert is_spam("hello", history) is True


def test_normal_message_not_spam():
    assert is_spam("Hello, are you available tomorrow?", []) is False


def test_outgoing_messages_not_counted_as_flood():
    history = [make_msg("hello", direction="outgoing") for _ in range(3)]
    assert is_spam("hello", history) is False


def test_mixed_history_flood_only_counts_incoming():
    history = [make_msg("hello")] * 2 + [make_msg("hello", direction="outgoing")]
    assert is_spam("hello", history) is False
