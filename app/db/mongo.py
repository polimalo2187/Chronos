from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client

def get_db() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        _db = get_client()[settings.mongodb_db]
    return _db

async def ensure_indexes() -> None:
    db = get_db()
    await db.users.create_index("email", unique=True)
    await db.users.create_index("telegram_id", unique=False)
    await db.telegram_link_codes.create_index("code", unique=True)
    # TTL index: auto-delete link codes when expires_at reached
    await db.telegram_link_codes.create_index("expires_at", expireAfterSeconds=0)
