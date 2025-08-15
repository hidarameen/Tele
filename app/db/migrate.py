import asyncio
from app.db.base import engine, Base
from app.db import models  # noqa: F401
from app.utils.logger import logger

async def run():
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
	logger.info("Database tables ensured (create_all). Consider using Alembic for production migrations.")

if __name__ == "__main__":
	asyncio.run(run())