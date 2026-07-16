"""Task and goal management API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.database import get_async_session
from app.models.user import User
from app.models.brain import Brain
from app.models.task import Task, Goal, TaskStatus, TaskPriority, Automation
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


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


@router.get("/")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List tasks for the user's brain."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    query = select(Task).where(Task.brain_id == brain.id)
    if status:
        query = query.where(Task.status == TaskStatus(status))
    query = query.order_by(desc(Task.created_at)).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "title": t.title,
            "description": t.description,
            "status": t.status.value,
            "priority": t.priority.value,
            "assigned_agent": t.assigned_agent,
            "requires_approval": t.requires_approval,
            "progress": f"{t.current_step}/{t.total_steps}" if t.total_steps > 0 else None,
            "created_at": t.created_at.isoformat(),
        }
        for t in tasks
    ]


@router.post("/")
async def create_task(
    req: CreateTaskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new task for the Brain."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    task = Task(
        brain_id=brain.id,
        title=req.title,
        description=req.description,
        priority=req.priority,
        requires_approval=req.requires_approval,
    )
    db.add(task)
    brain.total_tasks += 1

    return {
        "id": str(task.id),
        "title": task.title,
        "status": task.status.value,
        "created_at": task.created_at.isoformat(),
    }


@router.get("/goals")
async def list_goals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List goals."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404)

    result = await db.execute(
        select(Goal).where(Goal.brain_id == brain.id).order_by(desc(Goal.created_at))
    )
    goals = result.scalars().all()

    return [
        {
            "id": str(g.id),
            "title": g.title,
            "description": g.description,
            "status": g.status,
            "progress": g.progress,
            "milestones": g.milestones or [],
            "created_at": g.created_at.isoformat(),
        }
        for g in goals
    ]


@router.post("/goals")
async def create_goal(
    req: CreateGoalRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new goal."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    goal = Goal(
        brain_id=brain.id,
        title=req.title,
        description=req.description,
        milestones=req.milestones or [],
        constraints=req.constraints or [],
    )
    db.add(goal)

    return {
        "id": str(goal.id),
        "title": goal.title,
        "status": goal.status,
        "created_at": goal.created_at.isoformat(),
    }


@router.get("/automations")
async def list_automations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List automations."""
    result = await db.execute(select(Brain).where(Brain.user_id == user.id))
    brain = result.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404)

    result = await db.execute(
        select(Automation).where(Automation.brain_id == brain.id)
    )
    automations = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "name": a.name,
            "trigger_type": a.trigger_type,
            "is_active": a.is_active,
            "last_run_at": a.last_run_at.isoformat() if a.last_run_at else None,
            "run_count": a.run_count,
        }
        for a in automations
    ]
