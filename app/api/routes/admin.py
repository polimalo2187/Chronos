from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Literal

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.deps.auth import require_admin
from app.schemas.user import PlanUpdateIn
from app.db.mongo import get_db
from app.core.config import settings

router = APIRouter()


# -----------------------
# Helpers
# -----------------------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware_utc(dt: datetime) -> datetime:
    # Mongo a veces devuelve naive -> normalizamos
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _oid(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")


def _is_datetime(v) -> bool:
    return isinstance(v, datetime)


def _has_active_plan(user: dict) -> bool:
    exp = user.get("plan_expires_at")
    if _is_datetime(exp):
        exp = _as_aware_utc(exp)
        return exp > _now()
    return False


def _is_banned(user: dict) -> bool:
    if user.get("status") != "banned":
        return False

    until = user.get("banned_until")

    # ban temporal
    if _is_datetime(until):
        until = _as_aware_utc(until)
        return until > _now()

    # ban permanente (sin fecha)
    return True


def _extend_or_start(now: datetime, current_expires: datetime | None, days: int) -> datetime:
    """
    Opción B:
    - si el usuario YA tiene plan activo con fecha, se le SUMAN días a su expiración actual
    - si no, empieza desde ahora
    """
    if current_expires and _is_datetime(current_expires):
        cur = _as_aware_utc(current_expires)
        if cur > now:
            return cur + timedelta(days=days)
    return now + timedelta(days=days)


async def _award_referral_if_needed(db, paid_user: dict, paid_plan: str) -> None:
    """
    Cuando un usuario referido pasa a plus/premium por PRIMERA vez,
    se suma 1 referido al referrer y, si llega a 5, se le activa plan automáticamente.
    """
    if paid_plan not in ("plus", "premium"):
        return

    referred_by = paid_user.get("referred_by")
    if not referred_by:
        return

    # Evita doble crédito
    if paid_user.get("referral_awarded", False):
        return

    # Marca al usuario como ya premiado (idempotencia)
    await db.users.update_one({"_id": paid_user["_id"]}, {"$set": {"referral_awarded": True}})

    field = "referrals_premium" if paid_plan == "premium" else "referrals_plus"

    # Incrementa contador del referrer
    await db.users.update_one({"_id": referred_by}, {"$inc": {field: 1}})

    # Relee referrer
    referrer = await db.users.find_one({"_id": referred_by})
    if not referrer:
        return

    plus = int(referrer.get("referrals_plus", 0) or 0)
    premium = int(referrer.get("referrals_premium", 0) or 0)

    paid_days = int(getattr(settings, "paid_plan_days", 30) or 30)
    now = _now()

    # Prioridad: si llega a 5 premium => premium.
    if premium >= 5:
        new_exp = _extend_or_start(now, referrer.get("plan_expires_at"), paid_days)
        await db.users.update_one(
            {"_id": referrer["_id"]},
            {"$set": {"plan": "premium", "plan_expires_at": new_exp, "status": "active"}},
        )
        return

    # Si llega a 5 plus => plus (solo si no está ya premium por suscripción)
    if plus >= 5:
        new_exp = _extend_or_start(now, referrer.get("plan_expires_at"), paid_days)
        # No bajamos a alguien que ya sea premium
        current_plan = referrer.get("plan")
        if current_plan != "premium":
            await db.users.update_one(
                {"_id": referrer["_id"]},
                {"$set": {"plan": "plus", "plan_expires_at": new_exp, "status": "active"}},
            )
        return


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


class BanIn(BaseModel):
    permanent: bool = False
    days: Optional[int] = Field(None, ge=1, le=3650)
    reason: Optional[str] = Field(None, max_length=300)


# -----------------------
# Admin: set plan by user_id
# (IMPORTANTE: Admin NO puede setear FREE)
# -----------------------
@router.post("/users/{user_id}/plan")
async def admin_set_plan(
    user_id: str,
    payload: PlanUpdateIn,
    admin: dict = Depends(require_admin),
):
    # Admin SOLO maneja plus/premium
    if payload.plan not in ("plus", "premium"):
        raise HTTPException(status_code=400, detail="Admin can only set plus or premium")

    db = get_db()
    oid = _oid(user_id)

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_banned(user):
        raise HTTPException(status_code=409, detail="User is banned. Unban first.")

    # Duración SIEMPRE 30 días (o lo que diga settings)
    paid_days = int(getattr(settings, "paid_plan_days", 30) or 30)
    expires_at = _now() + timedelta(days=paid_days)

    await db.users.update_one(
        {"_id": oid},
        {"$set": {"plan": payload.plan, "plan_expires_at": expires_at, "status": "active"}},
    )

    # Referidos (si aplica)
    paid_user = await db.users.find_one({"_id": oid})
    if paid_user:
        await _award_referral_if_needed(db, paid_user, payload.plan)

    return {"ok": True, "user_id": str(oid), "plan": payload.plan, "plan_expires_at": expires_at}


# -----------------------
# Admin: lookup user for panel UI
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

    # Normalizamos datetimes por si vienen naive
    pe = user.get("plan_expires_at")
    bu = user.get("banned_until")
    if _is_datetime(pe):
        pe = _as_aware_utc(pe)
    if _is_datetime(bu):
        bu = _as_aware_utc(bu)

    return {
        "ok": True,
        "user_id": str(user["_id"]),
        "email": user.get("email"),
        "telegram_id": user.get("telegram_id"),
        "telegram_username": user.get("telegram_username"),
        "plan": user.get("plan"),
        "plan_expires_at": pe,
        "status": user.get("status", "active"),
        "banned_until": bu,

        # Referidos (para el panel)
        "referral_code": user.get("referral_code"),
        "referred_by": str(user.get("referred_by")) if user.get("referred_by") else None,
        "referrals_plus": int(user.get("referrals_plus", 0) or 0),
        "referrals_premium": int(user.get("referrals_premium", 0) or 0),
    }


# -----------------------
# Admin: activate plan (plus/premium) by email or telegram_id
# (duración fija: settings.paid_plan_days)
# -----------------------
@router.post("/plan/activate")
async def admin_activate_plan(
    payload: PlanActivateIn,
    admin: dict = Depends(require_admin),
):
    if not payload.email and payload.telegram_id is None:
        raise HTTPException(status_code=400, detail="Provide email or telegram_id")

    if payload.plan not in ("plus", "premium"):
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

    paid_days = int(getattr(settings, "paid_plan_days", 30) or 30)
    expires_at = _now() + timedelta(days=paid_days)

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"plan": payload.plan, "plan_expires_at": expires_at, "status": "active"}},
    )

    # Referidos (si aplica)
    paid_user = await db.users.find_one({"_id": user["_id"]})
    if paid_user:
        await _award_referral_if_needed(db, paid_user, payload.plan)

    return {"ok": True, "user_id": str(user["_id"]), "plan": payload.plan, "plan_expires_at": expires_at}


# -----------------------
# Admin: ban user (temporal o permanente)
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
# Admin: unban user
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

    new_status = "active" if _has_active_plan(user) else "inactive"

    await db.users.update_one(
        {"_id": oid},
        {"$set": {"status": new_status},
         "$unset": {"banned_until": "", "ban_reason": "", "banned_at": ""}},
    )

    return {"ok": True, "user_id": str(oid), "status": new_status}
