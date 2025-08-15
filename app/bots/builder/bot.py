import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
import redis.asyncio as redis
from app.config import settings
from app.bots.builder.handlers import router as builder_router
from app.utils.logger import logger

async def run_builder_bot():
	if not settings.builder_bot_token:
		raise RuntimeError("BUILDER_BOT_TOKEN is not configured")
	bot = Bot(token=settings.builder_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
	redis_client = redis.from_url(settings.redis_url, decode_responses=True)
	storage = RedisStorage(redis=redis_client)
	dp = Dispatcher(storage=storage)
	dp.include_router(builder_router)
	logger.info("Starting builder bot polling...")
	await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
	asyncio.run(run_builder_bot())