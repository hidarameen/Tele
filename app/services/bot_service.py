from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Bot, User
from app.utils.crypto import encrypt_text

async def create_bot(session: AsyncSession, owner: User, name: str, token: str, description: str | None = None) -> Bot:
	encrypted = encrypt_text(token)
	bot = Bot(owner_id=owner.id, name=name, token_encrypted=encrypted, description=description)
	session.add(bot)
	await session.flush()
	return bot

async def list_bots(session: AsyncSession, owner: User) -> list[Bot]:
	res = await session.execute(select(Bot).where(Bot.owner_id == owner.id).order_by(Bot.id.desc()))
	return list(res.scalars().all())

async def toggle_bot_active(session: AsyncSession, owner: User, bot_id: int, active: bool) -> Bot | None:
	res = await session.execute(select(Bot).where(Bot.id == bot_id, Bot.owner_id == owner.id))
	bot = res.scalar_one_or_none()
	if bot is None:
		return None
	bot.is_active = active
	await session.flush()
	return bot

async def delete_bot(session: AsyncSession, owner: User, bot_id: int) -> bool:
	res = await session.execute(select(Bot).where(Bot.id == bot_id, Bot.owner_id == owner.id))
	bot = res.scalar_one_or_none()
	if bot is None:
		return False
	await session.delete(bot)
	await session.flush()
	return True