from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine.url import make_url
from app.config import settings

class Base(DeclarativeBase):
	pass


def _normalize_database_url_and_args(url_str: str) -> tuple[str, dict]:
	ssl_required = None
	url = make_url(url_str)
	# Force asyncpg driver if a sync or bare driver is provided
	if url.drivername in ("postgresql", "postgres", "postgresql+psycopg2", "postgresql+pg8000"):
		url = url.set(drivername="postgresql+asyncpg")
	if url.drivername.startswith("postgresql"):
		query = dict(url.query)
		# Remove libpq-only params that asyncpg doesn't accept
		query.pop("channel_binding", None)
		sslmode_raw = query.get("sslmode")
		if sslmode_raw is not None:
			value = str(sslmode_raw).strip().lower()
			synonyms = {
				"enabled": "require", "enable": "require", "on": "require", "true": "require", "1": "require",
				"disabled": "disable", "off": "disable", "false": "disable", "0": "disable",
				"verifyfull": "verify-full", "verify_full": "verify-full",
				"verifyca": "verify-ca", "verify_ca": "verify-ca",
			}
			value_norm = synonyms.get(value, value)
			if value_norm in ("require", "verify-ca", "verify-full"):
				ssl_required = True
			elif value_norm == "disable":
				ssl_required = False
			# Always drop sslmode so it won't be passed to asyncpg
			query.pop("sslmode", None)
		url = url.set(query=query)
	return str(url), ({"ssl": ssl_required} if ssl_required is not None else {})

_normalized_url, _connect_args = _normalize_database_url_and_args(settings.database_url)

engine: AsyncEngine = create_async_engine(_normalized_url, pool_size=10, max_overflow=20, pool_pre_ping=True, connect_args=_connect_args)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_session() -> AsyncSession:
	async with AsyncSessionFactory() as session:
		yield session