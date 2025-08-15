from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from app.db.base import AsyncSessionFactory
from app.services.user_service import get_or_create_user, update_user_prefs
from app.services.user_session_service import list_user_sessions, create_user_session_from_string, delete_user_session
from .userbot_login import router as userbot_login_router

router = Router()
router.include_router(userbot_login_router)

@router.callback_query(F.data == "settings")
async def on_settings(call: CallbackQuery):
	builder = InlineKeyboardBuilder()
	builder.button(text="🌐 تغيير اللغة", callback_data="lang")
	builder.button(text="🕒 تغيير المنطقة الزمنية", callback_data="tz")
	builder.button(text="👤 إعدادات اليوزربوت", callback_data="userbot_settings")
	builder.adjust(1)
	await call.message.answer("الإعدادات:", reply_markup=builder.as_markup())
	await call.answer()

@router.callback_query(F.data == "userbot_settings")
async def on_userbot_settings(call: CallbackQuery):
	async with AsyncSessionFactory() as session:
		user = await get_or_create_user(session, call.from_user.id)
		sessions = await list_user_sessions(session, user)
	builder = InlineKeyboardBuilder()
	builder.button(text="➕ إضافة جلسة", callback_data="userbot_add")
	builder.button(text="📱 تسجيل عبر رقم الهاتف", callback_data="userbot_add_phone")
	for s in sessions:
		label = s.label or f"جلسة #{s.id}"
		builder.button(text=label, callback_data=f"userbot_s:{s.id}")
	builder.adjust(1)
	await call.message.answer("جلسات اليوزربوت:", reply_markup=builder.as_markup())
	await call.answer()

@router.callback_query(F.data.startswith("userbot_s:"))
async def on_userbot_item(call: CallbackQuery):
	session_id = int(call.data.split(":",1)[1])
	builder = InlineKeyboardBuilder()
	builder.button(text="🗑 حذف الجلسة", callback_data=f"userbot_del:{session_id}")
	builder.adjust(1)
	await call.message.answer("إدارة الجلسة:", reply_markup=builder.as_markup())
	await call.answer()

@router.callback_query(F.data.startswith("userbot_del:"))
async def on_userbot_delete(call: CallbackQuery):
	session_id = int(call.data.split(":",1)[1])
	async with AsyncSessionFactory() as session:
		user = await get_or_create_user(session, call.from_user.id)
		ok = await delete_user_session(session, user, session_id)
		await session.commit()
	if ok:
		await call.answer("تم الحذف")
	else:
		await call.answer("غير موجود", show_alert=True)

@router.callback_query(F.data == "userbot_add")
async def on_userbot_add(call: CallbackQuery):
	await call.message.answer("أرسل session string الخاصة ب Telethon")
	await call.answer()

@router.message(F.text.regexp(r"^1[A-Za-z0-9_-]{85,}"))
async def on_receive_session_string(message: Message):
	async with AsyncSessionFactory() as session:
		user = await get_or_create_user(session, message.from_user.id)
		await create_user_session_from_string(session, user, session_string=message.text.strip())
		await session.commit()
	await message.answer("تم حفظ الجلسة")