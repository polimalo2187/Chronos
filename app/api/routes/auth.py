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
from app.services.referral_service import get_or_create_referral_code
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
@router.get("/me")
async def me(user=Depends(get_current_user)):
    # get_current_user puede devolver dict o coroutine según implementación; normalizamos aquí
    if callable(user):
        user = user()
    if hasattr(user, "__await__"):
        user = await user

    # Asegura que el usuario tenga un código de referido generado (si no existe)
    user = await get_or_create_referral_code(user)

    referral = user.get("referral") or {}
    return {
        "_id": str(user.get("_id")),
        "email": user.get("email"),
        "plan": user.get("plan", "free"),
        "plan_expires_at": user.get("plan_expires_at"),
        "is_admin": bool(user.get("is_admin", False)),
        "telegram_id": user.get("telegram_id"),
        "telegram_username": user.get("telegram_username"),
        "telegram_linked": bool(user.get("telegram_linked", False)),
        "created_at": user.get("created_at"),
        "telegram_linked_at": user.get("telegram_linked_at"),
        "status": user.get("status", "active"),
        "account_state": user.get("account_state", "active"),
        "referral": {
            "code": referral.get("code"),
            "referred_by": referral.get("referred_by"),
            "plus": int(referral.get("plus", 0) or 0),
            "premium": int(referral.get("premium", 0) or 0),
        },
    }

