from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.security import create_access_token
from app.db.mongo import get_db
from app.deps.auth import get_current_user
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.services.users import create_user, authenticate

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn):
    """
    Registro = Plan FREE (trial) automático por settings.trial_days (default 7).
    """
    db = get_db()

    email = payload.email.strip().lower()

    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        user_id = await create_user(email, payload.password, is_admin=False)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")

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
    """
    Devuelve el usuario actual (para UI: plan/status/expiración).
    """
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    return user
