from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

    # Código de referido (opcional)
    referral_code: str | None = Field(None, min_length=4, max_length=32)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
