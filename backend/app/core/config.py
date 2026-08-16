"""
LexIntellectus ERP - Application Settings
Centralized configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "LexIntellectus"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # PostgreSQL
    POSTGRES_USER: str = "lexintellectus"
    POSTGRES_PASSWORD: str = "lexintellectus_dev_2026"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "lexintellectus"
    DATABASE_URL: str = ""

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "lexintellectus_redis_2026"
    REDIS_URL: str = ""

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "lexintellectus"
    MINIO_ROOT_PASSWORD: str = "lexintellectus_minio_2026"
    MINIO_BUCKET: str = "lexintellectus-documents"
    MINIO_USE_SSL: bool = False

    # JWT
    JWT_SECRET_KEY: str = "dev_secret_key_change_in_production_2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # SMTP / Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "notifications@lexintellectus.com"
    SMTP_PASSWORD: str = "change_me"
    EMAILS_ENABLED: bool = False

    # AI / Gemini
    GOOGLE_API_KEY: str = ""
    AI_STRATEGY: str = "local_expert"  # cloud_general or local_expert
    AI_PROVIDER: str = "google"        # google or ollama (for local offline LLMs like DeepSeek-R1)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "deepseek-r1:8b"

    # Stripe & PayPal Payments
    STRIPE_SECRET_KEY: str = "mock_stripe_secret_key_for_testing_only"
    STRIPE_WEBHOOK_SECRET: str = "whsec_placeholder"
    PAYPAL_CLIENT_ID: str = "placeholder_paypal_client_id"
    PAYPAL_CLIENT_SECRET: str = "placeholder_paypal_client_secret"
    PAYPAL_MODE: str = "sandbox"  # sandbox or live

    # Database Encryption (Fernet symmetric key)
    DB_ENCRYPTION_KEY: str = "T1Boc2QzSDRlNTZkNzhqOWowMTIzNDU2NzhqOWowMTI="



    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL for Alembic migrations."""
        return self.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    @property
    def redis_url_computed(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Try loading from .env files in order of preference
import pathlib

_base_dir = pathlib.Path(__file__).resolve().parent.parent.parent
_env_path = _base_dir / ".env"
_env_local_path = _base_dir / ".env.local"

if _env_path.exists():
    # Load .env first, then .env.local overrides for sensitive keys
    settings = Settings(
        _env_file=(str(_env_path), str(_env_local_path)) if _env_local_path.exists() else str(_env_path)
    )
else:
    # In Docker, env vars come from the container environment
    settings = Settings()

