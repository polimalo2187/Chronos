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
    telegram_link_secret: str = Field("", alias="TELEGRAM_LINK_SECRET")

    # Admin bootstrap (opcional)
    admin_email: str | None = Field(None, alias="ADMIN_EMAIL")
    admin_password: str | None = Field(None, alias="ADMIN_PASSWORD")

    # ===== PLANES =====
    trial_days: int = Field(7, alias="TRIAL_DAYS")
    paid_plan_days: int = Field(30, alias="PAID_PLAN_DAYS")

    # ===== BLOQUEO =====
    # usuario pasa a inactive al expirar plan
    # ban permanente o temporal se manejará en DB

    # ===== COMUNICACIÓN INTERNA (SCANNER → API) =====
    internal_api_key: str = Field(..., alias="INTERNAL_API_KEY")

    # ===== WHATSAPP (RENOVACIONES) =====
    whatsapp_contact: str = Field("", alias="WHATSAPP_CONTACT")

settings = Settings()
