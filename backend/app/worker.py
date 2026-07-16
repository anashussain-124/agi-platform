"""Celery worker configuration and task definitions."""
import os
from celery import Celery
import asyncio
from typing import Dict, Any

from app.core.config import settings
from app.agents.orchestrator import AgentOrchestrator
from app.core.database import SessionLocal
from app.services.ai_service import OpenRouterService
from app.services.memory_service import MemoryService

# Initialize Celery app
celery_app = Celery(
    "brain_agi_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="execute_goal_background")
def execute_goal_background(brain_id: str, goal: str, context: str = None) -> Dict[str, Any]:
    """Execute a complex goal in the background using the orchestrator."""
    # We must run the async orchestrator inside a synchronous celery task wrapper
    return asyncio.run(_async_execute_goal(brain_id, goal, context))


async def _async_execute_goal(brain_id: str, goal: str, context: str) -> Dict[str, Any]:
    import uuid
    ai_service = OpenRouterService()
    
    async with SessionLocal() as db:
        memory_service = MemoryService(db)
        orchestrator = AgentOrchestrator(
            brain_id=uuid.UUID(brain_id),
            ai_service=ai_service,
            memory_service=memory_service
        )
        
        # Execute the full goal
        return await orchestrator.orchestrate_goal(goal=goal, context=context)

# ---------------------------------------------------------
# Learning Engine Task
# ---------------------------------------------------------
@celery_app.task(name="process_learning_insights")
def process_learning_insights(brain_id: str, conversation_id: str):
    """Background task to extract user preferences from recent conversations."""
    return asyncio.run(_async_process_learning(brain_id, conversation_id))

async def _async_process_learning(brain_id: str, conversation_id: str):
    import uuid
    from sqlalchemy import select
    from app.models.brain import Message
    from app.models.memory import LearningEntry
    
    ai_service = OpenRouterService()
    
    async with SessionLocal() as db:
        # Fetch conversation
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == uuid.UUID(conversation_id))
            .order_by(Message.created_at.asc())
        )
        messages = result.scalars().all()
        
        if not messages:
            return {"status": "skipped", "reason": "No messages found"}
            
        transcript = "\n".join([f"{m.role}: {m.content}" for m in messages[-10:]])
        
        prompt = (
            "Analyze the following conversation snippet and extract any clear user preferences, "
            "coding styles, or factual statements about the user. Ignore general knowledge. "
            "Return JSON matching this schema: "
            "[{'category': 'preference|coding_style|workflow|fact', 'key': 'string', 'value': 'string', 'confidence': float(0.0-1.0)}]\n\n"
            f"Conversation:\n{transcript}"
        )
        
        try:
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                model=ai_service.reasoning_model,
                temperature=0.1
            )
            import json
            import re
            
            content = response["choices"][0]["message"]["content"]
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                insights = json.loads(match.group(0))
                
                # Store insights
                stored = 0
                for insight in insights:
                    if insight.get("confidence", 0) > 0.7:
                        entry = LearningEntry(
                            brain_id=uuid.UUID(brain_id),
                            category=insight["category"],
                            key=insight["key"],
                            value=insight["value"],
                            confidence=insight["confidence"]
                        )
                        db.add(entry)
                        stored += 1
                        
                await db.commit()
                return {"status": "success", "insights_stored": stored}
        except Exception as e:
            return {"status": "error", "message": str(e)}
