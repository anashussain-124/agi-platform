"""Default agent definitions for the orchestrator.
Extracted from orchestrator.py for cleaner separation of config and logic."""

from app.agents.orchestrator import Agent, AgentType, AgentCapability


def get_default_agents() -> list[Agent]:
    """Return the default set of specialized agents."""
    return [
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


# Agent name → AgentType mapping (complete mapping including all agents)
AGENT_TYPE_MAP: dict[str, AgentType] = {
    "Developer Agent": AgentType.DEVELOPER,
    "Research Agent": AgentType.RESEARCHER,
    "Security Agent": AgentType.SECURITY,
    "QA Agent": AgentType.QA,
    "Project Manager Agent": AgentType.PROJECT_MANAGER,
    "Documentation Agent": AgentType.DOCUMENTATION,
    "Infrastructure Agent": AgentType.INFRASTRUCTURE,
    "Business Agent": AgentType.BUSINESS,
    "Marketing Agent": AgentType.MARKETING,
}

# Task keyword → AgentType mapping
TASK_TYPE_MAP: dict[str, AgentType] = {
    "coding": AgentType.DEVELOPER,
    "debug": AgentType.DEVELOPER,
    "refactor": AgentType.DEVELOPER,
    "implement": AgentType.DEVELOPER,
    "research": AgentType.RESEARCHER,
    "documentation": AgentType.DOCUMENTATION,
    "docs": AgentType.DOCUMENTATION,
    "security": AgentType.SECURITY,
    "test": AgentType.QA,
    "deploy": AgentType.INFRASTRUCTURE,
    "infrastructure": AgentType.INFRASTRUCTURE,
    "devops": AgentType.INFRASTRUCTURE,
    "business": AgentType.BUSINESS,
    "analytics": AgentType.BUSINESS,
    "marketing": AgentType.MARKETING,
    "seo": AgentType.MARKETING,
    "plan": AgentType.PROJECT_MANAGER,
    "roadmap": AgentType.PROJECT_MANAGER,
    "design": AgentType.DESIGNER,
}
