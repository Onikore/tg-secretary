from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from ..db.repository import Repository


class DNDService:
    def __init__(
        self,
        repo: Repository,
        tz_offset_min: int = 0,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._repo = repo
        self._tz_offset_min = tz_offset_min
        self._now = now or (lambda: datetime.now(UTC))

    async def is_enabled(self, user_id: int) -> bool:
        settings = await self._repo.get_settings(user_id)
        if not settings.dnd_enabled:
            return False
        start = settings.quiet_start_min
        end = settings.quiet_end_min
        if start is None or end is None:
            return True
        local = self._now() + timedelta(minutes=self._tz_offset_min)
        cur = local.hour * 60 + local.minute
        if start <= end:
            return start <= cur < end
        return cur >= start or cur < end

    async def enable(self, user_id: int) -> None:
        await self._repo.update_dnd(user_id, True)

    async def disable(self, user_id: int) -> None:
        await self._repo.update_dnd(user_id, False)
