from fastapi import APIRouter, HTTPException
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.services.users import create_user, authenticate
from app.core.security import create_access_token
from pymongo.errors import DuplicateKeyError

router = APIRouter()

@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn):
    try:
        user_id = await create_user(payload.email, payload.password, is_admin=False)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")
    token = create_access_token(str(user_id))
    return {"access_token": token}

@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn):
    user = await authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user["_id"]))
    return {"access_token": token}
