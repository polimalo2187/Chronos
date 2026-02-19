from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient | None = None


def connect_to_mongo():
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.MONGODB_URI)


def get_db():
    if client is None:
        connect_to_mongo()
    return client[settings.MONGODB_DB]
