from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserOut(BaseModel):
    _id: str
    email: EmailStr
    plan: str
    plan_expires_at: Optional[datetime] = None
    is_admin: bool
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_linked: bool
    created_at: datetime
