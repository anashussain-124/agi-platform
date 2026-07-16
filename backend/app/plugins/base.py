"""Base Plugin Architecture for the AI Human Brain."""
from typing import Dict, Any, List, Callable, Awaitable
from pydantic import BaseModel
import inspect

class PluginAction(BaseModel):
    name: str
    description: str
    schema: Dict[str, Any]
    handler: Callable[..., Awaitable[Dict[str, Any]]]

class BasePlugin:
    """Base class for all BrainAGI plugins."""
    
    name: str = "Base Plugin"
    description: str = "Base plugin description"
    version: str = "0.1.0"
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._actions: List[PluginAction] = []
        self._register_actions()

    def _register_actions(self):
        """Override this method to register actions via self.register_action()"""
        pass

    def register_action(self, name: str, description: str, schema: Dict[str, Any], handler: Callable[..., Awaitable[Dict[str, Any]]]):
        """Register an action that AI agents can use."""
        self._actions.append(PluginAction(
            name=name,
            description=description,
            schema=schema,
            handler=handler
        ))

    def get_actions(self) -> List[PluginAction]:
        """Return all registered actions for this plugin."""
        return self._actions

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Return the plugin's actions formatted as OpenAI function tools."""
        tools = []
        for action in self._actions:
            tools.append({
                "type": "function",
                "function": {
                    "name": f"{self.__class__.__name__.lower()}_{action.name}",
                    "description": action.description,
                    "parameters": action.schema
                }
            })
        return tools

class PluginRegistry:
    """Central registry for all active plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}

    def register_plugin(self, plugin: BasePlugin):
        self._plugins[plugin.name] = plugin

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get OpenAI formatted tools from all registered plugins."""
        tools = []
        for plugin in self._plugins.values():
            tools.extend(plugin.get_openai_tools())
        return tools
        
    async def execute_action(self, plugin_name: str, action_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific plugin action."""
        if plugin_name not in self._plugins:
            return {"error": f"Plugin {plugin_name} not found"}
            
        plugin = self._plugins[plugin_name]
        for action in plugin.get_actions():
            if action.name == action_name:
                try:
                    return await action.handler(**kwargs)
                except Exception as e:
                    return {"error": f"Action execution failed: {str(e)}"}
                    
        return {"error": f"Action {action_name} not found in plugin {plugin_name}"}
