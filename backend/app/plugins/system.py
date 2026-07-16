from typing import Dict, Any
from app.plugins.base import BasePlugin

class SystemPlugin(BasePlugin):
    name = "SystemPlugin"
    description = "Provides system and shell command execution capabilities."
    
    def _register_actions(self):
        self.register_action(
            name="execute_command",
            description="Execute a shell command.",
            schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash/shell command to execute"},
                },
                "required": ["command"],
            },
            handler=self.execute_command
        )

    async def execute_command(self, command: str) -> Dict[str, Any]:
        import asyncio
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return {
                "command": command,
                "exit_code": process.returncode,
                "stdout": stdout.decode()[:5000] if stdout else "",
                "stderr": stderr.decode()[:5000] if stderr else ""
            }
        except Exception as e:
            return {"command": command, "error": str(e)}
