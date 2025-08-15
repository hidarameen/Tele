from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from app.config import settings
from app.services.user_service import get_or_create_user
from app.services.user_session_service import create_user_session_from_string
from app.db.base import AsyncSessionFactory
from app.utils.logger import logger
from app.bots.builder.states import UserbotState

router = Router()

@router.callback_query(F.data == "userbot_add_phone")
async def add_phone_start(call: CallbackQuery, state: FSMContext):
	await state.set_state(UserbotState.waiting_phone)
	await call.message.answer("أرسل رقم الهاتف مع رمز الدولة (مثال: +9665xxxxxxxx)")
	await call.answer()

@router.message(UserbotState.waiting_phone)
async def receive_phone(message: Message, state: FSMContext):
	phone = message.text.strip()
	api_id = settings.telethon_api_id
	api_hash = settings.telethon_api_hash
	if not api_id or not api_hash:
		await message.answer("إعدادات Telethon غير مكتملة")
		await state.clear()
		return
	client = TelegramClient(StringSession(), api_id, api_hash)
	await client.connect()
	sent = await client.send_code_request(phone)
	session_str = client.session.save()
	await client.disconnect()
	await state.update_data(phone=phone, phone_code_hash=sent.phone_code_hash, session=session_str)
	await state.set_state(UserbotState.waiting_code)
	await message.answer("أدخل كود التحقق المرسل")

@router.message(UserbotState.waiting_code)
async def receive_code(message: Message, state: FSMContext):
	data = await state.get_data()
	phone = data.get("phone")
	phone_code_hash = data.get("phone_code_hash")
	session_str = data.get("session")
	api_id = settings.telethon_api_id
	api_hash = settings.telethon_api_hash
	client = TelegramClient(StringSession(session_str), api_id, api_hash)
	await client.connect()
	try:
		await client.sign_in(phone=phone, code=message.text.strip(), phone_code_hash=phone_code_hash)
		new_session = client.session.save()
		async with AsyncSessionFactory() as session:
			user = await get_or_create_user(session, message.from_user.id)
			await create_user_session_from_string(session, user, new_session)
			await session.commit()
		await message.answer("تم تسجيل الدخول وحفظ الجلسة")
		await state.clear()
	finally:
		await client.disconnect()
	return

@router.message(UserbotState.waiting_code)
async def receive_code_with_2fa(message: Message, state: FSMContext):
	# fallback in case 2FA is needed; Telethon raises SessionPasswordNeededError
	data = await state.get_data()
	phone = data.get("phone")
	phone_code_hash = data.get("phone_code_hash")
	session_str = data.get("session")
	api_id = settings.telethon_api_id
	api_hash = settings.telethon_api_hash
	client = TelegramClient(StringSession(session_str), api_id, api_hash)
	await client.connect()
	try:
		try:
			await client.sign_in(phone=phone, code=message.text.strip(), phone_code_hash=phone_code_hash)
			new_session = client.session.save()
			async with AsyncSessionFactory() as session:
				user = await get_or_create_user(session, message.from_user.id)
				await create_user_session_from_string(session, user, new_session)
				await session.commit()
			await message.answer("تم تسجيل الدخول وحفظ الجلسة")
			await state.clear()
			return
		except SessionPasswordNeededError:
			await state.set_state(UserbotState.waiting_2fa)
			await state.update_data(session=session_str, phone=phone)
			await message.answer("الحساب محمي بكلمة مرور. أرسل كلمة المرور الآن")
			return
	finally:
		await client.disconnect()

@router.message(UserbotState.waiting_2fa)
async def receive_2fa(message: Message, state: FSMContext):
	data = await state.get_data()
	session_str = data.get("session")
	phone = data.get("phone")
	api_id = settings.telethon_api_id
	api_hash = settings.telethon_api_hash
	client = TelegramClient(StringSession(session_str), api_id, api_hash)
	await client.connect()
	try:
		await client.sign_in(password=message.text.strip())
		new_session = client.session.save()
		async with AsyncSessionFactory() as session:
			user = await get_or_create_user(session, message.from_user.id)
			await create_user_session_from_string(session, user, new_session)
			await session.commit()
		await message.answer("تم تسجيل الدخول وحفظ الجلسة")
		await state.clear()
	finally:
		await client.disconnect()