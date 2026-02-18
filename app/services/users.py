from datetime import datetime, timezone
from bson import ObjectId
from app.db.mongo import get_db
from app.core.security import hash_password, verify_password

async def create_user(email: str, password: str, is_admin: bool = False) -> ObjectId:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {
        "email": email.lower(),
        "password_hash": hash_password(password),
        "plan": "free",
        "plan_expires_at": None,
        "is_admin": bool(is_admin),
        "telegram_id": None,
        "telegram_username": None,
        "telegram_linked": False,
        "created_at": now,
    }
    res = await db.users.insert_one(doc)
    return res.inserted_id

async def authenticate(email: str, password: str) -> dict | None:
    db = get_db()
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return user
