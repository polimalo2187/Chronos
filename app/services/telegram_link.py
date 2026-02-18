import secrets
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from fastapi import HTTPException
from app.db.mongo import get_db

def _gen_code(nbytes: int = 6) -> str:
    return secrets.token_urlsafe(nbytes).replace("-", "").replace("_", "")[:10]

async def create_link_code(user_id: ObjectId, expires_minutes: int = 10) -> dict:
    db = get_db()
    code = _gen_code()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expires_minutes)
    doc = {
        "user_id": user_id,
        "code": code,
        "expires_at": expires_at,
        "used_at": None,
        "created_at": now,
    }
    try:
        await db.telegram_link_codes.insert_one(doc)
    except Exception:
        code = _gen_code()
        doc["code"] = code
        await db.telegram_link_codes.insert_one(doc)
    return {"code": code, "expires_at": expires_at}

async def consume_link_code(code: str) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = await db.telegram_link_codes.find_one({"code": code})
    if not doc:
        raise HTTPException(status_code=404, detail="Code not found")
    if doc.get("used_at"):
        raise HTTPException(status_code=409, detail="Code already used")
    if doc.get("expires_at") and doc["expires_at"] < now:
        raise HTTPException(status_code=410, detail="Code expired")
    await db.telegram_link_codes.update_one({"_id": doc["_id"]}, {"$set": {"used_at": now}})
    return doc
