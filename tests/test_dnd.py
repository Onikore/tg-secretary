from datetime import UTC, datetime
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


def _settings(dnd_enabled=True, start=None, end=None):
    s = Settings()
    s.dnd_enabled = dnd_enabled
    s.quiet_start_min = start
    s.quiet_end_min = end
    return s


def _at(hour, minute=0):
    return lambda: datetime(2026, 1, 1, hour, minute, tzinfo=UTC)


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


async def test_master_off_overrides_window(repo):
    repo.get_settings.return_value = _settings(dnd_enabled=False, start=540, end=1020)
    d = DNDService(repo, now=_at(12))
    assert await d.is_enabled(1) is False


async def test_no_window_means_always_on(repo):
    repo.get_settings.return_value = _settings()
    d = DNDService(repo, now=_at(3))
    assert await d.is_enabled(1) is True


async def test_inside_daytime_window(repo):
    repo.get_settings.return_value = _settings(start=540, end=1020)  # 09:00-17:00
    d = DNDService(repo, now=_at(12))
    assert await d.is_enabled(1) is True


async def test_outside_daytime_window(repo):
    repo.get_settings.return_value = _settings(start=540, end=1020)
    d = DNDService(repo, now=_at(18))
    assert await d.is_enabled(1) is False


async def test_overnight_window_wraps_midnight(repo):
    repo.get_settings.return_value = _settings(start=1320, end=480)  # 22:00-08:00
    assert await DNDService(repo, now=_at(23)).is_enabled(1) is True
    assert await DNDService(repo, now=_at(7)).is_enabled(1) is True
    assert await DNDService(repo, now=_at(12)).is_enabled(1) is False


async def test_tz_offset_shifts_window(repo):
    repo.get_settings.return_value = _settings(start=540, end=1020)  # 09:00-17:00 local
    # 07:00 UTC + 180min = 10:00 local -> inside
    d = DNDService(repo, tz_offset_min=180, now=_at(7))
    assert await d.is_enabled(1) is True
