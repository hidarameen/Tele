from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from app.db.base import AsyncSessionFactory
from app.db.models import Bot as BotModel, Task, User, UserSession
from app.services.task_service import create_task, list_tasks, update_task, delete_task, toggle_task
from app.services.user_service import get_or_create_user, update_user_prefs
from app.services.user_session_service import list_user_sessions, create_user_session_from_string, delete_user_session
from zoneinfo import ZoneInfo

from aiogram.fsm.context import FSMContext
from app.bots.builder.states import TaskState, SettingsState, UserbotState


def build_router(bot_id: int) -> Router:
	router = Router()

	async def _ensure_owner(message: Message | CallbackQuery) -> User | None:
		telegram_id = message.from_user.id if isinstance(message, Message) else message.from_user.id
		async with AsyncSessionFactory() as session:
			res = await session.execute(select(BotModel).where(BotModel.id == bot_id))
			bm = res.scalar_one_or_none()
			if not bm:
				return None
			res2 = await session.execute(select(User).where(User.id == bm.owner_id))
			owner = res2.scalar_one()
			if owner.telegram_user_id != telegram_id:
				return None
			return owner

	@router.message(CommandStart())
	async def start(message: Message):
		owner = await _ensure_owner(message)
		if not owner:
			return
		kb = InlineKeyboardBuilder()
		kb.button(text="➕ إضافة مهمة", callback_data="mb:add_task")
		kb.button(text="📋 قائمة المهام", callback_data="mb:list_tasks")
		kb.button(text="⚙️ الإعدادات", callback_data="mb:settings")
		kb.adjust(1)
		await message.answer("مرحباً بك في لوحة تحكم البوت المصنوع", reply_markup=kb.as_markup())

	@router.callback_query(F.data == "mb:list_tasks")
	async def list_tasks_cb(call: CallbackQuery):
		owner = await _ensure_owner(call)
		if not owner:
			await call.answer("غير مصرح", show_alert=True)
			return
		async with AsyncSessionFactory() as session:
			res = await session.execute(select(Task).where(Task.bot_id == bot_id).order_by(Task.id.desc()))
			tasks = list(res.scalars().all())
		kb = InlineKeyboardBuilder()
		for t in tasks:
			status = "🟢" if t.is_active else "⚪"
			kb.button(text=f"{status} {t.name}", callback_data=f"mb:task:{t.id}")
		kb.button(text="➕ إضافة مهمة", callback_data="mb:add_task")
		kb.adjust(1)
		await call.message.answer("مهامك:", reply_markup=kb.as_markup())
		await call.answer()

	@router.callback_query(F.data == "mb:add_task")
	async def add_task_start(call: CallbackQuery, state: FSMContext):
		owner = await _ensure_owner(call)
		if not owner:
			await call.answer("غير مصرح", show_alert=True)
			return
		await state.set_state(TaskState.waiting_new_task_name)
		await call.message.answer("أرسل اسم المهمة الجديدة")
		await call.answer()

	@router.message(TaskState.waiting_new_task_name)
	async def add_task_finish(message: Message, state: FSMContext):
		owner = await _ensure_owner(message)
		if not owner:
			return
		name = message.text.strip()
		async with AsyncSessionFactory() as session:
			# افتراضي: نوع bot
			res = await session.execute(select(BotModel).where(BotModel.id == bot_id))
			bm = res.scalar_one()
			await create_task(session, bm, name=name, task_type="bot")
			await session.commit()
		await state.clear()
		await message.answer("تم إنشاء المهمة")

	@router.callback_query(F.data.startswith("mb:task:"))
	async def task_item(call: CallbackQuery, state: FSMContext):
		owner = await _ensure_owner(call)
		if not owner:
			await call.answer("غير مصرح", show_alert=True)
			return
		task_id = int(call.data.split(":", 2)[2])
		kb = InlineKeyboardBuilder()
		kb.button(text="تفعيل/تعطيل", callback_data=f"mb:task_toggle:{task_id}")
		kb.button(text="✏️ تعديل الاسم", callback_data=f"mb:task_rename:{task_id}")
		kb.button(text="🔁 تبديل النوع", callback_data=f"mb:task_switch:{task_id}")
		kb.button(text="ℹ️ معلومات", callback_data=f"mb:task_info:{task_id}")
		kb.button(text="⚙️ إعدادات", callback_data=f"mb:task_settings:{task_id}")
		kb.button(text="🗑 حذف", callback_data=f"mb:task_delete:{task_id}")
		kb.adjust(2,2,2)
		await call.message.answer("إدارة المهمة:", reply_markup=kb.as_markup())
		await call.answer()

	@router.callback_query(F.data.startswith("mb:task_toggle:"))
	async def task_toggle(call: CallbackQuery):
		task_id = int(call.data.split(":", 2)[2])
		async with AsyncSessionFactory() as session:
			res = await session.execute(select(Task).where(Task.id == task_id, Task.bot_id == bot_id))
			t = res.scalar_one_or_none()
			if not t:
				await call.answer("غير موجود", show_alert=True)
				return
			await toggle_task(session, task_id, not t.is_active)
			await session.commit()
		await call.answer("تم")

	@router.callback_query(F.data.startswith("mb:task_delete:"))
	async def task_delete(call: CallbackQuery):
		task_id = int(call.data.split(":", 2)[2])
		async with AsyncSessionFactory() as session:
			res = await session.execute(select(Task).where(Task.id == task_id, Task.bot_id == bot_id))
			t = res.scalar_one_or_none()
			if not t:
				await call.answer("غير موجود", show_alert=True)
				return
			await delete_task(session, task_id)
			await session.commit()
		await call.answer("تم الحذف")

	@router.callback_query(F.data.startswith("mb:task_rename:"))
	async def task_rename_start(call: CallbackQuery, state: FSMContext):
		task_id = int(call.data.split(":", 2)[2])
		await state.set_state(TaskState.waiting_rename)
		await state.update_data(task_id=task_id)
		await call.message.answer("أرسل الاسم الجديد")
		await call.answer()

	@router.message(TaskState.waiting_rename)
	async def task_rename_finish(message: Message, state: FSMContext):
		data = await state.get_data()
		task_id = int(data["task_id"]) if "task_id" in data else None
		if not task_id:
			await state.clear()
			return
		new_name = message.text.strip()
		async with AsyncSessionFactory() as session:
			await update_task(session, task_id=task_id, name=new_name)
			await session.commit()
		await state.clear()
		await message.answer("تم التعديل")

	@router.callback_query(F.data.startswith("mb:task_switch:"))
	async def task_switch_type(call: CallbackQuery, state: FSMContext):
		task_id = int(call.data.split(":", 2)[2])
		async with AsyncSessionFactory() as session:
			res = await session.execute(select(Task).where(Task.id == task_id, Task.bot_id == bot_id))
			t = res.scalar_one_or_none()
			if not t:
				await call.answer("غير موجود", show_alert=True)
				return
			new_type = "userbot" if t.task_type == "bot" else "bot"
			if new_type == "userbot":
				# اختيار جلسة
				resb = await session.execute(select(BotModel).where(BotModel.id == bot_id))
				bm = resb.scalar_one()
				res_owner = await session.execute(select(User).where(User.id == bm.owner_id))
				owner = res_owner.scalar_one()
				sessions = await list_user_sessions(session, owner)
				if not sessions:
					await call.answer("لا توجد جلسات يوزربوت. أضف جلسة أولاً", show_alert=True)
					return
				kb = InlineKeyboardBuilder()
				for s in sessions:
					label = s.label or f"جلسة #{s.id}"
					kb.button(text=label, callback_data=f"mb:task_select_session:{task_id}:{s.id}")
				kb.adjust(1)
				await call.message.answer("اختر جلسة:", reply_markup=kb.as_markup())
				await call.answer()
				return
			else:
				await update_task(session, task_id=task_id, task_type=new_type, user_session_id=None)
				await session.commit()
				await call.answer("تم التبديل")

	@router.callback_query(F.data.startswith("mb:task_select_session:"))
	async def task_select_session(call: CallbackQuery):
		_, _, task_id_str, session_id_str = call.data.split(":", 3)
		task_id = int(task_id_str)
		session_id = int(session_id_str)
		async with AsyncSessionFactory() as session:
			await update_task(session, task_id=task_id, task_type="userbot", user_session_id=session_id)
			await session.commit()
		await call.answer("تم التعيين")

	@router.callback_query(F.data == "mb:settings")
	async def settings_menu(call: CallbackQuery):
		kb = InlineKeyboardBuilder()
		kb.button(text="🌐 تغيير اللغة", callback_data="mb:lang")
		kb.button(text="🕒 تغيير المنطقة الزمنية", callback_data="mb:tz")
		kb.button(text="👤 إعدادات اليوزربوت", callback_data="mb:userbot_settings")
		kb.adjust(1)
		await call.message.answer("الإعدادات:", reply_markup=kb.as_markup())
		await call.answer()

	@router.callback_query(F.data == "mb:lang")
	async def lang_menu(call: CallbackQuery):
		kb = InlineKeyboardBuilder()
		kb.button(text="العربية", callback_data="mb:lang:ar")
		kb.button(text="English", callback_data="mb:lang:en")
		kb.adjust(2)
		await call.message.answer("اختر اللغة:", reply_markup=kb.as_markup())
		await call.answer()

	@router.callback_query(F.data.startswith("mb:lang:"))
	async def lang_set(call: CallbackQuery):
		lang = call.data.split(":", 2)[2]
		async with AsyncSessionFactory() as session:
			owner = await _ensure_owner(call)
			if not owner:
				await call.answer("غير مصرح", show_alert=True)
				return
			owner.language_code = lang
			await session.merge(owner)
			await session.commit()
		await call.answer("تم")

	@router.callback_query(F.data == "mb:tz")
	async def tz_start(call: CallbackQuery, state: FSMContext):
		await state.set_state(SettingsState.waiting_timezone)
		await call.message.answer("أرسل المنطقة الزمنية (مثال: Asia/Riyadh)")
		await call.answer()

	@router.message(SettingsState.waiting_timezone)
	async def tz_finish(message: Message, state: FSMContext):
		candidate = message.text.strip()
		try:
			ZoneInfo(candidate)
		except Exception:
			await message.answer("منطقة زمنية غير صالحة")
			return
		async with AsyncSessionFactory() as session:
			owner = await _ensure_owner(message)
			if not owner:
				await state.clear()
				return
			owner.timezone = candidate
			await session.merge(owner)
			await session.commit()
		await state.clear()
		await message.answer("تم التحديث")

	# Userbot settings
	@router.callback_query(F.data == "mb:userbot_settings")
	async def ub_settings(call: CallbackQuery):
		owner = await _ensure_owner(call)
		if not owner:
			await call.answer("غير مصرح", show_alert=True)
			return
		async with AsyncSessionFactory() as session:
			sessions = await list_user_sessions(session, owner)
		kb = InlineKeyboardBuilder()
		kb.button(text="➕ إضافة بجلسة (Session String)", callback_data="mb:ub_add_session")
		kb.button(text="📱 تسجيل عبر رقم الهاتف", callback_data="mb:ub_add_phone")
		for s in sessions:
			label = s.label or f"جلسة #{s.id}"
			kb.button(text=label, callback_data=f"mb:ub_s:{s.id}")
		kb.adjust(1)
		await call.message.answer("جلسات اليوزربوت:", reply_markup=kb.as_markup())
		await call.answer()

	@router.callback_query(F.data == "mb:ub_add_session")
	async def ub_add_session(call: CallbackQuery, state: FSMContext):
		await state.set_state(UserbotState.waiting_session_string)
		await call.message.answer("أرسل Session String الخاصة ب Telethon")
		await call.answer()

	@router.message(UserbotState.waiting_session_string)
	async def ub_receive_session(message: Message, state: FSMContext):
		owner = await _ensure_owner(message)
		if not owner:
			await state.clear()
			return
		async with AsyncSessionFactory() as session:
			await create_user_session_from_string(session, owner, message.text.strip())
			await session.commit()
		await state.clear()
		await message.answer("تم حفظ الجلسة")

	# Phone login flow will be implemented in userbot_login module
	return router