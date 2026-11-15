"""
SQLAlchemy ORM models for QueueFlow.

Tables:
  managers     — user accounts (email + hashed password)
  queues       — a named queue owned by a manager
  tokens       — a person's queue ticket (the core entity)
  queue_stats  — daily aggregated analytics snapshots
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TokenStatus(str, enum.Enum):
    waiting = "waiting"
    serving = "serving"
    completed = "completed"
    cancelled = "cancelled"


class Manager(Base):
    __tablename__ = "managers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    queues: Mapped[list["Queue"]] = relationship("Queue", back_populates="manager")


class Queue(Base):
    __tablename__ = "queues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, default="")
    manager_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("managers.id"), nullable=False
    )
    # monotonically increasing counter — never reset, ensures unique token numbers
    next_token_number: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    manager: Mapped["Manager"] = relationship("Manager", back_populates="queues")
    tokens: Mapped[list["Token"]] = relationship("Token", back_populates="queue")


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    queue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("queues.id"), nullable=False
    )
    token_number: Mapped[int] = mapped_column(Integer, nullable=False)
    person_name: Mapped[str] = mapped_column(String, nullable=False)
    person_phone: Mapped[str] = mapped_column(String, default="")
    # position in the active queue (1-indexed). NULL when not waiting/serving.
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[TokenStatus] = mapped_column(
        Enum(TokenStatus), default=TokenStatus.waiting
    )
    # timestamps
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    called_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    queue: Mapped["Queue"] = relationship("Queue", back_populates="tokens")
