from unittest.mock import AsyncMock, MagicMock

import pytest

from src.db.models import Settings
from src.services.dnd import DNDService


@pytest.fixture
def repo():
    r = MagicMock()
    r.get_settings = AsyncMock()
    r.update_dnd = AsyncMock()
    return r


@pytest.fixture
def dnd(repo):
    return DNDService(repo)


async def test_is_enabled_returns_true_when_set(dnd, repo):
    s = Settings()
    s.dnd_enabled = True
    repo.get_settings.return_value = s
    assert await dnd.is_enabled(1) is True


async def test_is_enabled_returns_false_by_default(dnd, repo):
    s = Settings()
    s.dnd_enabled = False
    repo.get_settings.return_value = s
    assert await dnd.is_enabled(1) is False


async def test_enable_calls_repo(dnd, repo):
    await dnd.enable(1)
    repo.update_dnd.assert_awaited_once_with(1, True)


async def test_disable_calls_repo(dnd, repo):
    await dnd.disable(1)
    repo.update_dnd.assert_awaited_once_with(1, False)
