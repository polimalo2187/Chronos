from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserOut(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr
    plan: str
    plan_expires_at: datetime | None = None
    is_admin: bool = False
    telegram_id: int | None = None
    telegram_username: str | None = None
    telegram_linked: bool = False
    created_at: datetime

class PlanUpdateIn(BaseModel):
    plan: str = Field(..., pattern="^(free|plus|premium)$")
    days: int = Field(30, ge=1, le=365)
