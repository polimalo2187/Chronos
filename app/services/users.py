from __future__ import annotations

from datetime import datetime, timezone
from bson import ObjectId

from app.db.mongo import get_db
from app.core.security import hash_password, verify_password


async def create_user(email: str, password: str, is_admin: bool = False) -> ObjectId:
    db = get_db()
    now = datetime.now(timezone.utc)

    # Hash seguro (puede lanzar ValueError si >72 bytes)
    password_hash = hash_password(password)

    doc = {
        "email": email.strip().lower(),
        "password_hash": password_hash,

        # Defaults (register luego setea trial expiry)
        "plan": "free",
        "plan_expires_at": None,

        # Access control
        "status": "active",
        "trial_used": False,  # register lo pone True cuando setea expiry

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
