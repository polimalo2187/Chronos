from __future__ import annotations

from datetime import datetime, timezone
import secrets
import string

from bson import ObjectId

from app.db.mongo import get_db
from app.core.security import hash_password, verify_password


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _generate_unique_referral_code(length: int = 8) -> str:
    """Genera un código único para compartir (para referidos)."""
    alphabet = string.ascii_uppercase + string.digits
    db = get_db()

    # Intentos con colisión muy improbable, pero lo hacemos seguro.
    for _ in range(20):
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        exists = await db.users.find_one({"referral_code": code}, {"_id": 1})
        if not exists:
            return code

    # fallback: token_urlsafe recortado
    for _ in range(20):
        code = secrets.token_urlsafe(6).replace("-", "").replace("_", "").upper()[:length]
        exists = await db.users.find_one({"referral_code": code}, {"_id": 1})
        if not exists:
            return code

    raise RuntimeError("Could not generate unique referral code")


async def create_user(email: str, password: str, is_admin: bool = False, referred_by: ObjectId | None = None) -> ObjectId:
    db = get_db()
    now = _now()

    password_hash = hash_password(password)
    referral_code = await _generate_unique_referral_code()

    doc = {
        "email": email.strip().lower(),
        "password_hash": password_hash,

        # Defaults: register setea trial expiry
        "plan": "free",
        "plan_expires_at": None,

        # Access control
        "status": "active",
        "trial_used": False,

        "is_admin": bool(is_admin),

        # Telegram
        "telegram_id": None,
        "telegram_username": None,
        "telegram_linked": False,

        # Referidos
        "referral_code": referral_code,
        "referred_by": referred_by,           # ObjectId del referrer
        "referral_awarded": False,            # evita doble crédito
        "referrals_plus": 0,
        "referrals_premium": 0,

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
