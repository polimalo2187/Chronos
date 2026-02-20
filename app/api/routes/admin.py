from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Literal

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.deps.auth import require_admin
from app.schemas.user import PlanUpdateIn
from app.db.mongo import get_db

router = APIRouter()


# -----------------------
# Helpers
# -----------------------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _oid(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")


def _has_active_plan(user: dict) -> bool:
    exp = user.get("plan_expires_at")
    if isinstance(exp, datetime):
        return exp > _now()
    return False


def _is_banned(user: dict) -> bool:
    if user.get("status") == "banned":
        until = user.get("banned_until")
        if isinstance(until, datetime):
            # ban temporal vencido => lo consideramos no baneado,
            # pero idealmente se limpia con /unban
            return until > _now()
        # banned sin fecha => permanente
        return True
    return False


# -----------------------
# Inline schemas (admin only)
# -----------------------
PlanName = Literal["free", "plus", "premium"]


class LookupIn(BaseModel):
    email: Optional[EmailStr] = None
    telegram_id: Optional[int] = None


class PlanActivateIn(BaseModel):
    email: Optional[EmailStr] = None
    telegram_id: Optional[int] = None

    plan: PlanName = Field(..., description="plus o premium")
    days: int = Field(30, ge=1, le=365)


class BanIn(BaseModel):
    permanent: bool = False
    days: Optional[int] = Field(None, ge=1, le=3650)
    reason: Optional[str] = Field(None, max_length=300)


# -----------------------
# Existing endpoint (kept)
# -----------------------
@router.post("/users/{user_id}/plan")
async def admin_set_plan(
    user_id: str,
    payload: PlanUpdateIn,
    admin: dict = Depends(require_admin),
):
    db = get_db()
    oid = _oid(user_id)

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_banned(user):
        raise HTTPException(status_code=409, detail="User is banned. Unban first.")

    # Si plan_expires_at viene None, lo aceptamos (sin vencimiento)
    # Si viene datetime, lo guardamos tal cual
    await db.users.update_one(
        {"_id": oid},
        {"$set": {"plan": payload.plan, "plan_expires_at": payload.plan_expires_at, "status": "active"}},
    )

    return {"ok": True, "user_id": str(oid), "plan": payload.plan, "plan_expires_at": payload.plan_expires_at}


# -----------------------
# Optional: lookup user for admin UI
# -----------------------
@router.post("/users/lookup")
async def admin_lookup_user(
    payload: LookupIn,
    admin: dict = Depends(require_admin),
):
    if not payload.email and payload.telegram_id is None:
        raise HTTPException(status_code=400, detail="Provide email or telegram_id")

    db = get_db()
    q = {}
    if payload.email:
        q["email"] = payload.email.strip().lower()
    else:
        q["telegram_id"] = int(payload.telegram_id)

    user = await db.users.find_one(q)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # devolvemos lo mínimo para que el panel admin pueda operar
    return {
        "ok": True,
        "user_id": str(user["_id"]),
        "email": user.get("email"),
        "telegram_id": user.get("telegram_id"),
        "telegram_username": user.get("telegram_username"),
        "plan": user.get("plan"),
        "plan_expires_at": user.get("plan_expires_at"),
        "status": user.get("status", "active"),
        "banned_until": user.get("banned_until"),
    }


# -----------------------
# New: activate plan by email or telegram_id
# -----------------------
@router.post("/plan/activate")
async def admin_activate_plan(
    payload: PlanActivateIn,
    admin: dict = Depends(require_admin),
):
    if not payload.email and payload.telegram_id is None:
        raise HTTPException(status_code=400, detail="Provide email or telegram_id")

    if payload.plan == "free":
        # Free es trial, no lo activamos manualmente aquí
        raise HTTPException(status_code=400, detail="Use plus or premium")

    db = get_db()
    q = {}
    if payload.email:
        q["email"] = payload.email.strip().lower()
    else:
        q["telegram_id"] = int(payload.telegram_id)

    user = await db.users.find_one(q)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_banned(user):
        raise HTTPException(status_code=409, detail="User is banned. Unban first.")

    expires_at = _now() + timedelta(days=int(payload.days))

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"plan": payload.plan, "plan_expires_at": expires_at, "status": "active"}},
    )

    return {"ok": True, "user_id": str(user["_id"]), "plan": payload.plan, "plan_expires_at": expires_at}


# -----------------------
# New: ban user
# -----------------------
@router.post("/users/{user_id}/ban")
async def admin_ban_user(
    user_id: str,
    payload: BanIn,
    admin: dict = Depends(require_admin),
):
    db = get_db()
    oid = _oid(user_id)

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = _now()

    if payload.permanent:
        banned_until = None
    else:
        if payload.days is None:
            raise HTTPException(status_code=400, detail="days is required unless permanent=true")
        banned_until = now + timedelta(days=int(payload.days))

    await db.users.update_one(
        {"_id": oid},
        {"$set": {
            "status": "banned",
            "banned_until": banned_until,
            "ban_reason": payload.reason,
            "banned_at": now,
        }},
    )

    return {"ok": True, "user_id": str(oid), "status": "banned", "banned_until": banned_until, "reason": payload.reason}


# -----------------------
# New: unban user
# -----------------------
@router.post("/users/{user_id}/unban")
async def admin_unban_user(
    user_id: str,
    admin: dict = Depends(require_admin),
):
    db = get_db()
    oid = _oid(user_id)

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Si tiene plan vigente => active, si no => inactive
    new_status = "active" if _has_active_plan(user) else "inactive"

    await db.users.update_one(
        {"_id": oid},
        {"$set": {"status": new_status}, "$unset": {"banned_until": "", "ban_reason": "", "banned_at": ""}},
    )

    return {"ok": True, "user_id": str(oid), "status": new_status}
