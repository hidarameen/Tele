import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from sqlalchemy import select
from app.db.base import AsyncSessionFactory
from app.db.models import Bot as BotModel, Task, TaskRoutingRule
from app.utils.crypto import decrypt_text
from app.utils.logger import logger
from .panel import build_router

class MadeBotRunner:
	def __init__(self, bot_id: int) -> None:
		self.bot_id = bot_id
		self.dp: Dispatcher | None = None
		self.bot: Bot | None = None

	async def start(self) -> None:
		async with AsyncSessionFactory() as session:
			res = await session.execute(select(BotModel).where(BotModel.id == self.bot_id))
			bm = res.scalar_one()
			token = decrypt_text(bm.token_encrypted) if bm.token_encrypted else None
		if not token:
			raise RuntimeError("Token not configured for made bot")
		self.bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
		self.dp = Dispatcher()
		self.dp.include_router(build_router(self.bot_id))
		self.dp.message.register(self._on_message)
		logger.info(f"Starting made bot {bm.name} ({self.bot_id})")
		await self.dp.start_polling(self.bot, allowed_updates=self.dp.resolve_used_update_types())

	async def _on_message(self, message: Message):
		if message.chat.type == "private":
			return
		source_chat_id = message.chat.id
		async with AsyncSessionFactory() as session:
			res = await session.execute(select(Task).where(Task.bot_id == self.bot_id, Task.is_active == True))
			tasks = list(res.scalars().all())
			for task in tasks:
				res2 = await session.execute(select(TaskRoutingRule).where(TaskRoutingRule.task_id == task.id, TaskRoutingRule.source_chat_id == source_chat_id))
				for rule in res2.scalars().all():
					try:
						if rule.forward_mode == "copy":
							await message.copy_to(chat_id=rule.destination_chat_id)
						else:
							await message.forward(chat_id=rule.destination_chat_id)
					except Exception:
						logger.exception("forward error")