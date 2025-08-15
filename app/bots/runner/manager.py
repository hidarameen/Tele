import asyncio
from app.utils.logger import logger
from app.bots.made_bot.bot_runner import MadeBotRunner
from app.bots.userbot.userbot_runner import UserbotRunner

class RunnerManager:
	def __init__(self) -> None:
		self.bot_runners: dict[int, asyncio.Task] = {}
		self.userbot_runners: dict[int, asyncio.Task] = {}

	async def ensure_bot_running(self, bot_id: int) -> None:
		if bot_id in self.bot_runners and not self.bot_runners[bot_id].done():
			return
		async def _run():
			runner = MadeBotRunner(bot_id)
			await runner.start()
		self.bot_runners[bot_id] = asyncio.create_task(_run(), name=f"madebot:{bot_id}")
		logger.info(f"Spawned made bot runner bot_id={bot_id}")

	async def stop_bot(self, bot_id: int) -> None:
		task = self.bot_runners.get(bot_id)
		if task:
			task.cancel()
			self.bot_runners.pop(bot_id, None)

	async def ensure_userbot_running(self, user_session_id: int) -> None:
		if user_session_id in self.userbot_runners and not self.userbot_runners[user_session_id].done():
			return
		async def _run():
			runner = UserbotRunner(user_session_id)
			await runner.start()
		self.userbot_runners[user_session_id] = asyncio.create_task(_run(), name=f"userbot:{user_session_id}")
		logger.info(f"Spawned userbot runner session_id={user_session_id}")

	async def stop_userbot(self, user_session_id: int) -> None:
		task = self.userbot_runners.get(user_session_id)
		if task:
			task.cancel()
			self.userbot_runners.pop(user_session_id, None)

runner_manager = RunnerManager()