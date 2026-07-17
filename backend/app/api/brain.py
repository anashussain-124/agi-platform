"""Brain API endpoints — uses Repository pattern for dual-mode data access."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from types import SimpleNamespace

from app.core.database import get_async_session
from app.core.repository import BaseRepository
from app.core.compat_models import row_to_obj
from app.models.user import User
from app.models.brain import Brain, BrainModule, Conversation, Message
from app.api.auth import get_current_user
from app.services.ai_service import OpenRouterService
from app.services.memory_service import MemoryService
from app.core.logging import logger

router = APIRouter(prefix="/api/brain", tags=["brain"])
ai_service = OpenRouterService()


# ──────────────────────────────────────────────────────────
# Repository
# ──────────────────────────────────────────────────────────

class BrainRepository(BaseRepository):
    """Data access for brains, conversations, and messages."""

    async def get_brain_for_user(self, user_id: str) -> Optional[dict | Brain]:
        if self.use_supabase:
            rows = await self.supabase.get("brains", filters={"user_id": user_id}, limit=1)
            return rows[0] if rows else None
        result = await self.db.execute(select(Brain).where(Brain.user_id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()

    async def update_brain(self, user_id: str, updates: dict) -> Optional[dict | Brain]:
        if self.use_supabase:
            await self.supabase.update("brains", {"user_id": user_id}, updates)
            rows = await self.supabase.get("brains", filters={"user_id": user_id}, limit=1)
            return rows[0] if rows else None
        result = await self.db.execute(select(Brain).where(Brain.user_id == uuid.UUID(user_id)))
        brain = result.scalar_one_or_none()
        if brain:
            for key, value in updates.items():
                if hasattr(brain, key):
                    setattr(brain, key, value)
            await self.db.commit()
        return brain

    async def create_conversation(self, brain_id: str, title: str) -> dict:
        if self.use_supabase:
            return await self.supabase.create("conversations", {
                "brain_id": brain_id,
                "title": title,
            })
        conv = Conversation(brain_id=uuid.UUID(brain_id), title=title)
        self.db.add(conv)
        await self.db.flush()
        return {"id": str(conv.id), "brain_id": brain_id, "title": title}

    async def create_message(self, conversation_id: str, role: str, content: str) -> dict:
        if self.use_supabase:
            return await self.supabase.create("messages", {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
            })
        msg = Message(conversation_id=uuid.UUID(conversation_id), role=role, content=content)
        self.db.add(msg)
        await self.db.flush()
        return {"id": str(msg.id), "role": role, "content": content}

    async def get_messages(self, conversation_id: str, limit: int = 50) -> list[dict]:
        if self.use_supabase:
            return await self.supabase.get(
                "messages",
                filters={"conversation_id": conversation_id},
                order="created_at.asc",
                limit=limit,
            )
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == uuid.UUID(conversation_id))
            .order_by(Message.created_at)
            .limit(limit)
        )
        return [
            {"id": str(m.id), "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in result.scalars().all()
        ]

    async def get_conversations(self, brain_id: str, limit: int = 20) -> list[dict]:
        if self.use_supabase:
            rows = await self.supabase.get(
                "conversations",
                filters={"brain_id": brain_id, "is_archived": False},
                order="updated_at.desc",
                limit=limit,
            )
            return [
                {"id": r["id"], "title": r.get("title", "New Conversation"),
                 "summary": r.get("summary"), "updated_at": r.get("updated_at", "")}
                for r in rows
            ]
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.brain_id == uuid.UUID(brain_id))
            .where(Conversation.is_archived == False)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return [
            {"id": str(c.id), "title": c.title, "summary": c.summary, "updated_at": c.updated_at.isoformat()}
            for c in result.scalars().all()
        ]


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def _brain_to_dict(brain_data) -> dict:
    """Normalize brain data (dict or ORM object) to a consistent response dict."""
    if isinstance(brain_data, dict):
        return {
            "id": brain_data.get("id", ""),
            "name": brain_data.get("name", ""),
            "status": brain_data.get("status", "active"),
            "stats": {
                "total_conversations": brain_data.get("total_conversations", 0),
                "total_memories": brain_data.get("total_memories", 0),
                "total_tasks": brain_data.get("total_tasks", 0),
                "uptime_hours": float(brain_data.get("uptime_hours", 0)),
            },
            "preferences": brain_data.get("preferences", {}) or {},
            "settings": {
                "auto_learn": brain_data.get("auto_learn", True),
                "auto_index": brain_data.get("auto_index", True),
                "require_approval_deploy": brain_data.get("require_approval_deploy", True),
                "require_approval_write": brain_data.get("require_approval_write", False),
            },
            "last_active_at": brain_data.get("last_active_at"),
            "created_at": brain_data.get("created_at", ""),
        }

    # SQLAlchemy ORM object
    return {
        "id": str(brain_data.id),
        "name": brain_data.name,
        "status": brain_data.status.value if hasattr(brain_data.status, "value") else brain_data.status,
        "stats": {
            "total_conversations": brain_data.total_conversations,
            "total_memories": brain_data.total_memories,
            "total_tasks": brain_data.total_tasks,
            "uptime_hours": brain_data.uptime_hours,
        },
        "preferences": brain_data.preferences or {},
        "settings": {
            "auto_learn": brain_data.auto_learn,
            "auto_index": brain_data.auto_index,
            "require_approval_deploy": brain_data.require_approval_deploy,
            "require_approval_write": brain_data.require_approval_write,
        },
        "last_active_at": brain_data.last_active_at.isoformat() if brain_data.last_active_at else None,
        "created_at": brain_data.created_at.isoformat(),
    }


# ──────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────

@router.get("/")
async def get_brain(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get the current user's Brain."""
    repo = BrainRepository(db)
    brain = await repo.get_brain_for_user(str(user.id))
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found. Create one first.")
    return _brain_to_dict(brain)


@router.patch("/")
async def update_brain(
    name: Optional[str] = None,
    preferences: Optional[dict] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Update Brain settings."""
    updates = {}
    if name is not None:
        updates["name"] = name
    if preferences is not None:
        updates["preferences"] = preferences

    repo = BrainRepository(db)
    brain = await repo.update_brain(str(user.id), updates)
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")
    return _brain_to_dict(brain)


# ──────────────────────────────────────────────────────────
# Chat
# ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    brain_status: Optional[str] = None


@router.post("/chat")
async def chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Send a message to the Brain and get a response."""
    try:
        repo = BrainRepository(db)
        brain = await repo.get_brain_for_user(str(user.id))
        if not brain:
            raise HTTPException(status_code=404, detail="Brain not found")

        brain_id = brain["id"] if isinstance(brain, dict) else str(brain.id)
        brain_status = brain.get("status", "active") if isinstance(brain, dict) else brain.status.value

        # Conversation lookup or create
        conv_id = req.conversation_id
        if not conv_id:
            conv = await repo.create_conversation(brain_id, req.message[:50])
            conv_id = conv["id"]

        # Save user message
        await repo.create_message(conv_id, "user", req.message)

        # Build message history
        msgs = await repo.get_messages(conv_id, limit=50)
        history = [{"role": m["role"], "content": m["content"]} for m in msgs]

        # Get AI response
        try:
            ai_result = await ai_service.chat(history)
            ai_text = ai_result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("AI service error: %s", str(e)[:200])
            ai_text = (
                f"I encountered an issue connecting to the AI service: {e}\n\n"
                "Make sure OPENROUTER_API_KEY is set in your .env file."
            )

        # Save AI response
        await repo.create_message(conv_id, "assistant", ai_text)

        return ChatResponse(
            conversation_id=conv_id,
            response=ai_text,
            brain_status=brain_status,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat error: %s", str(e)[:300])
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")


@router.get("/conversations")
async def get_conversations(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get recent conversations."""
    repo = BrainRepository(db)
    brain = await repo.get_brain_for_user(str(user.id))
    if not brain:
        return []
    brain_id = brain["id"] if isinstance(brain, dict) else str(brain.id)
    return await repo.get_conversations(brain_id, limit)


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get messages for a conversation."""
    repo = BrainRepository(db)
    messages = await repo.get_messages(conversation_id, limit=200)
    return [
        {"id": m.get("id", ""), "role": m["role"], "content": m["content"], "created_at": m.get("created_at", "")}
        for m in messages
    ]
