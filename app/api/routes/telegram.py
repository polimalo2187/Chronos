from fastapi import APIRouter, Depends, Header, HTTPException
from datetime import datetime, timezone
from bson import ObjectId
from app.deps.auth import get_current_user
from app.schemas.telegram import LinkCodeOut, LinkConfirmIn
from app.services.telegram_link import create_link_code, consume_link_code
from app.core.config import settings
from app.db.mongo import get_db

router = APIRouter()

@router.post("/link-code", response_model=LinkCodeOut)
async def telegram_link_code(user: dict = Depends(get_current_user)):
    data = await create_link_code(user["_id"], expires_minutes=10)
    expires_at = data["expires_at"]
    now = datetime.now(timezone.utc)
    expires_in = max(0, int((expires_at - now).total_seconds()))
    deep_link = f"https://t.me/{settings.telegram_bot_username}?start=link_{data['code']}"
    return {"code": data["code"], "expires_in_seconds": expires_in, "deep_link": deep_link}

@router.post("/link")
async def telegram_link_confirm(payload: LinkConfirmIn, x_tg_secret: str | None = Header(default=None)):
    if not settings.telegram_link_secret:
        raise HTTPException(status_code=500, detail="TELEGRAM_LINK_SECRET not configured")
    if x_tg_secret != settings.telegram_link_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    link_doc = await consume_link_code(payload.code)
    user_id: ObjectId = link_doc["user_id"]

    db = get_db()
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {
            "telegram_id": payload.telegram_id,
            "telegram_username": payload.telegram_username,
            "telegram_linked": True,
            "telegram_linked_at": datetime.now(timezone.utc)
        }}
    )
    return {"ok": True, "user_id": str(user_id)}
