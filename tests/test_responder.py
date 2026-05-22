from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.db.models import Connection, MessageLog, Settings
from src.services.responder import Responder, describe_message


@pytest.fixture
def bot():
    b = MagicMock()
    b.send_message = AsyncMock()
    return b


@pytest.fixture
def repo():
    r = MagicMock()
    r.log_message = AsyncMock()
    r.get_connection = AsyncMock()
    r.get_settings = AsyncMock()
    r.get_recent_messages = AsyncMock(return_value=[])
    return r


@pytest.fixture
def ai():
    a = MagicMock()
    a.generate_reply = AsyncMock(return_value="I'll be back shortly!")
    return a


@pytest.fixture
def dnd():
    d = MagicMock()
    d.is_enabled = AsyncMock(return_value=True)
    return d


@pytest.fixture
def active_connection():
    c = Connection()
    c.business_connection_id = "conn1"
    c.user_id = 1
    c.can_reply = True
    c.is_active = True
    return c


@pytest.fixture
def default_settings():
    s = Settings()
    s.user_id = 1
    s.dnd_enabled = True
    s.ai_context = "I am a developer"
    s.auto_filter_spam = True
    return s


@pytest.fixture
def message():
    m = MagicMock()
    m.business_connection_id = "conn1"
    m.chat.id = 100
    m.text = "Hello, are you available tomorrow?"
    return m


@pytest.fixture
def responder(bot, repo, ai, dnd):
    return Responder(bot, repo, ai, dnd)


async def test_replies_when_all_conditions_met(
    responder, message, repo, bot, active_connection, default_settings
):
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    await responder.handle(message, user_id=1)
    bot.send_message.assert_awaited_once()


async def test_no_reply_when_dnd_off(
    responder, message, repo, bot, dnd, active_connection, default_settings
):
    dnd.is_enabled.return_value = False
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    await responder.handle(message, user_id=1)
    bot.send_message.assert_not_awaited()


async def test_no_reply_when_cannot_reply(
    responder, message, repo, bot, active_connection, default_settings
):
    active_connection.can_reply = False
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    await responder.handle(message, user_id=1)
    bot.send_message.assert_not_awaited()


async def test_no_reply_when_connection_missing(responder, message, repo, bot):
    repo.get_connection.return_value = None
    await responder.handle(message, user_id=1)
    bot.send_message.assert_not_awaited()


async def test_no_reply_for_spam(
    responder, message, repo, bot, active_connection, default_settings
):
    message.text = "hi"  # too short — spam
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    await responder.handle(message, user_id=1)
    bot.send_message.assert_not_awaited()


async def test_no_reply_when_ai_returns_none(
    responder, message, repo, bot, ai, active_connection, default_settings
):
    ai.generate_reply.return_value = None
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    await responder.handle(message, user_id=1)
    bot.send_message.assert_not_awaited()


async def test_always_logs_incoming(responder, message, repo, active_connection, default_settings):
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    await responder.handle(message, user_id=1)
    repo.log_message.assert_any_await("conn1", 100, "incoming", message.text)


async def test_replies_to_media_message(
    responder, repo, bot, active_connection, default_settings
):
    media = MagicMock()
    media.business_connection_id = "conn1"
    media.chat.id = 100
    media.text = None
    media.caption = None
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    await responder.handle(media, user_id=1)
    bot.send_message.assert_awaited_once()


def test_describe_prefers_text():
    assert describe_message(SimpleNamespace(text="hi there", caption=None)) == "hi there"


def test_describe_uses_caption_when_no_text():
    assert describe_message(SimpleNamespace(text=None, caption="nice pic")) == "nice pic"


def test_describe_labels_voice():
    msg = SimpleNamespace(text=None, caption=None, voice=SimpleNamespace())
    assert describe_message(msg) == "[voice message]"


def test_describe_empty_when_nothing():
    assert describe_message(SimpleNamespace(text=None, caption=None)) == ""


def _outgoing_at(when: datetime) -> MessageLog:
    m = MessageLog()
    m.created_at = when
    return m


async def test_no_reply_within_cooldown(
    bot, repo, ai, dnd, message, active_connection, default_settings
):
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    repo.get_last_outgoing = AsyncMock(return_value=_outgoing_at(datetime(2026, 1, 1, 12, 0)))
    r = Responder(bot, repo, ai, dnd, cooldown_min=5, now=lambda: datetime(2026, 1, 1, 12, 2))
    await r.handle(message, user_id=1)
    bot.send_message.assert_not_awaited()


async def test_reply_after_cooldown(
    bot, repo, ai, dnd, message, active_connection, default_settings
):
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    repo.get_last_outgoing = AsyncMock(return_value=_outgoing_at(datetime(2026, 1, 1, 12, 0)))
    r = Responder(bot, repo, ai, dnd, cooldown_min=5, now=lambda: datetime(2026, 1, 1, 12, 10))
    await r.handle(message, user_id=1)
    bot.send_message.assert_awaited_once()


async def test_reply_when_no_previous_outgoing(
    bot, repo, ai, dnd, message, active_connection, default_settings
):
    repo.get_connection.return_value = active_connection
    repo.get_settings.return_value = default_settings
    repo.get_last_outgoing = AsyncMock(return_value=None)
    r = Responder(bot, repo, ai, dnd, cooldown_min=5, now=lambda: datetime(2026, 1, 1, 12, 0))
    await r.handle(message, user_id=1)
    bot.send_message.assert_awaited_once()
