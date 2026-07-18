"""Executive Brain — the cognitive orchestration layer of the AI Human Brain.

This is the "Executive Function" of the system. It:
  1. Receives a high-level goal from the user.
  2. Loads relevant working/episodic memory as context.
  3. Uses the AgentOrchestrator to decompose the goal into a plan.
  4. Executes the plan by delegating subtasks to specialized agents.
  5. Persists the goal + each task to the data layer (dual-mode: Supabase or SQLAlchemy).
  6. Records outcomes back into memory.

It is intentionally backend-agnostic: when Supabase is configured it talks to the
REST API; otherwise it falls back to the SQLAlchemy session. The orchestrator
itself is model-driven (OpenRouter), so it works in both modes.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json
import uuid

from app.core.logging import logger
from app.core.repository import is_supabase_mode, get_supabase
from app.agents.orchestrator import AgentOrchestrator, AgentType
from app.agents.agent_config import AGENT_TYPE_MAP
from app.services.ai_service import OpenRouterService


# ──────────────────────────────────────────────────────────
# Persistence helpers (dual-mode)
# ──────────────────────────────────────────────────────────

async def _persist_goal(brain_id: str, title: str, description: str,
                        plan: list, db) -> dict:
    """Create a goal row. Returns the created record (dict)."""
    supabase = get_supabase()
    if supabase:
        return await supabase.create("goals", {
            "brain_id": brain_id,
            "title": title,
            "description": description,
            "status": "active",
            "progress": 0,
            "milestones": plan,
            "constraints": [],
        })
    # SQLAlchemy fallback
    from app.models.brain import Goal
    goal = Goal(brain_id=uuid.UUID(brain_id), title=title, description=description,
                milestones=plan, constraints=[])
    db.add(goal)
    await db.flush()
    return {"id": str(goal.id), "title": goal.title, "status": goal.status,
            "progress": goal.progress}


async def _persist_task(brain_id: str, goal_id: str, title: str,
                        description: str, assigned_agent: str, status: str,
                        result: Optional[dict], db) -> dict:
    """Create or update a task row linked to a goal."""
    supabase = get_supabase()
    if supabase:
        return await supabase.create("tasks", {
            "brain_id": brain_id,
            "goal_id": goal_id,
            "title": title,
            "description": description,
            "assigned_agent": assigned_agent,
            "status": status.upper(),
            "priority": "MEDIUM",
            "requires_approval": False,
            "result": result or {},
            "plan": {},
            "current_step": 1 if status == "completed" else 0,
            "total_steps": 1,
        })
    from app.models.brain import Task, TaskStatus, TaskPriority
    task = Task(brain_id=uuid.UUID(brain_id), goal_id=uuid.UUID(goal_id) if goal_id else None,
                title=title, description=description, assigned_agent=assigned_agent,
                status=TaskStatus(status), priority=TaskPriority.MEDIUM,
                requires_approval=False, result=result or {})
    db.add(task)
    await db.flush()
    return {"id": str(task.id), "title": task.title, "status": task.status.value}


async def _update_goal_progress(goal_id: str, progress: int, status: str, db):
    """Update goal progress + status."""
    supabase = get_supabase()
    if supabase:
        await supabase.update("goals", {"id": goal_id},
                              {"progress": progress, "status": status.upper()})
        return
    from app.models.brain import Goal
    goal = await db.get(Goal, uuid.UUID(goal_id))
    if goal:
        goal.progress = progress
        goal.status = status


async def _record_memory(brain_id: str, title: str, content: str, db):
    """Store an episodic memory of a completed goal (Supabase only — memory service
    needs pgvector which is available via SQLAlchemy; for Supabase we write a plain
    memory entry without embedding to keep it light)."""
    supabase = get_supabase()
    if supabase:
        try:
            await supabase.create("memory_entries", {
                "brain_id": brain_id,
                "memory_type": "episodic",
                "importance": "medium",
                "title": title,
                "content": content,
                "summary": content[:280],
                "tags": {"source": "executive_brain"},
                "context": {},
                "access_count": 0,
            })
        except Exception as e:
            logger.warning("Could not record memory: %s", str(e)[:120])


# ──────────────────────────────────────────────────────────
# Executive Brain
# ──────────────────────────────────────────────────────────

class ExecutiveBrain:
    """The executive function that turns goals into executed plans."""

    def __init__(self, brain_id: str, db=None, ai_service: Optional[OpenRouterService] = None):
        self.brain_id = brain_id
        self.db = db
        self.ai_service = ai_service or OpenRouterService()
        self.orchestrator = AgentOrchestrator(
            brain_id=uuid.UUID(brain_id) if _looks_like_uuid(brain_id) else uuid.uuid4(),
            ai_service=self.ai_service,
            memory_service=None,
        )

    # ──────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────

    async def _load_memory_context(self) -> str:
        """Pull recent working/episodic memory to ground the plan in prior context."""
        supabase = get_supabase()
        if not supabase:
            return ""
        try:
            rows = await supabase.get(
                "memory_entries",
                filters={"brain_id": self.brain_id},
                order="created_at.desc",
                limit=5,
            )
            if not rows:
                return ""
            parts = []
            for r in rows:
                parts.append(f"- {r.get('title', '')}: {r.get('content', '')[:200]}")
            return "Relevant prior memory:\n" + "\n".join(parts)
        except Exception as e:
            logger.warning("Memory context load failed: %s", str(e)[:120])
            return ""

    @staticmethod
    def _extract_json_array(text: str) -> Optional[list]:
        """Robustly extract a JSON array from model output that may contain prose,
        markdown fences, or multiple array-looking fragments."""
        if not text:
            return None
        cleaned = text.strip()
        # Strip markdown code fences
        if cleaned.startswith("```"):
            # remove opening fence (```json or ```)
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        # Try direct parse
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        # Find the outermost [ ... ] span
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                pass
        return None

    async def _decompose_goal(self, goal_text: str, context: str) -> list:
        """Use the reasoning model to break a goal into a structured plan.

        Returns a list of dicts: {"agent": <AgentType.value>, "task": <str>}.
        """
        sys_prompt = (
            "You are the Executive Planner for an autonomous AI Brain. "
            "Given a high-level goal, decompose it into 3-6 concrete, actionable steps. "
            "Each step must name the best-fit specialist agent and a clear task description. "
            "Available agents: developer, researcher, security, qa, project_manager, "
            "documentation, infrastructure, business, marketing.\n\n"
            "Respond with ONLY a JSON array — no prose, no markdown fences. Example:\n"
            '[{"agent":"researcher","task":"Research the top 5 HN APIs"},'
            '{"agent":"developer","task":"Write the scraper script"},'
            '{"agent":"qa","task":"Write tests for the scraper"}]'
        )
        user_prompt = f"Goal: {goal_text}"
        if context:
            user_prompt += f"\n\nContext:\n{context}"

        try:
            # Use an explicit reliable model for planning (gpt-4o-mini) rather than
            # the env-configured reasoning model, which may be a rate-limited free
            # model. The chat() fanout still retries other models on 429/timeout.
            result = await self.ai_service.chat(
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="openai/gpt-4o-mini",
                temperature=0.3,
                max_tokens=4096,
            )
            raw = result["choices"][0]["message"]["content"]
            plan = self._extract_json_array(raw)
            if plan:
                # Normalize / filter to valid structure
                clean = []
                for step in plan:
                    if not isinstance(step, dict):
                        continue
                    agent = str(step.get("agent", "developer")).strip().lower()
                    task = str(step.get("task") or step.get("description") or "").strip()
                    if not task:
                        continue
                    # Map agent name to a known type if possible
                    known = {a.value: a.value for a in AgentType}
                    agent_val = agent if agent in known else "developer"
                    clean.append({"agent": agent_val, "task": task})
                if clean:
                    return clean
        except Exception as e:
            logger.warning("Goal decomposition failed: %s", str(e)[:160])

        # Fallback: a single developer task so the goal still executes
        return [{"agent": "developer", "task": goal_text}]

    async def _run_subtask(self, agent_type_value: str, task: str, context: str) -> dict:
        """Execute a single subtask via the orchestrator's agent delegation."""
        from app.agents.agent_config import AGENT_TYPE_MAP
        agent_type = AGENT_TYPE_MAP.get(agent_type_value.title() + " Agent", AgentType.DEVELOPER) \
            if agent_type_value + " Agent" in AGENT_TYPE_MAP else AgentType.DEVELOPER
        # Direct lookup by value
        for name, at in AGENT_TYPE_MAP.items():
            if at.value == agent_type_value:
                agent_type = at
                break
        return await self.orchestrator.delegate_to_agent(agent_type, task, context=context or None)

    async def execute_goal(
        self,
        goal_text: str,
        description: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """Decompose and execute a goal end-to-end.

        Returns a structured result with the goal id, the plan, and per-step outcomes.
        """
        logger.info("ExecutiveBrain: executing goal '%s'", goal_text[:80])

        memory_ctx = await self._load_memory_context()
        combined_context = "\n\n".join(filter(None, [memory_ctx, context or ""]))

        # 1. Decompose the goal into a plan.
        plan = await self._decompose_goal(goal_text, combined_context)

        # 2. Persist the goal.
        goal_record = await _persist_goal(
            self.brain_id, goal_text, description or goal_text, plan, self.db,
        )
        goal_id = goal_record.get("id")

        # 3. Execute each subtask via the appropriate agent + QA review.
        steps_out = []
        completed = 0
        for i, step in enumerate(plan):
            agent_val = step.get("agent", "developer")
            task_desc = step.get("task", "")
            outcome = await self._run_subtask(agent_val, task_desc, combined_context)

            # QA review of the outcome
            review_text = ""
            try:
                review_prompt = (
                    f"Review this output for the task: '{task_desc}'.\n"
                    f"Output:\n{outcome.get('result', outcome.get('error', 'None'))[:1500]}\n\n"
                    "If good, reply 'APPROVED: [reason]'. If issues, 'REJECTED: [feedback]'."
                )
                review_result = await self.orchestrator.delegate_to_agent(
                    AgentType.QA, review_prompt)
                review_text = review_result.get("result", "")
            except Exception:
                review_text = ""

            status = "completed" if outcome.get("success") else "failed"
            if status == "completed":
                completed += 1

            task_record = await _persist_task(
                self.brain_id, goal_id, task_desc,
                (outcome.get("result") or outcome.get("error") or "")[:500],
                agent_val, status, outcome, self.db,
            )
            steps_out.append({
                "task_id": task_record.get("id"),
                "agent": agent_val,
                "task": task_desc,
                "status": status,
                "qa_review": review_text[:400],
                "result": (outcome.get("result") or "")[:600],
            })

        # 4. Update goal progress.
        total = len(steps_out) or 1
        progress = int((completed / total) * 100)
        final_status = "completed" if completed == total else "in_progress"
        if goal_id:
            await _update_goal_progress(goal_id, progress, final_status, self.db)

        # 5. Record an episodic memory of this goal.
        await _record_memory(
            self.brain_id,
            f"Goal executed: {goal_text[:80]}",
            f"Completed {completed}/{total} subtasks. Status: {final_status}.",
            self.db,
        )

        return {
            "goal_id": goal_id,
            "goal": goal_text,
            "status": final_status,
            "progress": progress,
            "plan": plan,
            "steps": steps_out,
        }

    async def quick_plan(self, goal_text: str, context: Optional[str] = None) -> dict:
        """Decompose a goal into a plan WITHOUT executing (for preview/approval)."""
        memory_ctx = await self._load_memory_context()
        combined_context = "\n\n".join(filter(None, [memory_ctx, context or ""]))
        try:
            plan = await self._decompose_goal(goal_text, combined_context)
            return {
                "goal": goal_text,
                "plan": plan,
                "status": "planned" if plan else "error",
            }
        except Exception as e:
            return {"goal": goal_text, "status": "error", "error": str(e)[:300], "plan": []}


def _looks_like_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False
