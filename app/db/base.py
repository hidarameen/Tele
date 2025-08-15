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
		# read sslmode
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
		# honor explicit ssl=true/false if present
		if "ssl" in query and ssl_required is None:
			ssl_val = str(query.get("ssl")).strip().lower()
			if ssl_val in ("1", "true", "on", "yes"):
				ssl_required = True
			elif ssl_val in ("0", "false", "off", "no"):
				ssl_required = False
		# drop all query params (asyncpg doesn't accept arbitrary URL params)
		url = url.set(query={})
	return str(url), ({"ssl": ssl_required} if ssl_required is not None else {})

_normalized_url, _connect_args = _normalize_database_url_and_args(settings.database_url)

engine: AsyncEngine = create_async_engine(_normalized_url, pool_size=10, max_overflow=20, pool_pre_ping=True, connect_args=_connect_args)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_session() -> AsyncSession:
	async with AsyncSessionFactory() as session:
		yield session