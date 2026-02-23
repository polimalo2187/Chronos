import random
import string
from datetime import datetime
from app.db.connection import get_db


def _generate_code():
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"CHRONOS-{rand}"


async def get_or_create_referral_code(user: dict):
    db = get_db()
    users = db.users

    # si ya tiene
    if user.get("referral", {}).get("code"):
        return user["referral"]["code"]

    # generar único
    while True:
        code = _generate_code()
        exists = await users.find_one({"referral.code": code})
        if not exists:
            break

    await users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "referral.code": code,
                "referral.created_at": datetime.utcnow(),
                "referral.plus": 0,
                "referral.premium": 0,
            }
        }
    )

    return code
