from sqlalchemy import String, Integer, BigInteger, Boolean, ForeignKey, Text, UniqueConstraint, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from app.db.base import Base

class User(Base):
	__tablename__ = "users"
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
	language_code: Mapped[str | None] = mapped_column(String(8))
	timezone: Mapped[str | None] = mapped_column(String(64))
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	bots: Mapped[list[Bot]] = relationship(back_populates="owner", cascade="all, delete-orphan")

class Bot(Base):
	__tablename__ = "bots"
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
	name: Mapped[str] = mapped_column(String(128), nullable=False)
	username: Mapped[str | None] = mapped_column(String(64), index=True)
	description: Mapped[str | None] = mapped_column(String(512))
	token_encrypted: Mapped[str | None] = mapped_column(Text)  # encrypted token for bot api
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	owner: Mapped[User] = relationship(back_populates="bots")
	tasks: Mapped[list[Task]] = relationship(back_populates="bot", cascade="all, delete-orphan")
	__table_args__ = (
		Index("ix_bots_owner_active", "owner_id", "is_active"),
	)

class UserSession(Base):
	__tablename__ = "user_sessions"
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
	session_type: Mapped[str] = mapped_column(String(32))  # telethon
	session_encrypted: Mapped[str] = mapped_column(Text)   # encrypted session string
	label: Mapped[str | None] = mapped_column(String(128))
	created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	__table_args__ = (
		Index("ix_user_sessions_owner", "owner_id"),
	)

class Task(Base):
	__tablename__ = "tasks"
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), index=True)
	name: Mapped[str] = mapped_column(String(128), nullable=False)
	task_type: Mapped[str] = mapped_column(String(16))  # "bot" | "userbot"
	user_session_id: Mapped[int | None] = mapped_column(ForeignKey("user_sessions.id", ondelete="SET NULL"), index=True)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	config: Mapped[dict] = mapped_column(JSON, default=dict)
	created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	bot: Mapped[Bot] = relationship(back_populates="tasks")
	__table_args__ = (
		Index("ix_tasks_bot_active", "bot_id", "is_active"),
	)

class TaskRoutingRule(Base):
	__tablename__ = "task_routing_rules"
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
	source_chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
	destination_chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
	forward_mode: Mapped[str] = mapped_column(String(32), default="copy")  # copy/forward/quote
	filters: Mapped[dict] = mapped_column(JSON, default=dict)  # future: keywords, media types, users
	created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	__table_args__ = (
		Index("ix_rules_task", "task_id"),
	)