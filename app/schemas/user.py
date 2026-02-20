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
    Para el endpoint /admin/users/{user_id}/plan (modo avanzado):
    - plan: free/plus/premium
    - plan_expires_at:
        - null => sin vencimiento
        - datetime => vencimiento exacto
    """
    plan: PlanName
    plan_expires_at: Optional[datetime] = None


class PlanActivateIn(BaseModel):
    """
    Activar PLUS/PREMIUM por email o telegram_id (modo panel).
    Duración real se calcula en backend con settings.paid_plan_days.
    """
    email: Optional[EmailStr] = None
    telegram_id: Optional[int] = None

    plan: Literal["plus", "premium"]
