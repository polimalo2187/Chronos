from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr


PlanName = Literal["free", "plus", "premium"]


class UserOut(BaseModel):
    _id: str
    email: EmailStr
    plan: PlanName
    plan_expires_at: Optional[datetime] = None
    is_admin: bool
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_linked: bool
    created_at: datetime


class PlanUpdateIn(BaseModel):
    plan: PlanName
    # Si quieres que sea "sin vencimiento", envía null.
    # Si quieres poner vencimiento, manda un ISO datetime.
    plan_expires_at: Optional[datetime] = None
