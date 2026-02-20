# app/api/routes/auth.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pymongo.errors import DuplicateKeyError

from app.core.security import create_access_token
from app.db.mongo import get_db
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.services.users import create_user, authenticate

router = APIRouter()


@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn):
    """
    Registro:
    - El usuario entra automáticamente en FREE por X días (trial).
    - Esa lógica se aplica en create_user() (app/services/users.py).
    - El admin NO maneja FREE; solo PLUS/PREMIUM vía endpoints admin.
    """
    db = get_db()

    email = payload.email.strip().lower()

    # Si ya existe email, 409
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Crear usuario (create_user ya setea: plan=free, plan_expires_at=now+trial_days, status=active, trial_used=True)
    try:
        user_id = await create_user(email, payload.password, is_admin=False)
    except DuplicateKeyError:
        # Por si hubo carrera entre requests
        raise HTTPException(status_code=409, detail="Email already registered")

    token = create_access_token(str(user_id))
    return {"access_token": token}


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn):
    """
    Login normal.
    La restricción de acceso (banned/inactive/expired) la aplica get_current_user
    cuando intentan consumir endpoints protegidos.
    """
    user = await authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["_id"]))
    return {"access_token": token}
