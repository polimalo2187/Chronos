from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.deps.auth import get_current_user

router = APIRouter()


def compute_account_state(user: dict) -> str:
    """
    Estados finales de la cuenta:
    - active
    - inactive
    - trial
    - banned
    """

    # ban permanente o temporal activo
    if user.get("status") == "banned":
        until = user.get("banned_until")
        if until is None:
            return "banned"
        if isinstance(until, datetime) and until > datetime.now(timezone.utc):
            return "banned"

    plan = user.get("plan", "free")
    exp = user.get("plan_expires_at")

    # FREE = trial
    if plan == "free":
        if not exp:
            return "inactive"
        return "trial" if exp > datetime.now(timezone.utc) else "inactive"

    # PLUS / PREMIUM
    if exp and exp > datetime.now(timezone.utc):
        return "active"

    return "inactive"


@router.get("/me")
async def me(user=Depends(get_current_user)):
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)

    state = compute_account_state(user)

    return {
        **user,
        "account_state": state
    }
