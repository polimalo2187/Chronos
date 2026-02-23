from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


PlanName = Literal["free", "plus", "premium"]
UserStatus = Literal["active", "inactive", "banned"]


class UserOut(BaseModel):
    """
    Response model para /me.
    IMPORTANTÍSIMO:
    - Todo lo "nuevo" va OPTIONAL para que no tumbe la API si en Mongo todavía no existe.
    """
    model_config = ConfigDict(extra="ignore")

    _id: str
    email: EmailStr

    plan: PlanName = "free"
    plan_expires_at: Optional[datetime] = None

    # Control de acceso / bloqueos
    status: Optional[UserStatus] = "active"
    banned_until: Optional[datetime] = None
    trial_used: Optional[bool] = False

    is_admin: bool = False

    # Telegram
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_linked: Optional[bool] = False

    created_at: datetime


class PlanUpdateIn(BaseModel):
    """
    Para /admin/users/{user_id}/plan
    (tu endpoint usa payload.days)
    """
    plan: PlanName
    days: int = Field(30, ge=1, le=365)


class PlanActivateIn(BaseModel):
    """
    Para activar por email o telegram_id.
    """
    email: Optional[EmailStr] = None
    telegram_id: Optional[int] = None

    plan: PlanName
    days: int = Field(30, ge=1, le=365)
