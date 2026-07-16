"""Brain API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
import json

from app.core.database import get_async_session
from app.models.user import User
from app.models.brain import Brain, BrainModule, Conversation, Message
from app.api.auth import get_current_user
from app.services.ai_service import OpenRouterService
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api/brain", tags=["brain"])

# Shared AI service instance
ai_service = OpenRouterService()


@router.get("/")
async def get_brain(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get the current user's Brain."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()

    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found. Create one first.")

    return {
        "id": str(brain.id),
        "name": brain.name,
        "status": brain.status.value,
        "stats": {
            "total_conversations": brain.total_conversations,
            "total_memories": brain.total_memories,
            "total_tasks": brain.total_tasks,
            "uptime_hours": brain.uptime_hours,
        },
        "preferences": brain.preferences or {},
        "settings": {
            "auto_learn": brain.auto_learn,
            "auto_index": brain.auto_index,
            "require_approval_deploy": brain.require_approval_deploy,
            "require_approval_write": brain.require_approval_write,
        },
        "last_active_at": brain.last_active_at.isoformat() if brain.last_active_at else None,
        "created_at": brain.created_at.isoformat(),
    }


@router.patch("/")
async def update_brain(
    name: Optional[str] = None,
    preferences: Optional[dict] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Update Brain settings."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()

    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    if name:
        brain.name = name
    if preferences:
        if brain.preferences:
            brain.preferences.update(preferences)
        else:
            brain.preferences = preferences

    return {"status": "updated", "name": brain.name}


@router.get("/modules")
async def get_modules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get installed Brain modules."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404)

    result = await db.execute(
        select(BrainModule).where(BrainModule.brain_id == brain.id)
    )
    modules = result.scalars().all()

    return [
        {
            "id": str(m.id),
            "name": m.name,
            "module_type": m.module_type,
            "enabled": m.enabled,
            "config": m.config,
        }
        for m in modules
    ]


@router.get("/conversations")
async def list_conversations(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List recent conversations."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404)

    result = await db.execute(
        select(Conversation)
        .where(Conversation.brain_id == brain.id, Conversation.is_archived == False)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "title": c.title,
            "summary": c.summary,
            "token_count": c.token_count,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in conversations
    ]


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


async def _build_chat_context(
    brain: Brain,
    conversation: Conversation,
    user_message: str,
    db: AsyncSession,
) -> list[dict]:
    """Build the full message context for the AI, including memory retrieval."""
    messages = []

    # 1. System prompt with brain personality
    system_prompt = (
        f"You are {brain.name}, a personal AI brain. "
        "You help your user reason, remember, plan, and build. "
        "You have access to persistent memory, specialized agents, and can learn preferences over time. "
        "Be helpful, precise, and proactive. If the user asks you to remember something, confirm it. "
        "Keep responses concise unless asked to elaborate."
    )

    # Add communication style preference
    if brain.communication_style:
        style_map = {
            "concise": "Keep responses very brief and to the point.",
            "balanced": "Provide helpful detail without being verbose.",
            "detailed": "Provide thorough, detailed responses.",
        }
        system_prompt += f"\n\nCommunication style: {style_map.get(brain.communication_style, '')}"

    messages.append({"role": "system", "content": system_prompt})

    # 2. Retrieve relevant memories for context
    try:
        memory_service = MemoryService(db)
        working_ctx = await memory_service.get_working_context(brain.id)
        if working_ctx and working_ctx != "No active working memory.":
            messages.append({
                "role": "system",
                "content": f"Current working memory:\n{working_ctx}",
            })

        # Semantic search for relevant memories
        relevant = await memory_service.search_memories(
            brain.id, user_message, limit=3, threshold=0.5
        )
        if relevant:
            memory_ctx = "\n".join(
                f"- [{m.memory_type.value}] {m.title}: {m.content[:300]}"
                for m in relevant
            )
            messages.append({
                "role": "system",
                "content": f"Relevant memories:\n{memory_ctx}",
            })
    except Exception:
        # Memory retrieval is best-effort; don't fail the chat
        pass

    # 3. Load recent conversation history
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .limit(20)
    )
    history = result.scalars().all()
    for msg in history:
        if msg.role in ("user", "assistant"):
            messages.append({"role": msg.role, "content": msg.content})

    # 4. Add the new user message
    messages.append({"role": "user", "content": user_message})

    return messages


@router.post("/chat")
async def chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Send a message to your Brain."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    # Get or create conversation
    conv_id = uuid.UUID(req.conversation_id) if req.conversation_id else uuid.uuid4()
    if not req.conversation_id:
        conv = Conversation(
            id=conv_id,
            brain_id=brain.id,
            title=req.message[:50] + ("..." if len(req.message) > 50 else ""),
        )
        db.add(conv)
        brain.total_conversations += 1
    else:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Store user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    await db.flush()

    # Build context and call AI
    chat_messages = await _build_chat_context(brain, conv, req.message, db)

    try:
        ai_response = await ai_service.chat(
            messages=chat_messages,
            temperature=0.7,
            max_tokens=4096,
        )
        response_text = ai_response["choices"][0]["message"]["content"]
    except Exception as e:
        response_text = (
            f"I encountered an issue connecting to the AI service: {str(e)}\n\n"
            "Make sure OPENROUTER_API_KEY is set in your .env file."
        )

    # Store assistant response
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=response_text,
    )
    db.add(assistant_msg)

    # Auto-learn: if the user asks to remember something, store it as a memory
    if brain.auto_learn:
        lower_msg = req.message.lower()
        if any(kw in lower_msg for kw in ["remember", "note that", "keep in mind", "save this"]):
            try:
                from app.models.memory import MemoryType, MemoryImportance
                memory_service = MemoryService(db)
                await memory_service.store_memory(
                    brain_id=brain.id,
                    memory_type=MemoryType.SEMANTIC,
                    title=f"User note: {req.message[:80]}",
                    content=req.message,
                    importance=MemoryImportance.MEDIUM,
                    source="conversation",
                    source_id=str(conv.id),
                )
                brain.total_memories += 1
            except Exception:
                pass  # Best-effort auto-learn

    return {
        "conversation_id": str(conv.id),
        "response": response_text,
        "brain_status": brain.status.value,
    }


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Stream a chat response from your Brain via Server-Sent Events."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    # Get or create conversation
    conv_id = uuid.UUID(req.conversation_id) if req.conversation_id else uuid.uuid4()
    if not req.conversation_id:
        conv = Conversation(
            id=conv_id,
            brain_id=brain.id,
            title=req.message[:50] + ("..." if len(req.message) > 50 else ""),
        )
        db.add(conv)
        brain.total_conversations += 1
    else:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Store user message
    user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
    db.add(user_msg)
    await db.flush()

    chat_messages = await _build_chat_context(brain, conv, req.message, db)

    async def event_generator():
        full_response = ""
        try:
            # Send conversation_id first
            yield f"data: {json.dumps({'type': 'meta', 'conversation_id': str(conv.id)})}\n\n"

            if not ai_service.api_key:
                content = (
                    "Brain AGI is running in development mode. "
                    "Configure OPENROUTER_API_KEY to enable AI responses."
                )
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                full_response = content
            else:
                import httpx
                async with httpx.AsyncClient(timeout=120) as client:
                    async with client.stream(
                        "POST",
                        f"{ai_service.base_url}/chat/completions",
                        headers=ai_service._headers(),
                        json={
                            "model": ai_service.default_model,
                            "messages": chat_messages,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "stream": True,
                        },
                    ) as response:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_response += content
                                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                                except json.JSONDecodeError:
                                    pass

            # Store complete response
            assistant_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=full_response,
            )
            db.add(assistant_msg)
            await db.commit()

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_msg = f"Stream error: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get messages from a conversation."""
    conv_uuid = uuid.UUID(conversation_id)
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_uuid)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
