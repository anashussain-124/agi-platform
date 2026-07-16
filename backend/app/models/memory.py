"""Memory models - the Brain's memory subsystem."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, Float, Integer, Enum as SAEnum, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import enum

from app.core.database import Base


class MemoryType(str, enum.Enum):
    WORKING = "working"        # Current context / active task
    EPISODIC = "episodic"      # Past experiences / conversations
    SEMANTIC = "semantic"      # Facts, concepts, knowledge
    PROCEDURAL = "procedural"  # How-to, workflows, skills
    KNOWLEDGE = "knowledge"    # Documents, research, references
    PROJECT = "project"        # Project-specific context


class MemoryImportance(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryEntry(Base):
    """A single memory entry stored by the Brain."""
    __tablename__ = "memory_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    memory_type: Mapped[MemoryType] = mapped_column(SAEnum(MemoryType), nullable=False)
    importance: Mapped[MemoryImportance] = mapped_column(SAEnum(MemoryImportance), default=MemoryImportance.MEDIUM)
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Embedding (pgvector)
    embedding: Mapped[Optional[str]] = mapped_column(nullable=True)  # Will be cast to vector
    
    # Metadata
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # conversation, document, manual, etc.
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # ID of source
    tags: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    context: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # Situational context
    
    # Access control
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Consolidation
    access_count: Mapped[int] = mapped_column(default=0)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        # Index for vector similarity search
        # CREATE INDEX ON memory_entries USING ivfflat (embedding vector_cosine_ops);
    )


class Document(Base):
    """Documents stored in the Knowledge Engine."""
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), default="text")  # text, pdf, markdown, code
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Processing
    embedding: Mapped[Optional[str]] = mapped_column(nullable=True)
    chunk_count: Mapped[int] = mapped_column(default=1)
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    extra_meta: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class DocumentChunk(Base):
    """A chunk of a document for RAG retrieval."""
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    brain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[str]] = mapped_column(nullable=True)  # pgvector
    chunk_index: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class LearningEntry(Base):
    """What the Brain has learned about user preferences and patterns."""
    __tablename__ = "learning_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # coding_style, preference, workflow, etc.
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # What led to this learning
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint('brain_id', 'category', 'key', name='uix_brain_category_key'),
    )
