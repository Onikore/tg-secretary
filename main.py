import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from src.config import config
from src.db.repository import Repository
from src.handlers import business, commands, connection
from src.services.ai import AIService
from src.services.dnd import DNDService
from src.services.responder import Responder

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    repo = Repository(config.db_path)
    await repo.init_db()

    session = AiohttpSession(proxy=config.proxy_url) if config.proxy_url else None
    bot = Bot(config.bot_token, session=session)
    ai = AIService(config.gemini_api_key, proxy=config.proxy_url or None)
    dnd = DNDService(repo, tz_offset_min=config.tz_offset_min)
    responder = Responder(bot, repo, ai, dnd, cooldown_min=config.reply_cooldown_min)

    dp = Dispatcher()
    dp.include_router(commands.setup(dnd, repo, config.owner_user_id))
    dp.include_router(connection.setup(repo))
    dp.include_router(business.setup(responder, config.owner_user_id))

    logger.info("Secretary bot starting (owner=%s)", config.owner_user_id)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
