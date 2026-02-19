from datetime import datetime, timedelta, timezone
import secrets
from bson import ObjectId

from app.db.connection import get_db


LINK_EXPIRE_SECONDS = 600  # 10 minutos


def _utcnow():
    # Siempre naive UTC (Mongo y Pydantic aman esto)
    return datetime.utcnow()


async def create_link_code(user_id: str):
    db = get_db()

    code = secrets.token_urlsafe(6)

    expires_at = _utcnow() + timedelta(seconds=LINK_EXPIRE_SECONDS)

    doc = {
        "user_id": ObjectId(user_id),
        "code": code,
        "expires_at": expires_at,
        "created_at": _utcnow(),
        "used": False,
    }

    await db.telegram_link_codes.insert_one(doc)

    return {
        "code": code,
        "expires_in_seconds": LINK_EXPIRE_SECONDS,
    }


async def consume_link_code(code: str):
    db = get_db()

    doc = await db.telegram_link_codes.find_one({"code": code, "used": False})

    if not doc:
        return None

    now = _utcnow()

    # Comparación segura (ambos naive)
    if doc.get("expires_at") and doc["expires_at"] < now:
        return None

    await db.telegram_link_codes.update_one(
        {"_id": doc["_id"]},
        {"$set": {"used": True}}
    )

    return doc
