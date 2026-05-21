from ..db.repository import Repository


class DNDService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    async def is_enabled(self, user_id: int) -> bool:
        settings = await self._repo.get_settings(user_id)
        return settings.dnd_enabled

    async def enable(self, user_id: int) -> None:
        await self._repo.update_dnd(user_id, True)

    async def disable(self, user_id: int) -> None:
        await self._repo.update_dnd(user_id, False)
