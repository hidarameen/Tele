import asyncio
from telethon import TelegramClient, events
from sqlalchemy import select
from app.db.base import AsyncSessionFactory
from app.db.models import Task, TaskRoutingRule, UserSession
from app.utils.crypto import decrypt_text
from app.utils.logger import logger
from app.config import settings
from telethon.sessions import StringSession

class UserbotRunner:
	def __init__(self, user_session_id: int) -> None:
		self.user_session_id = user_session_id
		self.client: TelegramClient | None = None

	async def start(self) -> None:
		async with AsyncSessionFactory() as session:
			res = await session.execute(select(UserSession).where(UserSession.id == self.user_session_id))
			us = res.scalar_one()
		session_string = decrypt_text(us.session_encrypted)
		api_id = settings.telethon_api_id
		api_hash = settings.telethon_api_hash
		if not api_id or not api_hash:
			raise RuntimeError("TELETHON_API_ID/TELETHON_API_HASH are required")
		self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
		self.client.add_event_handler(self._on_message, events.NewMessage())
		logger.info(f"Starting userbot session {self.user_session_id}")
		await self.client.start()
		await self.client.run_until_disconnected()

	async def _on_message(self, event: events.NewMessage.Event):
		source_chat_id = event.chat_id
		async with AsyncSessionFactory() as session:
			res = await session.execute(select(Task).where(Task.user_session_id == self.user_session_id, Task.is_active == True))
			tasks = list(res.scalars().all())
			for task in tasks:
				res2 = await session.execute(select(TaskRoutingRule).where(TaskRoutingRule.task_id == task.id, TaskRoutingRule.source_chat_id == source_chat_id))
				for rule in res2.scalars().all():
					try:
						await self.client.forward_messages(rule.destination_chat_id, event.message)
					except Exception:
						logger.exception("userbot forward error")