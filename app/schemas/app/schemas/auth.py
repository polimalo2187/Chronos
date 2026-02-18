from pydantic import BaseModel, EmailStr, Field, field_validator

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password demasiado larga (límite bcrypt: 72 bytes)")
        return v

class LoginIn(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password demasiado larga (límite bcrypt: 72 bytes)")
        return v

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
