"""OpenRouter AI service - connects the Brain to multiple AI models."""
from typing import Optional, List
import httpx

from app.core.config import settings
from app.core.logging import logger


class OpenRouterError(Exception):
    """Raised when the OpenRouter API returns an error."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"OpenRouter API error ({status_code}): {message}")


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

        # Coding tasks
        if any(kw in task_lower for kw in ["code", "refactor", "debug", "python", "typescript", "react"]):
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
        """Send a chat completion request to OpenRouter.

        Automatically retries across a fanout of reliable models if the primary
        model is rate-limited (429) or times out, so the Brain stays functional
        even when a free upstream model is throttled.
        """
        if not self.api_key:
            logger.warning("No OPENROUTER_API_KEY configured — returning dev mode response")
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

        primary = model or self.default_model
        # Fanout order: prefer free-tier models first (no credits needed), then
        # progressively more capable paid models as fallbacks. This keeps the Brain
        # functional on a free/zero-credit OpenRouter account as much as possible.
        fallbacks = [
            "google/gemma-4-26b-a4b-it:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-haiku",
            "google/gemini-flash-1.5",
        ]
        candidates = [primary] + [m for m in fallbacks if m != primary]

        last_err = None
        async with httpx.AsyncClient(timeout=120) as client:
            for attempt_model in candidates:
                try:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json={
                            "model": attempt_model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "stream": stream,
                        },
                    )
                    if response.status_code == 200:
                        return response.json()
                    if response.status_code in (429, 402):
                        # 429 = rate-limited, 402 = insufficient credits on this model.
                        # Either way, try the next candidate model.
                        logger.warning("Model %s unavailable (%d); trying fallback", attempt_model, response.status_code)
                        last_err = OpenRouterError(response.status_code, f"{attempt_model}: {response.status_code}")
                        continue
                    # Non-retryable error
                    raise OpenRouterError(response.status_code, response.text[:300])
                except httpx.TimeoutException as te:
                    logger.warning("Model %s timed out; trying fallback", attempt_model)
                    last_err = te
                    continue
            # All candidates failed
            if last_err:
                # Surface a clear, actionable message (e.g. insufficient credits).
                if isinstance(last_err, OpenRouterError) and last_err.status_code == 402:
                    raise OpenRouterError(
                        402,
                        "OpenRouter account has insufficient credits. Add credits at "
                        "https://openrouter.ai/settings/credits to enable agent execution.",
                    )
                raise last_err
            raise OpenRouterError(0, "All candidate models failed")

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
                        "content": "Development mode — no AI available.",
                    }
                }]
            }

        payload = {
            "model": self.agent_model,
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
                raise OpenRouterError(response.status_code, response.text[:300])

            return response.json()
