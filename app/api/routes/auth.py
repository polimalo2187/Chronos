from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.security import create_access_token
from app.db.mongo import get_db
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.services.users import create_user, authenticate
from app.deps.auth import get_current_user

router = APIRouter()


def _now():
    return datetime.now(timezone.utc)


@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn):
    """
    Registro = Plan FREE (trial) por settings.trial_days (default 7).
    """
    db = get_db()

    existing = await db.users.find_one({"email": payload.email.strip().lower()})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        user_id = await create_user(payload.email, payload.password, is_admin=False)
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
async def me(user: dict = get_current_user):
    """
    NOTA: Este endpoint depende de tu deps/auth.py; como ya lo tienes funcionando,
    lo dejamos simple: retorna datos seguros del usuario.
    """
    # Si FastAPI no resuelve esto así en tu repo, dime y lo ajusto al patrón Depends.
    user = await user  # compat por si viene como coroutine (según tu deps)
    return {
        "id": str(user.get("_id")),
        "email": user.get("email"),
        "plan": user.get("plan", "free"),
        "plan_expires_at": user.get("plan_expires_at"),
        "status": user.get("status", "active"),
        "is_admin": bool(user.get("is_admin", False)),
        "telegram_id": user.get("telegram_id"),
        "telegram_username": user.get("telegram_username"),
}
