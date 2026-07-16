from typing import Dict, Any
from app.plugins.base import BasePlugin

class WebPlugin(BasePlugin):
    name = "WebPlugin"
    description = "Provides web searching and scraping capabilities."
    
    def _register_actions(self):
        self.register_action(
            name="search",
            description="Search the web for current information.",
            schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                },
                "required": ["query"],
            },
            handler=self.search
        )

    async def search(self, query: str) -> Dict[str, Any]:
        import httpx
        try:
            # Simple DuckDuckGo HTML search for demonstration 
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://html.duckduckgo.com/html/?q={query}", timeout=10.0)
                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = []
                    for a in soup.find_all('a', class_='result__snippet'):
                        results.append(a.text)
                    return {"query": query, "results": results[:5]}
                return {"query": query, "results": [], "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"query": query, "results": [], "error": str(e)}
