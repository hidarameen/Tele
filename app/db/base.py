from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine.url import make_url
from app.config import settings

class Base(DeclarativeBase):
	pass

def _normalize_database_url(url_str: str) -> str:
	url = make_url(url_str)
	if url.drivername.startswith("postgresql"):
		query = dict(url.query)
		if "sslmode" in query:
			value = str(query.get("sslmode", "")).strip().lower()
			# map common synonyms
			synonyms = {
				"enabled": "require", "enable": "require", "on": "require", "true": "require", "1": "require",
				"disabled": "disable", "disable": "disable", "off": "disable", "false": "disable", "0": "disable",
				"verifyfull": "verify-full", "verify_full": "verify-full",
				"verifyca": "verify-ca", "verify_ca": "verify-ca",
				"prefer_ssl": "prefer", "allow_ssl": "allow", "require_ssl": "require",
				"noverify": "require", "no-verify": "require",
			}
			value_norm = synonyms.get(value, value)
			recognized = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
			if value_norm in recognized:
				query["sslmode"] = value_norm
			else:
				# drop unknown/empty sslmode
				query.pop("sslmode", None)
			url = url.set(query=query)
		return str(url)
	return str(url)

engine: AsyncEngine = create_async_engine(_normalize_database_url(settings.database_url), pool_size=10, max_overflow=20, pool_pre_ping=True)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_session() -> AsyncSession:
	async with AsyncSessionFactory() as session:
		yield session