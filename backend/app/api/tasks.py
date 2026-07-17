"""Task and goal management API — uses Repository pattern for dual-mode data access."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.database import get_async_session
from app.core.repository import BaseRepository
from app.models.user import User
from app.models.brain import Brain
from app.models.task import Task, Goal, TaskStatus, TaskPriority, Automation
from app.api.auth import get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ──────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    requires_approval: bool = False


class CreateGoalRequest(BaseModel):
    title: str
    description: Optional[str] = None
    milestones: Optional[list] = None
    constraints: Optional[list] = None


# ──────────────────────────────────────────────────────────
# Repository
# ──────────────────────────────────────────────────────────

class TaskRepository(BaseRepository):
    """Data access for tasks, goals, and automations."""

    async def get_brain_id(self, user_id: str) -> Optional[str]:
        if self.use_supabase:
            rows = await self.supabase.get("brains", filters={"user_id": user_id}, limit=1)
            return rows[0]["id"] if rows else None
        result = await self.db.execute(select(Brain).where(Brain.user_id == uuid.UUID(user_id)))
        brain = result.scalar_one_or_none()
        return str(brain.id) if brain else None

    async def list_tasks(self, brain_id: str, status: Optional[str] = None, limit: int = 20) -> list[dict]:
        if self.use_supabase:
            filters = {"brain_id": brain_id}
            if status:
                filters["status"] = status
            rows = await self.supabase.get("tasks", filters=filters, order="created_at.desc", limit=limit)
            return [_task_to_dict(r) for r in rows]

        query = select(Task).where(Task.brain_id == uuid.UUID(brain_id))
        if status:
            query = query.where(Task.status == TaskStatus(status))
        query = query.order_by(desc(Task.created_at)).limit(limit)
        result = await self.db.execute(query)
        return [_task_to_dict(t) for t in result.scalars().all()]

    async def create_task(self, brain_id: str, title: str, description: Optional[str],
                          priority: str, requires_approval: bool) -> dict:
        if self.use_supabase:
            task = await self.supabase.create("tasks", {
                "brain_id": brain_id,
                "title": title,
                "description": description,
                "priority": priority,
                "requires_approval": requires_approval,
                "status": "PENDING",
            })
            return {"id": task["id"], "title": task["title"],
                    "status": task.get("status", "PENDING"), "created_at": task.get("created_at", "")}

        task = Task(
            brain_id=uuid.UUID(brain_id), title=title, description=description,
            priority=TaskPriority(priority), requires_approval=requires_approval,
        )
        self.db.add(task)
        await self.db.flush()
        return {"id": str(task.id), "title": task.title,
                "status": task.status.value, "created_at": task.created_at.isoformat()}

    async def list_goals(self, brain_id: str, limit: int = 50) -> list[dict]:
        if self.use_supabase:
            rows = await self.supabase.get("goals", filters={"brain_id": brain_id},
                                           order="created_at.desc", limit=limit)
            return [_goal_to_dict(r) for r in rows]

        result = await self.db.execute(
            select(Goal).where(Goal.brain_id == uuid.UUID(brain_id))
            .order_by(desc(Goal.created_at)).limit(limit)
        )
        return [_goal_to_dict(g) for g in result.scalars().all()]

    async def create_goal(self, brain_id: str, title: str, description: Optional[str],
                          milestones: list, constraints: list) -> dict:
        if self.use_supabase:
            goal = await self.supabase.create("goals", {
                "brain_id": brain_id, "title": title, "description": description,
                "milestones": milestones, "constraints": constraints, "status": "active",
            })
            return {"id": goal["id"], "title": goal["title"],
                    "status": goal.get("status", "active"), "created_at": goal.get("created_at", "")}

        goal = Goal(
            brain_id=uuid.UUID(brain_id), title=title, description=description,
            milestones=milestones, constraints=constraints,
        )
        self.db.add(goal)
        await self.db.flush()
        return {"id": str(goal.id), "title": goal.title,
                "status": goal.status, "created_at": goal.created_at.isoformat()}

    async def list_automations(self, brain_id: str, limit: int = 50) -> list[dict]:
        if self.use_supabase:
            rows = await self.supabase.get("automations", filters={"brain_id": brain_id}, limit=limit)
            return [_automation_to_dict(r) for r in rows]

        result = await self.db.execute(
            select(Automation).where(Automation.brain_id == uuid.UUID(brain_id))
        )
        return [_automation_to_dict(a) for a in result.scalars().all()]


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def _task_to_dict(t) -> dict:
    """Normalize task data to response dict."""
    if isinstance(t, dict):
        total = t.get("total_steps", 0)
        return {
            "id": t["id"], "title": t.get("title", ""), "description": t.get("description"),
            "status": t.get("status", ""), "priority": t.get("priority", ""),
            "assigned_agent": t.get("assigned_agent"),
            "requires_approval": t.get("requires_approval", False),
            "progress": f"{t.get('current_step', 0)}/{total}" if total > 0 else None,
            "created_at": t.get("created_at", ""),
        }
    return {
        "id": str(t.id), "title": t.title, "description": t.description,
        "status": t.status.value, "priority": t.priority.value,
        "assigned_agent": t.assigned_agent, "requires_approval": t.requires_approval,
        "progress": f"{t.current_step}/{t.total_steps}" if t.total_steps > 0 else None,
        "created_at": t.created_at.isoformat(),
    }


def _goal_to_dict(g) -> dict:
    """Normalize goal data to response dict."""
    if isinstance(g, dict):
        return {
            "id": g["id"], "title": g.get("title", ""), "description": g.get("description"),
            "status": g.get("status", ""), "progress": g.get("progress", 0),
            "milestones": g.get("milestones", []) or [], "created_at": g.get("created_at", ""),
        }
    return {
        "id": str(g.id), "title": g.title, "description": g.description,
        "status": g.status, "progress": g.progress,
        "milestones": g.milestones or [], "created_at": g.created_at.isoformat(),
    }


def _automation_to_dict(a) -> dict:
    """Normalize automation data to response dict."""
    if isinstance(a, dict):
        return {
            "id": a["id"], "name": a.get("name", ""), "trigger_type": a.get("trigger_type", ""),
            "is_active": a.get("is_active", True), "last_run_at": a.get("last_run_at"),
            "run_count": a.get("run_count", 0),
        }
    return {
        "id": str(a.id), "name": a.name, "trigger_type": a.trigger_type,
        "is_active": a.is_active,
        "last_run_at": a.last_run_at.isoformat() if a.last_run_at else None,
        "run_count": a.run_count,
    }


# ──────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────

@router.get("/")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        repo = TaskRepository(db)
        brain_id = await repo.get_brain_id(str(user.id))
        if not brain_id:
            raise HTTPException(status_code=404, detail="Brain not found")
        return await repo.list_tasks(brain_id, status, limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")


@router.post("/")
async def create_task(
    req: CreateTaskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        repo = TaskRepository(db)
        brain_id = await repo.get_brain_id(str(user.id))
        if not brain_id:
            raise HTTPException(status_code=404, detail="Brain not found")
        priority = req.priority.value if hasattr(req.priority, "value") else req.priority
        return await repo.create_task(brain_id, req.title, req.description, priority, req.requires_approval)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")


@router.get("/goals")
async def list_goals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        repo = TaskRepository(db)
        brain_id = await repo.get_brain_id(str(user.id))
        if not brain_id:
            raise HTTPException(status_code=404, detail="Brain not found")
        return await repo.list_goals(brain_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")


@router.post("/goals")
async def create_goal(
    req: CreateGoalRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        repo = TaskRepository(db)
        brain_id = await repo.get_brain_id(str(user.id))
        if not brain_id:
            raise HTTPException(status_code=404, detail="Brain not found")
        return await repo.create_goal(
            brain_id, req.title, req.description,
            req.milestones or [], req.constraints or [],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")


@router.get("/automations")
async def list_automations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        repo = TaskRepository(db)
        brain_id = await repo.get_brain_id(str(user.id))
        if not brain_id:
            raise HTTPException(status_code=404, detail="Brain not found")
        return await repo.list_automations(brain_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:300]}")
