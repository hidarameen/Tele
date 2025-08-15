from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine.url import make_url
from app.config import settings

class Base(DeclarativeBase):
	pass

def _normalize_database_url(url_str: str) -> str:
	url = make_url(url_str)
	if url.drivername.startswith("postgresql+asyncpg"):
		query = dict(url.query)
		if "sslmode" in query:
			value = str(query.get("sslmode", "")).lower()
			query.pop("sslmode", None)
			if value in ("require", "verify-full", "verify-ca"):
				query["ssl"] = "true"
			elif value in ("disable", "allow", "prefer"):
				query.setdefault("ssl", "false")
			url = url.set(query=query)
	return str(url)

engine: AsyncEngine = create_async_engine(_normalize_database_url(settings.database_url), pool_size=10, max_overflow=20, pool_pre_ping=True)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_session() -> AsyncSession:
	async with AsyncSessionFactory() as session:
		yield session