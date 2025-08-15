from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import UserSession, User
from app.utils.crypto import encrypt_text, decrypt_text

async def create_user_session_from_string(session: AsyncSession, owner: User, session_string: str, label: str | None = None) -> UserSession:
	encrypted = encrypt_text(session_string)
	us = UserSession(owner_id=owner.id, session_type="telethon", session_encrypted=encrypted, label=label)
	session.add(us)
	await session.flush()
	return us

async def list_user_sessions(session: AsyncSession, owner: User) -> list[UserSession]:
	res = await session.execute(select(UserSession).where(UserSession.owner_id == owner.id).order_by(UserSession.id.desc()))
	return list(res.scalars().all())

async def delete_user_session(session: AsyncSession, owner: User, session_id: int) -> bool:
	res = await session.execute(select(UserSession).where(UserSession.id == session_id, UserSession.owner_id == owner.id))
	us = res.scalar_one_or_none()
	if us is None:
		return False
	await session.delete(us)
	await session.flush()
	return True

async def get_user_session(session: AsyncSession, owner: User, session_id: int) -> UserSession | None:
	res = await session.execute(select(UserSession).where(UserSession.id == session_id, UserSession.owner_id == owner.id))
	return res.scalar_one_or_none()