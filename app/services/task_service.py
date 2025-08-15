from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Task, TaskRoutingRule, Bot

async def create_task(session: AsyncSession, bot: Bot, name: str, task_type: str, config: dict | None = None, user_session_id: int | None = None) -> Task:
	task = Task(bot_id=bot.id, name=name, task_type=task_type, config=config or {}, user_session_id=user_session_id)
	session.add(task)
	await session.flush()
	return task

async def list_tasks(session: AsyncSession, bot: Bot) -> list[Task]:
	res = await session.execute(select(Task).where(Task.bot_id == bot.id).order_by(Task.id.desc()))
	return list(res.scalars().all())

async def toggle_task(session: AsyncSession, task_id: int, active: bool) -> Task | None:
	res = await session.execute(select(Task).where(Task.id == task_id))
	task = res.scalar_one_or_none()
	if task is None:
		return None
	task.is_active = active
	await session.flush()
	return task

async def update_task(session: AsyncSession, task_id: int, name: str | None = None, task_type: str | None = None, config: dict | None = None, user_session_id: int | None = None) -> Task | None:
	res = await session.execute(select(Task).where(Task.id == task_id))
	task = res.scalar_one_or_none()
	if task is None:
		return None
	if name is not None:
		task.name = name
	if task_type is not None:
		task.task_type = task_type
	if config is not None:
		task.config = config
	if user_session_id is not None:
		task.user_session_id = user_session_id
	await session.flush()
	return task

async def delete_task(session: AsyncSession, task_id: int) -> bool:
	res = await session.execute(select(Task).where(Task.id == task_id))
	task = res.scalar_one_or_none()
	if task is None:
		return False
	await session.delete(task)
	await session.flush()
	return True

async def add_routing_rule(session: AsyncSession, task: Task, source_chat_id: int, destination_chat_id: int, forward_mode: str = "copy", filters: dict | None = None) -> TaskRoutingRule:
	rule = TaskRoutingRule(task_id=task.id, source_chat_id=source_chat_id, destination_chat_id=destination_chat_id, forward_mode=forward_mode, filters=filters or {})
	session.add(rule)
	await session.flush()
	return rule

async def list_routing_rules(session: AsyncSession, task: Task) -> list[TaskRoutingRule]:
	res = await session.execute(select(TaskRoutingRule).where(TaskRoutingRule.task_id == task.id).order_by(TaskRoutingRule.id.desc()))
	return list(res.scalars().all())

async def delete_routing_rule(session: AsyncSession, rule_id: int) -> bool:
	res = await session.execute(select(TaskRoutingRule).where(TaskRoutingRule.id == rule_id))
	rule = res.scalar_one_or_none()
	if rule is None:
		return False
	await session.delete(rule)
	await session.flush()
	return True