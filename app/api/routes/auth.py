from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.security import create_access_token
from app.db.mongo import get_db
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.services.users import create_user, authenticate
from app.deps.auth import get_current_user

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn):
    """
    Registro = Plan FREE (trial) por settings.trial_days (default 7).
    A los X días, queda inactive y no se reactiva solo.
    """
    db = get_db()

    email = payload.email.strip().lower()

    # Si ya existe email, 409
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Resolver referido (si viene)
    referred_by: ObjectId | None = None
    if payload.referral_code:
        code = payload.referral_code.strip().upper()
        referrer = await db.users.find_one({"referral_code": code}, {"_id": 1})
        if not referrer:
            raise HTTPException(status_code=400, detail="Invalid referral_code")
        referred_by = referrer["_id"]

    # Crear usuario
    try:
        user_id = await create_user(email, payload.password, is_admin=False, referred_by=referred_by)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Aplicar trial FREE automáticamente
    trial_days = int(getattr(settings, "trial_days", 7) or 7)
    expires_at = _now() + timedelta(days=trial_days)

    await db.users.update_one(
        {"_id": user_id},
        {"$set": {
            "plan": "free",
            "plan_expires_at": expires_at,
            "status": "active",
            "trial_used": True,
        }},
    )

    token = create_access_token(str(user_id))
    return {"access_token": token}


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn):
    user = await authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user["_id"]))
    return {"access_token": token}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """Devuelve el usuario actual (para la UI)."""
    user = dict(user)
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)

    # Campos útiles para UI
    for key in ("plan_expires_at", "created_at", "banned_until", "banned_at", "telegram_linked_at"):
        val = user.get(key)
        if isinstance(val, datetime) and val.tzinfo is None:
            user[key] = val.replace(tzinfo=timezone.utc)

    return {
        **user,
        "referral": {
            "code": user.get("referral_code"),
            "referred_by": str(user.get("referred_by")) if user.get("referred_by") else None,
            "plus": int(user.get("referrals_plus", 0) or 0),
            "premium": int(user.get("referrals_premium", 0) or 0),
        }
    }
