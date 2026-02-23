from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, OperationFailure
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
    """
    Crea índices necesarios.

    FIX IMPORTANTE:
    - referral_code debe ser UNIQUE, pero tu DB ya tiene usuarios viejos con referral_code = null.
      MongoDB considera null como un valor y rompe el índice unique.
    - Solución: antes de crear el índice, quitamos referral_code cuando sea null
      y creamos un índice UNIQUE parcial (solo aplica cuando referral_code es string).
    """
    db = get_db()

    await db.users.create_index("email", unique=True)
    await db.users.create_index("telegram_id", unique=False)

    # Telegram link codes
    await db.telegram_link_codes.create_index("code", unique=True)
    await db.telegram_link_codes.create_index("expires_at", expireAfterSeconds=0)

    # ----
    # REFERRALS
    # ----
    # 1) Limpia datos legacy: referral_code = null (causa DuplicateKeyError en índice unique)
    try:
        await db.users.update_many({"referral_code": None}, {"$unset": {"referral_code": ""}})
    except Exception:
        # no tumbar startup por esto
        pass

    # 2) Si existe un índice viejo mal creado, lo borramos
    try:
        async for ix in db.users.list_indexes():
            if ix.get("name") == "referral_code_1":
                try:
                    await db.users.drop_index("referral_code_1")
                except Exception:
                    pass
                break
    except Exception:
        pass

    # 3) Crear índice UNIQUE parcial: solo cuando referral_code sea string
    #    (así permite usuarios legacy sin referral_code)
    try:
        await db.users.create_index(
            "referral_code",
            unique=True,
            name="referral_code_1",
            partialFilterExpression={"referral_code": {"$type": "string"}},
        )
    except DuplicateKeyError:
        # Si todavía existe duplicado real (dos strings iguales), no tumbamos el backend
        # pero OJO: debes corregir esos duplicados manualmente.
        pass
    except OperationFailure:
        pass
