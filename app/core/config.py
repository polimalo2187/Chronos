from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Mongo
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db: str = Field("chronos", alias="MONGODB_DB")

    # Auth/JWT
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(43200, alias="JWT_EXPIRE_MINUTES")  # 30 días

    # Telegram linking
    telegram_bot_username: str = Field("CRNAssistant_bot", alias="TELEGRAM_BOT_USERNAME")
    telegram_link_secret: str = Field("", alias="TELEGRAM_LINK_SECRET")  # required for /telegram/link

    # Optional admin bootstrap
    admin_email: str | None = Field(None, alias="ADMIN_EMAIL")
    admin_password: str | None = Field(None, alias="ADMIN_PASSWORD")

settings = Settings()
