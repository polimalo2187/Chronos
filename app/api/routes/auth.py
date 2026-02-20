from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.security import create_access_token
from app.db.mongo import get_db
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.services.users import create_user, authenticate

router = APIRouter()


def _now():
    return datetime.now(timezone.utc)


@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn):
    """
    Registro = Plan FREE (trial) por settings.trial_days (default 7).
    A los X días, queda inactive y no se reactiva solo.
    """
    db = get_db()

    # Si ya existe email, 409
    existing = await db.users.find_one({"email": payload.email.strip().lower()})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Crear usuario (crea password_hash + email)
    try:
        user_id = await create_user(payload.email, payload.password, is_admin=False)
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
    """
    Login normal.
    La restricción de acceso (banned/inactive/expired) la aplica get_current_user
    cuando intentan consumir endpoints.
    """
    user = await authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["_id"]))
    return {"access_token": token}
