from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User

async def get_or_create_user(session: AsyncSession, telegram_user_id: int, language_code: str | None = None, timezone: str | None = None) -> User:
	result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
	user = result.scalar_one_or_none()
	if user is None:
		user = User(telegram_user_id=telegram_user_id, language_code=language_code, timezone=timezone)
		session.add(user)
		await session.flush()
	return user

async def update_user_prefs(session: AsyncSession, user: User, language_code: str | None = None, timezone: str | None = None) -> User:
	if language_code is not None:
		user.language_code = language_code
	if timezone is not None:
		user.timezone = timezone
	await session.flush()
	return user