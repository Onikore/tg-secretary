from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Dispatcher

from src.db.repository import Repository
from src.handlers import business, commands, connection
from src.services.dnd import DNDService
from src.services.responder import Responder


@pytest.fixture
async def repo(tmp_path):
    r = Repository(str(tmp_path / "wiring.db"))
    await r.init_db()
    return r


async def test_dispatcher_resolves_business_update_types(repo):
    bot = MagicMock()
    bot.send_message = AsyncMock()
    ai = MagicMock()
    dnd = DNDService(repo)
    responder = Responder(bot, repo, ai, dnd)

    dp = Dispatcher()
    dp.include_router(commands.setup(dnd, repo, 1))
    dp.include_router(connection.setup(repo))
    dp.include_router(business.setup(responder, 1))

    used = dp.resolve_used_update_types()

    # Without these, Telegram never delivers business updates and the bot is silent.
    assert "business_message" in used
    assert "business_connection" in used
    assert "edited_business_message" in used
    assert "message" in used
