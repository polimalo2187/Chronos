# app/deps/auth.py

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.db.mongo import get_db

bearer = HTTPBearer(auto_error=False)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware_utc(dt: datetime) -> datetime:
    # Mongo puede devolver naive -> lo normalizamos
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _is_datetime(value) -> bool:
    return isinstance(value, datetime)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = decode_token(creds.credentials)
        sub = payload.get("sub")
        if not sub:
            raise ValueError("Missing sub")
        user_id = ObjectId(sub)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = get_db()
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    now = _now()

    # ---------
    # BAN LOGIC
    # ---------
    if user.get("status") == "banned":
        banned_until = user.get("banned_until")

        # ban temporal
        if _is_datetime(banned_until):
            banned_until = _as_aware_utc(banned_until)
            if banned_until > now:
                raise HTTPException(status_code=403, detail="User banned")
            # ban vencido -> dejamos pasar (ideal limpiar con /admin/users/{id}/unban)

        else:
            # ban permanente (sin fecha)
            raise HTTPException(status_code=403, detail="User banned")

    # -------------------
    # PLAN / ACCESS LOGIC
    # -------------------
    # Admin puede entrar incluso si status inactive o plan expirado (pero NO si está banned)
    if user.get("is_admin", False):
        return user

    # Si está inactive, cortamos
    if user.get("status") == "inactive":
        raise HTTPException(status_code=403, detail="Plan inactive")

    plan = user.get("plan", "free")
    exp = user.get("plan_expires_at")

    # Si no hay expiración guardada => NO se da acceso (evita bugs/datos inconsistentes)
    if not _is_datetime(exp):
        # Free siempre debe tener expiración (trial)
        # Plus/Premium siempre debe tener expiración (30 días)
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"status": "inactive"}},
        )
        raise HTTPException(status_code=403, detail="Plan inactive")

    exp = _as_aware_utc(exp)

    # Si el plan expira y ya venció => marcamos inactive y cortamos
    if exp <= now:
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"status": "inactive"}},
        )
        raise HTTPException(status_code=403, detail="Plan expired")

    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin only")
    return user
