"""Agent orchestration framework.
Coordinates specialized AI agents for different tasks."""

from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
import json
from datetime import datetime, timezone

from app.core.logging import logger


class AgentType(str, Enum):
    DEVELOPER = "developer"
    RESEARCHER = "researcher"
    DESIGNER = "designer"
    SECURITY = "security"
    QA = "qa"
    MARKETING = "marketing"
    BUSINESS = "business"
    PROJECT_MANAGER = "project_manager"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"
    ORCHESTRATOR = "orchestrator"


class AgentCapability:
    """Describes what an agent can do."""

    def __init__(
        self,
        name: str,
        description: str,
        tools: List[str],
        model_preference: str = "openai/gpt-4o-mini",
    ):
        self.name = name
        self.description = description
        self.tools = tools
        self.model_preference = model_preference


class Agent:
    """A specialized AI agent with specific capabilities."""

    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        system_prompt: str,
    ):
        self.id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.system_prompt = system_prompt
        self.is_busy = False
        self.current_task_id = None
        self.tasks_completed = 0
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.agent_type.value,
            "name": self.name,
            "description": self.description,
            "is_busy": self.is_busy,
            "current_task_id": self.current_task_id,
            "tasks_completed": self.tasks_completed,
            "capabilities": [c.name for c in self.capabilities],
        }


class AgentOrchestrator:
    """Coordinates multiple agents to accomplish complex goals."""

    def __init__(self, brain_id: uuid.UUID, ai_service=None, memory_service=None):
        self.brain_id = brain_id
        self.ai_service = ai_service
        self.memory_service = memory_service
        self.agents: Dict[str, Agent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """Load agents from the extracted config module."""
        from app.agents.agent_config import get_default_agents

        for agent in get_default_agents():
            self.agents[agent.agent_type.value] = agent

    def get_agent(self, agent_type: AgentType) -> Optional[Agent]:
        return self.agents.get(agent_type.value)

    def get_available_agents(self) -> List[Agent]:
        return [a for a in self.agents.values() if not a.is_busy]

    def select_agent_for_task(self, task_type: str) -> Optional[Agent]:
        """Intelligently select the best agent for a task."""
        from app.agents.agent_config import TASK_TYPE_MAP

        agent_type = TASK_TYPE_MAP.get(task_type, AgentType.ORCHESTRATOR)
        return self.agents.get(agent_type.value)

    async def delegate_to_agent(
        self,
        agent_type: AgentType,
        task: str,
        context: Optional[str] = None,
    ) -> dict:
        """Delegate a task to a specific agent and get the result."""
        agent = self.get_agent(agent_type)
        if not agent:
            return {"error": f"No agent found for type: {agent_type}"}

        if agent.is_busy:
            return {"error": f"Agent {agent.name} is busy"}

        agent.is_busy = True
        logger.info("Delegating task to %s: %s", agent.name, task[:80])

        try:
            # Build the prompt
            messages = [
                {"role": "system", "content": agent.system_prompt},
            ]
            if context:
                messages.append({"role": "system", "content": f"Context:\n{context}"})
            messages.append({"role": "user", "content": task})

            # Load tools from plugin registry
            from app.plugins.base import PluginRegistry
            from app.agents.base import get_default_plugin_registry
            registry = get_default_plugin_registry()
            tools = registry.get_all_tools()

            # Call AI
            if self.ai_service:
                # Dynamically route to the best model for the task
                model = self.ai_service.route_task(task, requires_tools=len(tools) > 0)

                # Use the unified routing tier (reasoning/fast) for all agents.
                # Agent-specific model preferences are ignored to keep everything
                # on the free provider chain.
                response = await self.ai_service.chat(messages=messages, model=model)
                result = response["choices"][0]["message"]["content"]
            else:
                result = f"[{agent.name} would process: {task[:100]}...]"

            agent.tasks_completed += 1
            logger.info("Agent %s completed task successfully", agent.name)
            return {"agent": agent.name, "result": result, "success": True}

        except Exception as e:
            logger.error("Agent %s failed: %s", agent.name, str(e)[:200])
            return {"agent": agent.name, "error": str(e), "success": False}
        finally:
            agent.is_busy = False
            agent.current_task_id = None

    async def orchestrate_goal(
        self,
        goal: str,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Break down a goal and coordinate multiple agents to achieve it."""
        from app.agents.agent_config import AGENT_TYPE_MAP

        logger.info("Orchestrating goal: %s", goal[:100])

        # 1. PM agent creates the plan as a JSON array of tasks
        pm_prompt = (
            f"Break down this goal into actionable steps.\nGoal: {goal}\n\n"
            f"Context: {context or 'None provided'}\n\n"
            "Return ONLY a JSON array of task objects. Example:\n"
            '[\n  {"agent": "Developer Agent", "task": "Write the function X"},\n'
            '  {"agent": "QA Agent", "task": "Test the function X"}\n]'
        )
        pm_result = await self.delegate_to_agent(AgentType.PROJECT_MANAGER, pm_prompt)

        # 2. Parse the plan into tasks
        plan_text = pm_result.get("result", "")
        tasks = []
        try:
            # Strip markdown code blocks if present
            clean_text = plan_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            tasks = json.loads(clean_text.strip())
        except json.JSONDecodeError:
            logger.warning("Failed to parse plan JSON for goal: %s", goal[:50])
            return {
                "goal": goal,
                "plan": plan_text,
                "error": "Failed to parse plan into JSON tasks.",
                "subtasks": [],
            }

        # 3. Execute tasks with appropriate agents
        results: Dict[str, Any] = {
            "goal": goal,
            "plan": tasks,
            "subtasks": [],
        }

        for i, step in enumerate(tasks):
            agent_str = step.get("agent", "Developer Agent")
            task_desc = step.get("task", "")

            # Find the best agent type, default to developer
            agent_type = AGENT_TYPE_MAP.get(agent_str, AgentType.DEVELOPER)

            # Execute subtask
            step_result = await self.delegate_to_agent(agent_type, task_desc)

            # QA Review
            review_prompt = (
                f"Review the following output for the task: '{task_desc}'.\n"
                f"Check for accuracy, completeness, and potential issues.\n\n"
                f"Output to review:\n{step_result.get('result', step_result.get('error', 'None'))}\n\n"
                "If it looks good, respond with 'APPROVED: [brief reason]'. "
                "If there are issues, respond with 'REJECTED: [detailed feedback]'."
            )
            review_result = await self.delegate_to_agent(AgentType.QA, review_prompt)
            review_text = review_result.get("result", "")

            results["subtasks"].append({
                "step": i + 1,
                "assigned_to": agent_str,
                "task": task_desc,
                "outcome": step_result,
                "qa_review": review_text,
                "status": "approved" if "APPROVED" in review_text else "rejected_or_warned",
            })

        logger.info("Goal orchestration complete: %d subtasks", len(results["subtasks"]))
        return results
