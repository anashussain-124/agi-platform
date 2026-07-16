from typing import Dict, Any, Optional
from app.plugins.base import BasePlugin
import httpx
import base64

class GitHubPlugin(BasePlugin):
    name = "GitHubPlugin"
    description = "Provides capabilities to interact with GitHub repositories."
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.access_token = self.config.get("github_access_token", "")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BrainAGI-Agent"
        }
        if self.access_token:
            headers["Authorization"] = f"token {self.access_token}"
        return headers
        
    def _register_actions(self):
        self.register_action(
            name="get_repo_info",
            description="Get basic information about a GitHub repository.",
            schema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "The repository owner"},
                    "repo": {"type": "string", "description": "The repository name"},
                },
                "required": ["owner", "repo"],
            },
            handler=self.get_repo_info
        )
        
        self.register_action(
            name="get_file_content",
            description="Get the content of a file from a GitHub repository.",
            schema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "The repository owner"},
                    "repo": {"type": "string", "description": "The repository name"},
                    "path": {"type": "string", "description": "The path to the file in the repository"},
                },
                "required": ["owner", "repo", "path"],
            },
            handler=self.get_file_content
        )

    async def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=self._get_headers(),
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": data.get("full_name"),
                    "description": data.get("description"),
                    "stars": data.get("stargazers_count"),
                    "language": data.get("language"),
                    "default_branch": data.get("default_branch")
                }
            return {"error": f"HTTP {response.status_code}: {response.text}"}

    async def get_file_content(self, owner: str, repo: str, path: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers=self._get_headers(),
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("type") == "file" and data.get("encoding") == "base64":
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    return {"path": path, "content": content}
                return {"error": "Path is not a base64 encoded file (might be a directory)"}
            return {"error": f"HTTP {response.status_code}: {response.text}"}
