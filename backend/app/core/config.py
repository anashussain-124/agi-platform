"""Centralized configuration for Brain AGI Platform."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "BrainAGI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./brain_agi.db"
    DATABASE_URL_SYNC: str = "sqlite:///./brain_agi.db"

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

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Encryption
    ENCRYPTION_KEY: Optional[str] = None  # Fernet key for secret encryption

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # pgvector
    EMBEDDING_DIMENSION: int = 1536  # OpenAI ada-002

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
