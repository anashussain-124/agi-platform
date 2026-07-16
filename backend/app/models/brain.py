"""Brain model - each user owns a unique AI Brain."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, Float, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class BrainStatus(str, enum.Enum):
    CREATING = "creating"
    ACTIVE = "active"
    PAUSED = "paused"
    SLEEPING = "sleeping"


class Brain(Base):
    """Each user's unique AI Brain."""
    __tablename__ = "brains"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), default="My Brain")
    status: Mapped[BrainStatus] = mapped_column(SAEnum(BrainStatus), default=BrainStatus.CREATING)
    
    # Personality / preferences (learned over time)
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    coding_style: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    communication_style: Mapped[Optional[str]] = mapped_column(String(50), default="balanced")
    
    # Stats
    total_conversations: Mapped[int] = mapped_column(default=0)
    total_memories: Mapped[int] = mapped_column(default=0)
    total_tasks: Mapped[int] = mapped_column(default=0)
    uptime_hours: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Settings
    auto_learn: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_index: Mapped[bool] = mapped_column(Boolean, default=True)
    require_approval_deploy: Mapped[bool] = mapped_column(Boolean, default=True)
    require_approval_write: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class BrainModule(Base):
    """Modules/capabilities installed on a Brain."""
    __tablename__ = "brain_modules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    module_type: Mapped[str] = mapped_column(String(50), nullable=False)  # agent, tool, integration
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Conversation(Base):
    """A conversation/session with the Brain."""
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_meta: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    token_count: Mapped[int] = mapped_column(default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Message(Base):
    """A single message in a conversation."""
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_meta: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    token_count: Mapped[int] = mapped_column(default=0)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
