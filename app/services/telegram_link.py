from datetime import datetime, timedelta
import secrets
from bson import ObjectId

from app.db.mongo import get_db


LINK_EXPIRE_SECONDS = 600  # 10 minutos


def _utcnow():
    # Naive UTC (coherente con Mongo/Motor en este proyecto)
    return datetime.utcnow()


async def create_link_code(user_id: str, expires_minutes: int = 10):
    db = get_db()

    code = secrets.token_urlsafe(6)
    expires_at = _utcnow() + timedelta(minutes=expires_minutes)

    doc = {
        "user_id": ObjectId(user_id),
        "code": code,
        "expires_at": expires_at,
        "created_at": _utcnow(),
        "used": False,
    }

    await db.telegram_link_codes.insert_one(doc)

    # Tu route /link-code calcula expires_in_seconds, así que devolvemos expires_at
    return {
        "code": code,
        "expires_at": expires_at,
    }


async def consume_link_code(code: str):
    db = get_db()

    doc = await db.telegram_link_codes.find_one({"code": code, "used": False})
    if not doc:
        return None

    now = _utcnow()

    if doc.get("expires_at") and doc["expires_at"] < now:
        return None

    await db.telegram_link_codes.update_one(
        {"_id": doc["_id"]},
        {"$set": {"used": True}},
    )

    return doc
