from typing import Dict, Any, Optional
from app.plugins.base import BasePlugin
import httpx

class WebsitePlugin(BasePlugin):
    name = "WebsitePlugin"
    description = "Analyze websites, extract text, and check basic SEO."
    
    def _register_actions(self):
        self.register_action(
            name="analyze_url",
            description="Fetch a URL and extract its text content, title, and meta description.",
            schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to analyze (e.g. https://example.com)"},
                },
                "required": ["url"],
            },
            handler=self.analyze_url
        )

    async def analyze_url(self, url: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, timeout=15.0)
                if response.status_code != 200:
                    return {"url": url, "error": f"HTTP {response.status_code}"}
                    
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                title = soup.title.string if soup.title else "No Title"
                meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
                meta_desc = meta_desc_tag['content'] if meta_desc_tag else "No Description"
                
                # Extract text, remove scripts and styles
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text(separator=' ', strip=True)
                
                # Limit text to roughly 4000 tokens for context window safety
                text_preview = text[:15000]
                
                return {
                    "url": url,
                    "title": title,
                    "meta_description": meta_desc,
                    "content": text_preview
                }
        except Exception as e:
            return {"url": url, "error": str(e)}
