from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    app_name: str = "Homey.ai"
    app_env: Literal["development", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # Transport (mock or telegram)
    transport: Literal["mock", "telegram"] = "mock"

    # Telegram Bot API
    telegram_bot_token: str | None = None
    telegram_webhook_url: str | None = None  # Optional, for webhook mode
    telegram_webhook_secret: str | None = None  # Optional, for webhook validation

    # Gemini API
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    # Database
    database_url: str = "postgresql://homey:homey@localhost:5432/homeyai"
    redis_url: str = "redis://localhost:6379"

    # Media Storage (S3/R2 compatible)
    storage_type: Literal["local", "s3"] = "local"
    s3_bucket: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
