from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from app.db.base import AsyncSessionFactory
from app.db.models import Bot, Task
from app.services.task_service import create_task, list_tasks, delete_task, toggle_task
from app.services.user_service import get_or_create_user

router = Router()

@router.callback_query(F.data.startswith("tasks:"))
async def on_tasks_menu(call: CallbackQuery):
	bot_id = int(call.data.split(":", 1)[1])
	async with AsyncSessionFactory() as session:
		user = await get_or_create_user(session, call.from_user.id, language_code=call.from_user.language_code)
		res = await session.execute(select(Bot).where(Bot.id == bot_id, Bot.owner_id == user.id))
		bot = res.scalar_one_or_none()
		if bot is None:
			await call.answer("غير موجود", show_alert=True)
			return
		tasks = await list_tasks(session, bot)
	builder = InlineKeyboardBuilder()
	builder.button(text="➕ إضافة مهمة", callback_data=f"task_add:{bot_id}")
	for t in tasks:
		status = "🟢" if t.is_active else "⚪"
		builder.button(text=f"{status} {t.name}", callback_data=f"task:{t.id}")
	builder.adjust(1)
	await call.message.answer("مهام البوت:", reply_markup=builder.as_markup())
	await call.answer()

@router.callback_query(F.data.startswith("task:"))
async def on_task_item(call: CallbackQuery):
	task_id = int(call.data.split(":", 1)[1])
	builder = InlineKeyboardBuilder()
	builder.button(text="تعطيل/تنشيط", callback_data=f"task_toggle:{task_id}")
	builder.button(text="حذف", callback_data=f"task_delete:{task_id}")
	builder.adjust(2)
	await call.message.answer("إدارة المهمة:", reply_markup=builder.as_markup())
	await call.answer()

@router.callback_query(F.data.startswith("task_toggle:"))
async def on_task_toggle(call: CallbackQuery):
	task_id = int(call.data.split(":", 1)[1])
	async with AsyncSessionFactory() as session:
		res = await session.execute(select(Task).where(Task.id == task_id))
		t = res.scalar_one_or_none()
		if t is None:
			await call.answer("غير موجود", show_alert=True)
			return
		await toggle_task(session, task_id, not t.is_active)
		await session.commit()
	await call.answer("تم")

@router.callback_query(F.data.startswith("task_delete:"))
async def on_task_delete(call: CallbackQuery):
	task_id = int(call.data.split(":", 1)[1])
	async with AsyncSessionFactory() as session:
		ok = await delete_task(session, task_id)
		await session.commit()
	if ok:
		await call.answer("تم الحذف")
	else:
		await call.answer("غير موجود", show_alert=True)