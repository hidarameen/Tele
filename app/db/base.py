from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

class Base(DeclarativeBase):
	pass

engine: AsyncEngine = create_async_engine(settings.database_url, pool_size=10, max_overflow=20, pool_pre_ping=True)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_session() -> AsyncSession:
	async with AsyncSessionFactory() as session:
		yield session