"""OpenRouter AI service - connects the Brain to multiple AI models."""
from typing import Optional, List, AsyncGenerator
import httpx
import json

from app.core.config import settings


class OpenRouterService:
    """Service for communicating with OpenRouter API."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.default_model = settings.OPENROUTER_MODEL
        self.reasoning_model = settings.OPENROUTER_REASONING_MODEL
        self.agent_model = getattr(settings, "OPENROUTER_AGENT_MODEL", self.default_model)

    def route_task(self, task_description: str, requires_tools: bool = False) -> str:
        """Dynamically select the best model for the task based on heuristics."""
        task_lower = task_description.lower()
        
        # Complex reasoning, planning, or architecture
        if any(kw in task_lower for kw in ["plan", "architect", "complex", "analyze", "strategy"]):
            return self.reasoning_model
            
        # Agent execution / tool use
        if requires_tools or "execute" in task_lower or "tool" in task_lower:
            return self.agent_model
            
        # Coding (if we had a specific coding model)
        if any(kw in task_lower for kw in ["code", "refactor", "debug", "python", "typescript", "react"]):
            # Fallback to reasoning model for code if no coding model is specified
            return self.reasoning_model
            
        # Default lightweight/fast model (chat, summarization, etc)
        return self.default_model

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://brain-agi.app",
            "X-Title": "BrainAGI",
        }

    async def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict:
        """Send a chat completion request to OpenRouter."""
        if not self.api_key:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": (
                            "Brain AGI is running in development mode. "
                            "Please configure OPENROUTER_API_KEY in your .env file "
                            "to enable AI-powered responses."
                        )
                    }
                }]
            }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={
                    "model": model or self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream,
                },
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.text}")

            return response.json()

    async def reason(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Use a stronger reasoning model for complex tasks."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        result = await self.chat(
            messages=messages,
            model=self.reasoning_model,
            temperature=0.3,
            max_tokens=8192,
        )

        return result["choices"][0]["message"]["content"]

    async def agent_chat(
        self,
        messages: list,
        tools: Optional[list] = None,
    ) -> dict:
        """Chat with tool-calling capability for agent use."""
        if not self.api_key:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Development mode - no AI available.",
                    }
                }]
            }

        payload = {
            "model": settings.OPENROUTER_AGENT_MODEL,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 8192,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )

            if response.status_code != 200:
                raise Exception(f"Agent chat error: {response.text}")

            return response.json()

    async def select_model_for_task(self, task_type: str) -> str:
        """Dynamically select the best model for a given task type."""
        model_map = {
            "reasoning": "anthropic/claude-sonnet-4",
            "coding": "anthropic/claude-sonnet-4",
            "writing": "openai/gpt-4o-mini",
            "analysis": "openai/gpt-4o",
            "research": "google/gemini-2.0-flash-001",
            "creative": "anthropic/claude-3.5-haiku",
            "quick": "openai/gpt-4o-mini",
            "planning": "anthropic/claude-sonnet-4",
            "debugging": "openai/gpt-4o",
        }
        return model_map.get(task_type, self.default_model)
