from pydantic import BaseModel, Field

class LinkCodeOut(BaseModel):
    code: str
    expires_in_seconds: int
    deep_link: str

class LinkConfirmIn(BaseModel):
    code: str = Field(min_length=4, max_length=32)
    telegram_id: int
    telegram_username: str | None = None
