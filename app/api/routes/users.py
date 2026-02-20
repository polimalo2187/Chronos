from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.deps.auth import get_current_user

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware_utc(dt: datetime) -> datetime:
    # Mongo a veces devuelve naive -> lo normalizamos
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _normalize_user_datetimes(user: dict) -> dict:
    # Normaliza campos datetime comunes para evitar líos de serialización/comparación
    for key in ("plan_expires_at", "banned_until", "created_at", "banned_at", "telegram_linked_at"):
        val = user.get(key)
        if isinstance(val, datetime):
            user[key] = _as_aware_utc(val)
    return user


def compute_account_state(user: dict) -> str:
    now = _now()

    # banned
    if user.get("status") == "banned":
        until = user.get("banned_until")
        if isinstance(until, datetime):
            until = _as_aware_utc(until)
            return "banned" if until > now else "inactive"
        return "banned"

    plan = user.get("plan", "free")
    exp = user.get("plan_expires_at")

    # free = trial
    if plan == "free":
        if not isinstance(exp, datetime):
            return "inactive"
        exp = _as_aware_utc(exp)
        return "trial" if exp > now else "inactive"

    # plus/premium
    if isinstance(exp, datetime):
        exp = _as_aware_utc(exp)
        return "active" if exp > now else "inactive"

    return "inactive"


@router.get("/me")
async def me(user=Depends(get_current_user)):
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)

    user = _normalize_user_datetimes(user)

    return {**user, "account_state": compute_account_state(user)}
