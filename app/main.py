import asyncio
from app.db.migrate import run as migrate_run
from app.bots.builder.bot import run_builder_bot
from app.utils.logger import logger

async def main():
	await migrate_run()
	await run_builder_bot()

if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		logger.info("Shutting down...")