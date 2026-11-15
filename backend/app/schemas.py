"""
Pydantic schemas (request/response models) for QueueFlow.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.models.models import TokenStatus


# ── Auth ─────────────────────────────────────────────────────────────────────

class ManagerCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class ManagerOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    manager_id: Optional[int] = None


# ── Queue ─────────────────────────────────────────────────────────────────────

class QueueCreate(BaseModel):
    name: str
    description: str = ""

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Queue name cannot be empty")
        return v.strip()


class QueueUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class QueueOut(BaseModel):
    id: int
    name: str
    description: str
    manager_id: int
    is_active: bool
    created_at: datetime
    # these are computed in the endpoint, not stored columns
    waiting_count: int = 0
    serving_count: int = 0

    model_config = {"from_attributes": True}


# ── Token / Person ────────────────────────────────────────────────────────────

class PersonRegister(BaseModel):
    person_name: str
    person_phone: str = ""

    @field_validator("person_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Person name cannot be empty")
        return v.strip()


class TokenOut(BaseModel):
    id: int
    queue_id: int
    token_number: int
    person_name: str
    person_phone: str
    position: Optional[int]
    status: TokenStatus
    joined_at: datetime
    called_at: Optional[datetime]
    completed_at: Optional[datetime]
    # computed fields
    estimated_wait_minutes: Optional[float] = None
    actual_wait_minutes: Optional[float] = None
    service_duration_minutes: Optional[float] = None

    model_config = {"from_attributes": True}


# ── Analytics ─────────────────────────────────────────────────────────────────

class QueueAnalytics(BaseModel):
    queue_id: int
    queue_name: str
    total_tokens: int
    completed_tokens: int
    cancelled_tokens: int
    waiting_tokens: int
    serving_tokens: int
    avg_wait_minutes: Optional[float]
    avg_service_minutes: Optional[float]
    # last 7 days daily breakdown
    daily_stats: list[dict]


class OverallAnalytics(BaseModel):
    total_queues: int
    total_tokens_today: int
    total_completed_today: int
    total_cancelled_today: int
    avg_wait_minutes: Optional[float]
    avg_service_minutes: Optional[float]
    queue_analytics: list[QueueAnalytics]
