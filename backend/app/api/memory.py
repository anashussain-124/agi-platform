"""Memory API endpoints — uses Repository pattern for dual-mode data access."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.database import get_async_session
from app.core.repository import BaseRepository
from app.models.user import User
from app.models.brain import Brain
from app.models.memory import MemoryEntry, MemoryType, MemoryImportance
from app.api.auth import get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/api/memory", tags=["memory"])


# ──────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────

class StoreMemoryRequest(BaseModel):
    memory_type: str
    title: str
    content: str
    importance: str = "medium"
    source: Optional[str] = None
    tags: Optional[dict] = None


# ──────────────────────────────────────────────────────────
# Repository
# ──────────────────────────────────────────────────────────

class MemoryRepository(BaseRepository):
    """Data access for memory entries."""

    async def get_brain_id(self, user_id: str) -> Optional[str]:
        if self.use_supabase:
            rows = await self.supabase.get("brains", filters={"user_id": user_id}, limit=1)
            return rows[0]["id"] if rows else None
        result = await self.db.execute(select(Brain).where(Brain.user_id == uuid.UUID(user_id)))
        brain = result.scalar_one_or_none()
        return str(brain.id) if brain else None

    async def list_memories(self, brain_id: str, memory_type: Optional[str] = None,
                            limit: int = 20) -> list[dict]:
        if self.use_supabase:
            filters = {"brain_id": brain_id}
            if memory_type:
                filters["memory_type"] = memory_type
            rows = await self.supabase.get("memory_entries", filters=filters,
                                           order="created_at.desc", limit=limit)
            return [_memory_to_dict(r) for r in rows]

        query = select(MemoryEntry).where(MemoryEntry.brain_id == uuid.UUID(brain_id))
        if memory_type:
            query = query.where(MemoryEntry.memory_type == MemoryType(memory_type))
        query = query.order_by(desc(MemoryEntry.created_at)).limit(limit)
        result = await self.db.execute(query)
        return [_memory_to_dict(m) for m in result.scalars().all()]

    async def store_memory(self, brain_id: str, memory_type: str, title: str,
                           content: str, importance: str = "medium",
                           source: Optional[str] = None, tags: Optional[dict] = None) -> dict:
        if self.use_supabase:
            entry = await self.supabase.create("memory_entries", {
                "brain_id": brain_id, "memory_type": memory_type,
                "importance": importance, "title": title,
                "content": content, "source": source, "tags": tags or {},
            })
            return {"id": entry["id"], "title": entry.get("title", ""),
                    "memory_type": entry.get("memory_type", ""), "created_at": entry.get("created_at", "")}

        entry = MemoryEntry(
            brain_id=uuid.UUID(brain_id),
            memory_type=MemoryType(memory_type),
            importance=MemoryImportance(importance),
            title=title, content=content, source=source, tags=tags or {},
        )
        self.db.add(entry)
        await self.db.flush()
        return {"id": str(entry.id), "title": entry.title,
                "memory_type": entry.memory_type.value, "created_at": entry.created_at.isoformat()}

    async def search_memories(self, brain_id: str, query: str,
                              memory_type: Optional[str] = None, limit: int = 10) -> list[dict]:
        """Text-based search across memories."""
        if self.use_supabase:
            # Server-side filtering isn't available via basic PostgREST for ILIKE,
            # so we fetch and filter client-side (limited to 200 rows)
            rows = await self.supabase.get("memory_entries", filters={"brain_id": brain_id}, limit=200)
            q = query.lower()
            matched = [
                r for r in rows
                if q in r.get("title", "").lower() or q in r.get("content", "").lower()
            ]
            if memory_type:
                matched = [r for r in matched if r.get("memory_type") == memory_type]
            return [_search_result_to_dict(r) for r in matched[:limit]]

        # SQLAlchemy — use ILIKE for server-side text search
        from sqlalchemy import or_
        stmt = select(MemoryEntry).where(MemoryEntry.brain_id == uuid.UUID(brain_id))
        stmt = stmt.where(
            or_(
                MemoryEntry.title.ilike(f"%{query}%"),
                MemoryEntry.content.ilike(f"%{query}%"),
            )
        )
        if memory_type:
            stmt = stmt.where(MemoryEntry.memory_type == MemoryType(memory_type))
        stmt = stmt.order_by(desc(MemoryEntry.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return [_search_result_to_dict(m) for m in result.scalars().all()]

    async def get_working_context(self, brain_id: str, limit: int = 5) -> list[dict]:
        if self.use_supabase:
            rows = await self.supabase.get(
                "memory_entries",
                filters={"brain_id": brain_id, "memory_type": "working"},
                order="created_at.desc", limit=limit,
            )
            return [{"title": w.get("title", ""), "content": w.get("content", "")} for w in rows]

        stmt = (
            select(MemoryEntry)
            .where(MemoryEntry.brain_id == uuid.UUID(brain_id))
            .where(MemoryEntry.memory_type == MemoryType.WORKING)
            .order_by(MemoryEntry.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [{"title": m.title, "content": m.content} for m in result.scalars().all()]


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def _memory_to_dict(m) -> dict:
    """Normalize memory entry to response dict."""
    if isinstance(m, dict):
        return {
            "id": m["id"], "memory_type": m.get("memory_type", ""),
            "importance": m.get("importance", "medium"), "title": m.get("title", ""),
            "summary": m.get("summary") or m.get("content", "")[:200],
            "source": m.get("source"), "tags": m.get("tags"),
            "access_count": m.get("access_count", 0), "created_at": m.get("created_at", ""),
        }
    return {
        "id": str(m.id), "memory_type": m.memory_type.value,
        "importance": m.importance.value, "title": m.title,
        "summary": m.summary or m.content[:200],
        "source": m.source, "tags": m.tags,
        "access_count": m.access_count, "created_at": m.created_at.isoformat(),
    }


def _search_result_to_dict(m) -> dict:
    """Normalize search result to response dict."""
    if isinstance(m, dict):
        return {
            "id": m["id"], "title": m.get("title", ""),
            "content": m.get("content", "")[:500], "memory_type": m.get("memory_type", ""),
            "importance": m.get("importance", "medium"), "source": m.get("source"),
        }
    return {
        "id": str(m.id), "title": m.title,
        "content": m.content[:500], "memory_type": m.memory_type.value,
        "importance": m.importance.value, "source": m.source,
    }


# ──────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────

@router.get("/")
async def list_memories(
    memory_type: Optional[str] = None,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List memories."""
    try:
        repo = MemoryRepository(db)
        brain_id = await repo.get_brain_id(str(user.id))
        if not brain_id:
            raise HTTPException(status_code=404, detail="Brain not found")
        return await repo.list_memories(brain_id, memory_type, limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")


@router.post("/")
async def store_memory(
    req: StoreMemoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Store a new memory."""
    try:
        repo = MemoryRepository(db)
        brain_id = await repo.get_brain_id(str(user.id))
        if not brain_id:
            raise HTTPException(status_code=404, detail="Brain not found")
        return await repo.store_memory(
            brain_id, req.memory_type, req.title, req.content,
            req.importance, req.source, req.tags,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")


@router.get("/search")
async def search_memories(
    query: str = Query(..., min_length=1),
    memory_type: Optional[str] = None,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Text-based search across memories."""
    try:
        repo = MemoryRepository(db)
        brain_id = await repo.get_brain_id(str(user.id))
        if not brain_id:
            raise HTTPException(status_code=404, detail="Brain not found")
        return await repo.search_memories(brain_id, query, memory_type, limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")


@router.get("/working")
async def get_working_context(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get current working memory context."""
    try:
        repo = MemoryRepository(db)
        brain_id = await repo.get_brain_id(str(user.id))
        if not brain_id:
            raise HTTPException(status_code=404, detail="Brain not found")
        context = await repo.get_working_context(brain_id)
        return {"context": context}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")
