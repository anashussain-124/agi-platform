"""Agent base class and tool framework."""
from typing import Optional, List, Dict, Any, Callable
import json


class Tool:
    """A tool that an agent can use."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict,
        function: Callable,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function

    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    async def execute(self, **kwargs) -> str:
        try:
            result = await self.function(**kwargs)
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})


from app.plugins.base import PluginRegistry
from app.plugins.web import WebPlugin
from app.plugins.filesystem import FileSystemPlugin
from app.plugins.system import SystemPlugin
from app.plugins.github import GitHubPlugin
from app.plugins.website import WebsitePlugin

def get_default_plugin_registry() -> PluginRegistry:
    """Create a registry with default plugins."""
    registry = PluginRegistry()
    registry.register_plugin(WebPlugin())
    registry.register_plugin(FileSystemPlugin())
    registry.register_plugin(SystemPlugin())
    registry.register_plugin(GitHubPlugin())
    registry.register_plugin(WebsitePlugin())
    return registry
