"""Centralized configuration for Brain AGI Platform."""
import os
import warnings
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional, List


def _default_db_url() -> str:
    """Return a SQLite URL that works on the current platform.
    - Locally: ./brain_agi.db
    - Vercel: /tmp/brain_agi.db (read-only / root)
    """
    if os.environ.get("VERCEL_ENV") or not os.access(".", os.W_OK):
        return "sqlite+aiosqlite:////tmp/brain_agi.db"
    return "sqlite+aiosqlite:///./brain_agi.db"


class Settings(BaseSettings):
    # App
    APP_NAME: str = "BrainAGI"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = _default_db_url()
    DATABASE_URL_SYNC: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_REASONING_MODEL: str = "anthropic/claude-sonnet-4"
    OPENROUTER_AGENT_MODEL: str = "openai/gpt-4o"

    # Auth
    JWT_SECRET: str = "change-me-in-production-jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 72
    MFA_ENABLED: bool = False

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # Encryption
    ENCRYPTION_KEY: Optional[str] = None  # Fernet key for secret encryption

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # pgvector
    EMBEDDING_DIMENSION: int = 1536  # OpenAI ada-002

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    @model_validator(mode="after")
    def _warn_default_secrets(self) -> "Settings":
        """Warn if default secrets are being used in non-debug mode."""
        if not self.DEBUG:
            if self.SECRET_KEY == "change-me-in-production":
                warnings.warn(
                    "⚠️  SECRET_KEY is set to the default value! "
                    "Set a strong random string in production.",
                    stacklevel=2,
                )
            if self.JWT_SECRET == "change-me-in-production-jwt":
                warnings.warn(
                    "⚠️  JWT_SECRET is set to the default value! "
                    "Set a strong random string in production.",
                    stacklevel=2,
                )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
