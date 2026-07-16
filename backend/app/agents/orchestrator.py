"""Agent orchestration framework.
Coordinates specialized AI agents for different tasks."""

from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
from datetime import datetime, timezone


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
        """Create the default set of specialized agents."""
        agents_config = [
            Agent(
                agent_type=AgentType.DEVELOPER,
                name="Developer Agent",
                description="Writes, debugs, and refactors code. Handles implementation tasks.",
                capabilities=[
                    AgentCapability("code_generation", "Write new code", ["read", "write", "search", "git"]),
                    AgentCapability("debugging", "Find and fix bugs", ["read", "search", "execute"]),
                    AgentCapability("refactoring", "Improve existing code", ["read", "write", "search"]),
                ],
                system_prompt="You are an expert software developer. Write clean, well-tested code.",
            ),
            Agent(
                agent_type=AgentType.RESEARCHER,
                name="Research Agent",
                description="Searches documentation, papers, and APIs for information.",
                capabilities=[
                    AgentCapability("web_search", "Search the web", ["web_search"]),
                    AgentCapability("document_analysis", "Analyze documents", ["read", "search"]),
                    AgentCapability("api_research", "Research APIs", ["web_search", "read"]),
                ],
                system_prompt="You are a research assistant. Find accurate, relevant information.",
            ),
            Agent(
                agent_type=AgentType.SECURITY,
                name="Security Agent",
                description="Scans for vulnerabilities, secrets, and security issues.",
                capabilities=[
                    AgentCapability("vulnerability_scan", "Find vulnerabilities", ["read", "search"]),
                    AgentCapability("secret_detection", "Find exposed secrets", ["search"]),
                    AgentCapability("dependency_review", "Check dependencies", ["read", "execute"]),
                ],
                system_prompt="You are a security expert. Identify vulnerabilities and suggest fixes.",
            ),
            Agent(
                agent_type=AgentType.QA,
                name="QA Agent",
                description="Generates tests and runs regression checks.",
                capabilities=[
                    AgentCapability("test_generation", "Write tests", ["read", "write"]),
                    AgentCapability("regression", "Run regression checks", ["execute"]),
                ],
                system_prompt="You are a QA engineer. Write thorough tests.",
            ),
            Agent(
                agent_type=AgentType.PROJECT_MANAGER,
                name="Project Manager Agent",
                description="Creates roadmaps, tracks progress, and allocates tasks.",
                capabilities=[
                    AgentCapability("planning", "Create plans", ["read", "write"]),
                    AgentCapability("tracking", "Track progress", ["read"]),
                    AgentCapability("reporting", "Generate reports", ["read", "write"]),
                ],
                system_prompt="You are a project manager. Break down goals into actionable tasks.",
            ),
            Agent(
                agent_type=AgentType.DOCUMENTATION,
                name="Documentation Agent",
                description="Creates and maintains documentation.",
                capabilities=[
                    AgentCapability("readme", "Create READMEs", ["read", "write"]),
                    AgentCapability("docs", "Write documentation", ["read", "write", "search"]),
                    AgentCapability("changelog", "Generate changelogs", ["read", "write"]),
                ],
                system_prompt="You are a technical writer. Create clear, comprehensive documentation.",
            ),
            Agent(
                agent_type=AgentType.INFRASTRUCTURE,
                name="Infrastructure Agent",
                description="Handles deployments, monitoring, and CI/CD.",
                capabilities=[
                    AgentCapability("deployment", "Deploy applications", ["execute", "read"]),
                    AgentCapability("monitoring", "Monitor systems", ["read", "execute"]),
                    AgentCapability("ci_cd", "Manage CI/CD", ["read", "write", "execute"]),
                ],
                system_prompt="You are a DevOps engineer. Manage infrastructure reliably.",
            ),
            Agent(
                agent_type=AgentType.BUSINESS,
                name="Business Agent",
                description="Analyzes analytics, revenue, and growth.",
                capabilities=[
                    AgentCapability("analytics", "Analyze metrics", ["read", "execute"]),
                    AgentCapability("reporting", "Business reports", ["read", "write"]),
                    AgentCapability("strategy", "Strategic advice", ["read", "web_search"]),
                ],
                system_prompt="You are a business analyst. Provide data-driven insights.",
            ),
            Agent(
                agent_type=AgentType.MARKETING,
                name="Marketing Agent",
                description="SEO, content ideas, and social media.",
                capabilities=[
                    AgentCapability("seo", "SEO analysis", ["web_search", "read"]),
                    AgentCapability("content", "Content creation", ["write"]),
                    AgentCapability("social_media", "Social media", ["write"]),
                ],
                system_prompt="You are a marketing specialist. Drive growth through content and SEO.",
            ),
        ]

        for agent in agents_config:
            self.agents[agent.agent_type.value] = agent

    def get_agent(self, agent_type: AgentType) -> Optional[Agent]:
        return self.agents.get(agent_type.value)

    def get_available_agents(self) -> List[Agent]:
        return [a for a in self.agents.values() if not a.is_busy]

    def select_agent_for_task(self, task_type: str) -> Optional[Agent]:
        """Intelligently select the best agent for a task."""
        type_map = {
            "coding": AgentType.DEVELOPER,
            "debug": AgentType.DEVELOPER,
            "refactor": AgentType.DEVELOPER,
            "implement": AgentType.DEVELOPER,
            "research": AgentType.RESEARCHER,
            "documentation": AgentType.DOCUMENTATION,
            "security": AgentType.SECURITY,
            "test": AgentType.QA,
            "deploy": AgentType.INFRASTRUCTURE,
            "infrastructure": AgentType.INFRASTRUCTURE,
            "business": AgentType.BUSINESS,
            "analytics": AgentType.BUSINESS,
            "marketing": AgentType.MARKETING,
            "plan": AgentType.PROJECT_MANAGER,
            "design": AgentType.DESIGNER,
        }

        agent_type = type_map.get(task_type, AgentType.ORCHESTRATOR)
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
                
                # Override with agent preference if it exists and we didn't specifically route to reasoning/agent
                if agent.capabilities and model == self.ai_service.default_model:
                     model = agent.capabilities[0].model_preference
                     
                response = await self.ai_service.chat(messages=messages, model=model)
                result = response["choices"][0]["message"]["content"]
            else:
                result = f"[{agent.name} would process: {task[:100]}...]"

            agent.tasks_completed += 1
            return {"agent": agent.name, "result": result, "success": True}

        except Exception as e:
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
        import json
        
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
            # Fallback if AI didn't return valid JSON
            return {
                "goal": goal,
                "plan": plan_text,
                "error": "Failed to parse plan into JSON tasks.",
                "subtasks": []
            }

        # 3. Execute tasks with appropriate agents
        results = {
            "goal": goal,
            "plan": tasks,
            "subtasks": [],
        }

        # Map string agent names back to enum
        agent_map = {
            "Developer Agent": AgentType.DEVELOPER,
            "Research Agent": AgentType.RESEARCHER,
            "Security Agent": AgentType.SECURITY,
            "QA Agent": AgentType.QA,
            "Project Manager": AgentType.PROJECT_MANAGER,
        }

        for i, step in enumerate(tasks):
            agent_str = step.get("agent", "Developer Agent")
            task_desc = step.get("task", "")
            
            # Find the best agent type, default to developer
            agent_type = agent_map.get(agent_str, AgentType.DEVELOPER)
            
            # 1. Generate (Execute subtask)
            step_result = await self.delegate_to_agent(agent_type, task_desc)
            
            # 2. QA Review / Fact Check
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
                "status": "approved" if "APPROVED" in review_text else "rejected_or_warned"
            })

        return results
