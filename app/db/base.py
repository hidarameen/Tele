from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine.url import make_url, URL
from app.config import settings

class Base(DeclarativeBase):
	pass


def _clean(val):
	if val is None:
		return None
	s = str(val).strip()
	if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
		s = s[1:-1]
	return s


def _build_url_from_params() -> str | None:
	host = _clean(settings.db_host)
	name = _clean(settings.db_name)
	user = _clean(settings.db_user)
	password = _clean(settings.db_password)
	if not all([host, name, user, password]):
		return None
	port_raw = settings.db_port if settings.db_port is not None else 5432
	try:
		port = int(str(port_raw).strip())
	except Exception:
		port = 5432
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
		raw = _clean(url_str)
		url = make_url(raw)
	# Force asyncpg driver if a sync or bare driver is provided
	if url.drivername in ("postgresql", "postgres", "postgresql+psycopg2", "postgresql+pg8000"):
		url = url.set(drivername="postgresql+asyncpg")
	if url.drivername.startswith("postgresql"):
		query = dict(url.query)
		# SSL from DB_SSLMODE param if present
		sslmode_env = _clean(settings.db_sslmode)
		if sslmode_env:
			val = sslmode_env.lower()
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
		# Drop all query params for asyncpg compatibility
		url = url.set(query={})
	return str(url), ({"ssl": ssl_required} if ssl_required is not None else {})

_normalized_url, _connect_args = _normalize_database_url_and_args(settings.database_url)

engine: AsyncEngine = create_async_engine(_normalized_url, pool_size=10, max_overflow=20, pool_pre_ping=True, connect_args=_connect_args)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_session() -> AsyncSession:
	async with AsyncSessionFactory() as session:
		yield session