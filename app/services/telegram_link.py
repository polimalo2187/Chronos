from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.db.mongo import get_db


def _ensure_aware_utc(dt: datetime) -> datetime:
    """
    Normaliza datetimes para evitar el error:
    'can't compare offset-naive and offset-aware datetimes'

    - Si viene naive (sin tzinfo), asumimos que es UTC (típico de Mongo/Motor).
    - Si viene aware, lo convertimos a UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def create_link_code(
    user_id: str,
    expires_in_seconds: int = 600,
) -> Dict[str, Any]:
    """
    Crea un código temporal para vincular Telegram.
    """
    db = get_db()
    code = _random_code(8)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=expires_in_seconds)

    doc = {
        "code": code,
        "user_id": user_id,
        "created_at": now,
        "expires_at": expires_at,
    }
    await db.telegram_link_codes.insert_one(doc)
    return doc


async def consume_link_code(code: str) -> Optional[Dict[str, Any]]:
    """
    Consume un código (solo se puede usar 1 vez).
    Si expiró o no existe, retorna None.
    """
    db = get_db()
    doc = await db.telegram_link_codes.find_one({"code": code})
    if not doc:
        return None

    expires_at = doc.get("expires_at")
    if expires_at:
        expires_at = _ensure_aware_utc(expires_at)
        now = datetime.now(timezone.utc)

        if expires_at < now:
            # Expirado: lo eliminamos
            await db.telegram_link_codes.delete_one({"_id": doc["_id"]})
            return None

    # Consumir (una sola vez)
    await db.telegram_link_codes.delete_one({"_id": doc["_id"]})
    return doc


def _random_code(length: int = 8) -> str:
    """
    Código corto para deep-link /start link_<code>
    """
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
