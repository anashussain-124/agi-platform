"""Integration models - GitHub, Vercel, Supabase, etc."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class IntegrationProvider(str, enum.Enum):
    GITHUB = "github"
    VERCEL = "vercel"
    SUPABASE = "supabase"
    RENDER = "render"
    OPENROUTER = "openrouter"
    GUMROAD = "gumroad"
    INSTAGRAM = "instagram"
    EMAIL = "email"
    CUSTOM = "custom"


class Integration(Base):
    """Third-party service integration."""
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    
    provider: Mapped[IntegrationProvider] = mapped_column(SAEnum(IntegrationProvider), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Encrypted credentials
    encrypted_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scopes: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Config
    config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # Provider-specific config
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AuditLog(Base):
    """Audit trail for all actions."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "task.created", "memory.read"
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "task", "memory", "integration"
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    details: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
