# app/services/users.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from bson import ObjectId

from app.db.mongo import get_db
from app.core.security import hash_password, verify_password
from app.core.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def create_user(email: str, password: str, is_admin: bool = False) -> ObjectId:
    db = get_db()
    now = _now()

    # Hash seguro (puede lanzar ValueError si >72 bytes)
    password_hash = hash_password(password)

    # ✅ REGLA CHRONOS:
    # - Al registrarse: el usuario entra FREE automáticamente por 7 días (trial_days)
    # - Admin NO maneja free; solo plus/premium (eso va por endpoints admin)
    if is_admin:
        plan = "free"
        plan_expires_at = None
        trial_used = False
        status = "active"
    else:
        trial_days = int(getattr(settings, "trial_days", 7) or 7)
        plan = "free"
        plan_expires_at = now + timedelta(days=trial_days)
        trial_used = True
        status = "active"

    doc = {
        "email": email.strip().lower(),
        "password_hash": password_hash,

        # Plan defaults
        "plan": plan,
        "plan_expires_at": plan_expires_at,

        # Access control
        "status": status,
        "trial_used": trial_used,

        "is_admin": bool(is_admin),

        # Telegram
        "telegram_id": None,
        "telegram_username": None,
        "telegram_linked": False,

        "created_at": now,
    }

    res = await db.users.insert_one(doc)
    return res.inserted_id


async def authenticate(email: str, password: str) -> dict | None:
    db = get_db()
    user = await db.users.find_one({"email": email.strip().lower()})
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return user
