"""Memory Service - The Brain's memory subsystem.
Stores, retrieves, and manages memories of all types."""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, delete, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import MemoryEntry, MemoryType, MemoryImportance, Document, LearningEntry
from app.services.rag_service import EmbeddingService


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embeddings = EmbeddingService()

    async def store_memory(
        self,
        brain_id: uuid.UUID,
        memory_type: MemoryType,
        title: str,
        content: str,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        source: Optional[str] = None,
        source_id: Optional[str] = None,
        tags: Optional[dict] = None,
        context: Optional[dict] = None,
    ) -> MemoryEntry:
        """Store a new memory with embedding."""
        # Generate embedding
        embedding_text = f"{title}\n{content}"
        embedding = await self.embeddings.embed(embedding_text)

        entry = MemoryEntry(
            brain_id=brain_id,
            memory_type=memory_type,
            importance=importance,
            title=title,
            content=content,
            source=source,
            source_id=source_id,
            tags=tags or {},
            context=context or {},
            embedding=embedding,  # Will be stored via raw SQL for pgvector
        )
        self.db.add(entry)
        await self.db.flush()

        # Store embedding via raw SQL
        await self.db.execute(
            text("UPDATE memory_entries SET embedding = :embedding::vector WHERE id = :id"),
            {"embedding": embedding, "id": entry.id},
        )

        return entry

    async def search_memories(
        self,
        brain_id: uuid.UUID,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[MemoryEntry]:
        """Semantic search across memories."""
        query_embedding = await self.embeddings.embed(query)

        sql = """
            SELECT id, brain_id, memory_type, importance, title, content, summary,
                   source, source_id, tags, context, access_count, last_accessed_at,
                   created_at, updated_at,
                   1 - (CAST(embedding AS vector) <=> CAST(:query AS vector)) as similarity
            FROM memory_entries
            WHERE brain_id = :brain_id
            AND 1 - (CAST(embedding AS vector) <=> CAST(:query AS vector)) > :threshold
        """
        params = {"query": query_embedding, "brain_id": brain_id, "threshold": threshold}

        if memory_type:
            sql += " AND memory_type = :memory_type"
            params["memory_type"] = memory_type.value

        sql += " ORDER BY similarity DESC LIMIT :limit"
        params["limit"] = limit

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        memories = []
        for row in rows:
            entry = MemoryEntry(
                id=row[0], brain_id=row[1], memory_type=MemoryType(row[2]),
                importance=MemoryImportance(row[3]), title=row[4], content=row[5],
                summary=row[6], source=row[7], source_id=row[8], tags=row[9],
                context=row[10], access_count=row[11] or 0, last_accessed_at=row[12],
                created_at=row[13], updated_at=row[14],
            )
            memories.append(entry)

        return memories

    async def get_recent_memories(
        self, brain_id: uuid.UUID, memory_type: Optional[MemoryType] = None, limit: int = 20
    ) -> List[MemoryEntry]:
        """Get most recent memories."""
        query = select(MemoryEntry).where(MemoryEntry.brain_id == brain_id)
        if memory_type:
            query = query.where(MemoryEntry.memory_type == memory_type)
        query = query.order_by(desc(MemoryEntry.created_at)).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_working_context(self, brain_id: uuid.UUID) -> str:
        """Get the current working memory context as a formatted string."""
        memories = await self.get_recent_memories(brain_id, MemoryType.WORKING, limit=10)
        parts = []
        for m in memories:
            parts.append(f"[{m.importance.value.upper()}] {m.title}: {m.content[:500]}")
        return "\n\n".join(parts) if parts else "No active working memory."

    async def consolidate_memories(self, brain_id: uuid.UUID):
        """Consolidate similar or related memories (run periodically)."""
        # Find memories with similar embeddings and merge them
        sql = """
            SELECT m1.id as id1, m2.id as id2,
                   1 - (CAST(m1.embedding AS vector) <=> CAST(m2.embedding AS vector)) as similarity
            FROM memory_entries m1
            JOIN memory_entries m2 ON m1.id < m2.id
            WHERE m1.brain_id = :brain_id AND m2.brain_id = :brain_id
            AND 1 - (m1.embedding::vector <=> m2.embedding::vector) > 0.92
            LIMIT 50
        """
        result = await self.db.execute(text(sql), {"brain_id": brain_id})
        pairs = result.fetchall()

        for id1, id2, similarity in pairs:
            # Merge memory 2 into memory 1
            m2 = await self.db.get(MemoryEntry, id2)
            m1 = await self.db.get(MemoryEntry, id1)
            if m1 and m2:
                m1.access_count += m2.access_count
                await self.db.delete(m2)

    async def store_document(
        self,
        brain_id: uuid.UUID,
        title: str,
        content: str,
        content_type: str = "text",
        metadata: Optional[dict] = None,
    ) -> Document:
        """Store a document and index it for RAG."""
        doc = Document(
            brain_id=brain_id,
            title=title,
            content=content,
            content_type=content_type,
            extra_meta=metadata or {},
        )
        self.db.add(doc)
        await self.db.flush()

        # Chunk and embed
        chunks = self._chunk_text(content)
        for chunk in chunks:
            embedding = await self.embeddings.embed(chunk)
            await self.db.execute(
                text("""
                    INSERT INTO document_chunks (document_id, brain_id, content, embedding, chunk_index)
                    VALUES (:doc_id, :brain_id, :content, :embedding::vector, :idx)
                """),
                {
                    "doc_id": doc.id,
                    "brain_id": brain_id,
                    "content": chunk,
                    "embedding": embedding,
                    "idx": chunks.index(chunk),
                },
            )

        doc.is_indexed = True
        doc.chunk_count = len(chunks)
        return doc

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                # Try to break at a sentence boundary
                last_period = text.rfind(".", start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            chunks.append(text[start:end])
            start = end - overlap if end < len(text) else len(text)
        return chunks

    async def learn(
        self,
        brain_id: uuid.UUID,
        category: str,
        key: str,
        value: str,
        confidence: float = 0.5,
        evidence: Optional[dict] = None,
    ) -> LearningEntry:
        """Store a learning about user preferences."""
        # Check if learning exists
        query = select(LearningEntry).where(
            LearningEntry.brain_id == brain_id,
            LearningEntry.category == category,
            LearningEntry.key == key,
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update with recency-weighted confidence
            existing.value = value
            existing.confidence = max(existing.confidence, confidence)
            existing.evidence = evidence or {}
            return existing
        else:
            entry = LearningEntry(
                brain_id=brain_id,
                category=category,
                key=key,
                value=value,
                confidence=confidence,
                evidence=evidence or {},
            )
            self.db.add(entry)
            return entry
