from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _bcrypt_safe_password(password: str) -> str:
    """
    bcrypt solo usa los primeros 72 bytes.
    Para evitar crash, si pasa de 72 bytes, lanzamos ValueError controlado.
    """
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password exceeds bcrypt 72-byte limit")
    return password

def hash_password(password: str) -> str:
    password = _bcrypt_safe_password(password)
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    password = _bcrypt_safe_password(password)
    return pwd_context.verify(password, password_hash)

def create_access_token(sub: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": sub, "iat": int(now.timestamp()), "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
