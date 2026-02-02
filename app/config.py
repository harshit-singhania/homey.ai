from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    app_name: str = "Homey.ai"
    app_env: Literal["development", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    transport: Literal["mock", "whatsapp"] = "mock"

    whatsapp_phone_number_id: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_verify_token: str | None = None
    whatsapp_app_secret: str | None = None

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    database_url: str = "postgresql://homey:homey@localhost:5432/homeyai"
    redis_url: str = "redis://localhost:6379"

    storage_type: Literal["local", "s3"] = "local"
    s3_bucket: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
