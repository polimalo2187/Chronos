from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.deps.auth import require_admin
from app.schemas.user import PlanUpdateIn
from app.db.mongo import get_db

router = APIRouter()

@router.post("/users/{user_id}/plan")
async def admin_set_plan(user_id: str, payload: PlanUpdateIn, admin: dict = Depends(require_admin)):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    db = get_db()
    expires_at = datetime.now(timezone.utc) + timedelta(days=payload.days)
    res = await db.users.update_one(
        {"_id": oid},
        {"$set": {"plan": payload.plan, "plan_expires_at": expires_at}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True, "plan": payload.plan, "plan_expires_at": expires_at}
