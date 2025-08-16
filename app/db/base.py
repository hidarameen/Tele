from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine.url import make_url, URL
from app.config import settings
from app.utils.logger import logger
import os

class Base(DeclarativeBase):
	pass


def _build_url_from_params() -> str | None:
	# Pull from DB_* first, then fall back to common PG* env vars (useful on platforms like Neon/Render/Heroku)
	host = settings.db_host or os.getenv("PGHOST") or os.getenv("POSTGRES_HOST")
	name = settings.db_name or os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB")
	user = settings.db_user or os.getenv("PGUSER") or os.getenv("POSTGRES_USER")
	password = settings.db_password or os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD")
	port_env = settings.db_port or os.getenv("PGPORT") or os.getenv("POSTGRES_PORT")
	try:
		port = int(port_env) if port_env else 5432
	except Exception:
		port = 5432
	if not all([host, name, user, password]):
		return None
	return str(URL.create(
		drivername="postgresql+asyncpg",
		host=host,
		port=port,
		database=name,
		username=user,
		password=password,
	))


def _normalize_database_url_and_args(url_str: str | None) -> tuple[str, dict]:
	ssl_required = None
	if not url_str:
		built = _build_url_from_params()
		if not built:
			raise RuntimeError("DATABASE_URL or DB_*-params are required")
		url = make_url(built)
	else:
		url = make_url(url_str.strip())
	# Force asyncpg driver if a sync or bare driver is provided
	if url.drivername in ("postgresql", "postgres", "postgresql+psycopg2", "postgresql+pg8000"):
		url = url.set(drivername="postgresql+asyncpg")
	if url.drivername.startswith("postgresql"):
		query = dict(url.query)
		# SSL from DB_SSLMODE param if present
		if settings.db_sslmode:
			val = settings.db_sslmode.strip().lower()
			if val in ("require", "verify-ca", "verify-full"):
				ssl_required = True
			elif val == "disable":
				ssl_required = False
		# otherwise read sslmode from url
		if ssl_required is None:
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
		# fallback: pick from PGSSLMODE env if still None
		if ssl_required is None:
			pg_sslmode = os.getenv("PGSSLMODE") or os.getenv("POSTGRES_SSLMODE")
			if pg_sslmode:
				val = pg_sslmode.strip().lower()
				if val in ("require", "verify-ca", "verify-full"):
					ssl_required = True
				elif val == "disable":
					ssl_required = False
		# Drop all query params for asyncpg compatibility, but preserve 'options' (important for some managed PG providers like Neon)
		preserved = {}
		if 'options' in query:
			preserved['options'] = query['options']
		url = url.set(query=preserved)
	return str(url), ({"ssl": ssl_required} if ssl_required is not None else {})


def _mask_url_password(url: str) -> str:
	try:
		u = make_url(url)
		return str(u.set(password=("***" if u.password else None)))
	except Exception:
		return url

_normalized_url, _connect_args = _normalize_database_url_and_args(settings.database_url)

# Safe log (without password) of the final connection target for easier diagnostics
logger.info(f"DB connect URL: {_mask_url_password(_normalized_url)} | SSL={'on' if _connect_args.get('ssl') else 'off'}")

engine: AsyncEngine = create_async_engine(_normalized_url, pool_size=10, max_overflow=20, pool_pre_ping=True, connect_args=_connect_args)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_session() -> AsyncSession:
	async with AsyncSessionFactory() as session:
		yield session