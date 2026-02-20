from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field


PlanName = Literal["free", "plus", "premium"]
UserStatus = Literal["active", "inactive", "banned"]


class UserOut(BaseModel):
    _id: str
    email: EmailStr

    plan: PlanName
    plan_expires_at: Optional[datetime] = None

    status: UserStatus = "active"
    banned_until: Optional[datetime] = None

    # Trial control (free 7 días solo 1 vez)
    trial_used: bool = False

    is_admin: bool

    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_linked: bool

    created_at: datetime


class PlanUpdateIn(BaseModel):
    """
    Para el endpoint /admin/users/{user_id}/plan
    - plan: free/plus/premium
    - days: duración en días (por defecto 30 para plus/premium, 7 para free si se usa como trial)
    """
    plan: PlanName
    days: int = Field(30, ge=1, le=365)


class PlanActivateIn(BaseModel):
    """
    Activar por email o telegram_id (admin panel).
    """
    email: Optional[EmailStr] = None
    telegram_id: Optional[int] = None

    plan: PlanName
    days: int = Field(30, ge=1, le=365)
