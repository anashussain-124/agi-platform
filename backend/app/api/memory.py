"""Memory API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.database import get_async_session
from app.models.user import User
from app.models.brain import Brain
from app.models.memory import MemoryEntry, MemoryType, MemoryImportance
from app.api.auth import get_current_user
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api/memory", tags=["memory"])


class StoreMemoryRequest(BaseModel):
    memory_type: MemoryType
    title: str
    content: str
    importance: MemoryImportance = MemoryImportance.MEDIUM
    source: Optional[str] = None
    tags: Optional[dict] = None


@router.get("/")
async def list_memories(
    memory_type: Optional[str] = None,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List memories."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    query = select(MemoryEntry).where(MemoryEntry.brain_id == brain.id)
    if memory_type:
        query = query.where(MemoryEntry.memory_type == MemoryType(memory_type))
    query = query.order_by(desc(MemoryEntry.created_at)).limit(limit)

    result = await db.execute(query)
    memories = result.scalars().all()

    return [
        {
            "id": str(m.id),
            "memory_type": m.memory_type.value,
            "importance": m.importance.value,
            "title": m.title,
            "summary": m.summary or m.content[:200],
            "source": m.source,
            "tags": m.tags,
            "access_count": m.access_count,
            "created_at": m.created_at.isoformat(),
        }
        for m in memories
    ]


@router.post("/")
async def store_memory(
    req: StoreMemoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Store a new memory."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    memory_service = MemoryService(db)
    entry = await memory_service.store_memory(
        brain_id=brain.id,
        memory_type=req.memory_type,
        title=req.title,
        content=req.content,
        importance=req.importance,
        source=req.source,
        tags=req.tags,
    )
    brain.total_memories += 1

    return {
        "id": str(entry.id),
        "title": entry.title,
        "memory_type": entry.memory_type.value,
        "created_at": entry.created_at.isoformat(),
    }


@router.get("/search")
async def search_memories(
    query: str = Query(..., min_length=1),
    memory_type: Optional[str] = None,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Semantic search across memories."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    memory_service = MemoryService(db)
    mem_type = MemoryType(memory_type) if memory_type else None
    memories = await memory_service.search_memories(
        brain.id, query, memory_type=mem_type, limit=limit
    )

    return [
        {
            "id": str(m.id),
            "title": m.title,
            "content": m.content[:500],
            "memory_type": m.memory_type.value,
            "importance": m.importance.value,
            "source": m.source,
        }
        for m in memories
    ]


@router.get("/working")
async def get_working_context(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get current working memory context."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    memory_service = MemoryService(db)
    context = await memory_service.get_working_context(brain.id)

    return {"context": context}
