from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Literal

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.deps.auth import require_admin
from app.schemas.user import PlanUpdateIn
from app.db.mongo import get_db

router = APIRouter()


# -----------------------
# Helpers
# -----------------------
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_object_id(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")


def _compute_status_after_unban(user_doc: dict) -> str:
    """
    Si el usuario tiene plan vigente -> active, si no -> inactive.
    (Banned siempre lo quita el unban.)
    """
    now = _now_utc()
    plan = (user_doc.get("plan") or "").lower()
    expires_at = user_doc.get("plan_expires_at")

    if expires_at and isinstance(expires_at, datetime) and expires_at > now:
        return "active"

    # Si no hay expiración, asumimos que no tiene plan vigente.
    # (En tu sistema: al expirar no vuelve a free)
    return "inactive"


# -----------------------
# Request models (inline)
# -----------------------
PlanName = Literal["free", "plus", "premium"]


class PlanActivateIn(BaseModel):
    # Identificador: uno de los dos
    email: Optional[str] = None
    telegram_id: Optional[int] = None

    plan: PlanName = Field(..., description="plus o premium (free no se activa manualmente normalmente)")
    days: int = Field(30, ge=1, le=365, description="Duración del plan en días")


class BanIn(BaseModel):
    # Si permanent=True, ignoramos days
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
    oid = _to_object_id(user_id)

    db = get_db()
    expires_at = _now_utc() + timedelta(days=payload.days)

    # Si está baneado, por defecto NO dejamos setear plan sin desbanear
    u = await db.users.find_one({"_id": oid})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if (u.get("status") == "banned") or (u.get("banned_until") and isinstance(u["banned_until"], datetime) and u["banned_until"] > _now_utc()):
        raise HTTPException(status_code=409, detail="User is banned. Unban first.")

    res = await db.users.update_one(
        {"_id": oid},
        {"$set": {"plan": payload.plan, "plan_expires_at": expires_at, "status": "active"}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"ok": True, "user_id": str(oid), "plan": payload.plan, "plan_expires_at": expires_at}


# -----------------------
# New: Activate plan by email or telegram_id
# -----------------------
@router.post("/plan/activate")
async def admin_activate_plan(
    payload: PlanActivateIn,
    admin: dict = Depends(require_admin),
):
    if not payload.email and payload.telegram_id is None:
        raise HTTPException(status_code=400, detail="Provide email or telegram_id")

    if payload.plan == "free":
        # Free es trial; normalmente no se reactiva manualmente
        raise HTTPException(status_code=400, detail="Use plus or premium for manual activation")

    db = get_db()
    query = {}
    if payload.email:
        query["email"] = payload.email.strip().lower()
    else:
        query["telegram_id"] = int(payload.telegram_id)

    user = await db.users.find_one(query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Si está baneado, no activamos hasta desban
    now = _now_utc()
    banned_until = user.get("banned_until")
    if user.get("status") == "banned":
        # si el ban era temporal y ya pasó, lo consideramos no baneado, pero limpiarlo es mejor con /unban
        if isinstance(banned_until, datetime) and banned_until <= now:
            pass
        else:
            raise HTTPException(status_code=409, detail="User is banned. Unban first.")

    expires_at = now + timedelta(days=payload.days)

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"plan": payload.plan, "plan_expires_at": expires_at, "status": "active"}},
    )

    return {"ok": True, "user_id": str(user["_id"]), "plan": payload.plan, "plan_expires_at": expires_at}


# -----------------------
# New: Ban user (temporary or permanent)
# -----------------------
@router.post("/users/{user_id}/ban")
async def admin_ban_user(
    user_id: str,
    payload: BanIn,
    admin: dict = Depends(require_admin),
):
    oid = _to_object_id(user_id)
    db = get_db()

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = _now_utc()

    banned_until = None
    if payload.permanent:
        banned_until = None
    else:
        # Si no es permanente, days es requerido
        if payload.days is None:
            raise HTTPException(status_code=400, detail="days is required unless permanent=true")
        banned_until = now + timedelta(days=int(payload.days))

    update = {
        "status": "banned",
        "banned_until": banned_until,
        "ban_reason": payload.reason,
        "banned_at": now,
    }

    await db.users.update_one({"_id": oid}, {"$set": update})

    return {
        "ok": True,
        "user_id": str(oid),
        "status": "banned",
        "banned_until": banned_until,
        "reason": payload.reason,
    }


# -----------------------
# New: Unban user
# -----------------------
@router.post("/users/{user_id}/unban")
async def admin_unban_user(
    user_id: str,
    admin: dict = Depends(require_admin),
):
    oid = _to_object_id(user_id)
    db = get_db()

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_status = _compute_status_after_unban(user)

    await db.users.update_one(
        {"_id": oid},
        {"$set": {"status": new_status}, "$unset": {"banned_until": "", "ban_reason": "", "banned_at": ""}},
    )

    return {"ok": True, "user_id": str(oid), "status": new_status}
