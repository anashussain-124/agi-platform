from typing import Dict, Any
from app.plugins.base import BasePlugin

class FileSystemPlugin(BasePlugin):
    name = "FileSystemPlugin"
    description = "Provides file reading and writing capabilities."
    
    def _register_actions(self):
        self.register_action(
            name="read_file",
            description="Read a file from the workspace.",
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The absolute or relative path to the file"},
                },
                "required": ["path"],
            },
            handler=self.read_file
        )
        
        self.register_action(
            name="write_file",
            description="Write content to a file in the workspace.",
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The absolute or relative path to the file"},
                    "content": {"type": "string", "description": "The content to write to the file"},
                },
                "required": ["path", "content"],
            },
            handler=self.write_file
        )

    async def read_file(self, path: str) -> Dict[str, Any]:
        import os
        from pathlib import Path
        try:
            workspace = Path("/app/workspace") if os.environ.get("PORT") else Path(os.getcwd())
            workspace.mkdir(parents=True, exist_ok=True)
            target = (workspace / path).resolve()
            
            if not target.is_relative_to(workspace):
                return {"path": path, "error": "Access denied. Cannot access files outside workspace."}
            
            if not target.exists():
                return {"path": path, "error": "File not found"}
            with open(target, "r", encoding="utf-8") as f:
                return {"path": str(target), "content": f.read(10000)}
        except Exception as e:
            return {"path": path, "error": str(e)}

    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        import os
        from pathlib import Path
        try:
            workspace = Path("/app/workspace") if os.environ.get("PORT") else Path(os.getcwd())
            workspace.mkdir(parents=True, exist_ok=True)
            target = (workspace / path).resolve()
            
            if not target.is_relative_to(workspace):
                return {"path": path, "error": "Access denied. Cannot write files outside workspace.", "written": False}
                
            os.makedirs(target.parent, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return {"path": str(target), "written": True}
        except Exception as e:
            return {"path": path, "error": str(e), "written": False}
