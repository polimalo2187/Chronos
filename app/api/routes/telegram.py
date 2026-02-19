from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.config import settings
from app.deps.auth import get_current_user
from app.schemas.telegram import LinkCodeOut, LinkConfirmIn
from app.services.telegram_link import create_link_code, consume_link_code
from app.db.mongo import get_db

router = APIRouter()


@router.post("/link-code", response_model=LinkCodeOut)
async def telegram_link_code(user: dict = Depends(get_current_user)):
    # create_link_code debe devolver: {"code": "...", "expires_at": datetime}
    data = await create_link_code(str(user["_id"]), expires_minutes=10)

    expires_at = data.get("expires_at")
    if expires_at is None:
        # Por si tu servicio devuelve expires_in directamente
        expires_in = int(data.get("expires_in_seconds", 0))
    else:
        # Normaliza expires_at para evitar naive vs aware
        if getattr(expires_at, "tzinfo", None) is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        expires_in = max(0, int((expires_at - now).total_seconds()))

    if not settings.telegram_bot_username:
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_USERNAME not configured")

    deep_link = f"https://t.me/{settings.telegram_bot_username}?start=link_{data['code']}"
    return {"code": data["code"], "expires_in_seconds": expires_in, "deep_link": deep_link}


@router.post("/link")
async def telegram_link_confirm(
    payload: LinkConfirmIn,
    x_tg_secret: str | None = Header(default=None),
):
    if not settings.telegram_link_secret:
        raise HTTPException(status_code=500, detail="TELEGRAM_LINK_SECRET not configured")
    if x_tg_secret != settings.telegram_link_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    link_doc = await consume_link_code(payload.code)
    if not link_doc:
        raise HTTPException(status_code=404, detail="Invalid or expired code")

    user_id = link_doc["user_id"]

    db = get_db()
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {
            "telegram_id": payload.telegram_id,
            "telegram_username": payload.telegram_username,
            "telegram_linked": True,
            "telegram_linked_at": datetime.now(timezone.utc),
        }},
    )
    return {"ok": True, "user_id": str(user_id)}
