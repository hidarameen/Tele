from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import AsyncSessionFactory
from app.services.user_service import get_or_create_user
from app.services.bot_service import create_bot, list_bots, delete_bot, toggle_bot_active
from app.utils.logger import logger
from .tasks_handlers import router as tasks_router
from .handlers_settings import router as settings_router

router = Router()
router.include_router(tasks_router)
router.include_router(settings_router)

MAIN_MENU = "main_menu"

@router.message(CommandStart())
async def on_start(message: Message):
	async with AsyncSessionFactory() as session:
		user = await get_or_create_user(session, message.from_user.id, language_code=message.from_user.language_code)
		await session.commit()
	builder = InlineKeyboardBuilder()
	builder.button(text="➕ إضافة بوت جديد", callback_data="add_bot")
	builder.button(text="🤖 قائمة البوتات", callback_data="list_bots")
	builder.button(text="⚙️ الإعدادات", callback_data="settings")
	builder.adjust(1)
	await message.answer("مرحباً بك في صانع البوتات", reply_markup=builder.as_markup())

@router.callback_query(F.data == "add_bot")
async def on_add_bot(call: CallbackQuery):
	await call.message.answer("أرسل اسم البوت ثم فاصلة ثم التوكن\nمثال:\nMyForwarderBot, 123456:ABC-XYZ")
	await call.answer()

@router.message(F.text.contains(","))
async def on_receive_token(message: Message):
	try:
		name, token = [x.strip() for x in message.text.split(",", 1)]
		async with AsyncSessionFactory() as session:
			user = await get_or_create_user(session, message.from_user.id, language_code=message.from_user.language_code)
			bot = await create_bot(session, user, name=name, token=token)
			await session.commit()
		await message.answer(f"تم إضافة البوت: {name}\nالرجاء إضافتي كمطور في بوتك المصنوع وابدأ من خلال محادثته الخاصة.")
	except Exception as e:
		logger.exception("add bot error")
		await message.answer("تعذر إضافة البوت. تأكد من الصيغة والصلاحيات.")

@router.callback_query(F.data == "list_bots")
async def on_list_bots(call: CallbackQuery):
	async with AsyncSessionFactory() as session:
		user = await get_or_create_user(session, call.from_user.id, language_code=call.from_user.language_code)
		bots = await list_bots(session, user)
		await session.commit()
	builder = InlineKeyboardBuilder()
	for b in bots:
		status = "🟢" if b.is_active else "⚪"
		builder.button(text=f"{status} {b.name}", callback_data=f"bot:{b.id}")
	builder.adjust(1)
	await call.message.answer("بوتاتك:", reply_markup=builder.as_markup())
	await call.answer()

@router.callback_query(F.data.startswith("bot:"))
async def on_bot_item(call: CallbackQuery):
	bot_id = int(call.data.split(":", 1)[1])
	builder = InlineKeyboardBuilder()
	builder.button(text="تعطيل/تنشيط", callback_data=f"toggle_bot:{bot_id}")
	builder.button(text="حذف", callback_data=f"delete_bot:{bot_id}")
	builder.button(text="المهام", callback_data=f"tasks:{bot_id}")
	builder.adjust(2, 1)
	await call.message.answer("إدارة البوت:", reply_markup=builder.as_markup())
	await call.answer()

@router.callback_query(F.data.startswith("toggle_bot:"))
async def on_toggle_bot(call: CallbackQuery):
	bot_id = int(call.data.split(":", 1)[1])
	async with AsyncSessionFactory() as session:
		user = await get_or_create_user(session, call.from_user.id, language_code=call.from_user.language_code)
		from sqlalchemy import select
		from app.db.models import Bot
		res = await session.execute(select(Bot).where(Bot.id == bot_id, Bot.owner_id == user.id))
		b = res.scalar_one_or_none()
		if b is None:
			await call.answer("غير موجود", show_alert=True)
			return
		b.is_active = not b.is_active
		await session.commit()
	await call.answer("تم")

@router.callback_query(F.data.startswith("delete_bot:"))
async def on_delete_bot(call: CallbackQuery):
	bot_id = int(call.data.split(":", 1)[1])
	async with AsyncSessionFactory() as session:
		user = await get_or_create_user(session, call.from_user.id, language_code=call.from_user.language_code)
		ok = await delete_bot(session, user, bot_id)
		await session.commit()
	if ok:
		await call.answer("تم الحذف")
	else:
		await call.answer("غير موجود", show_alert=True)