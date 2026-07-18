"""Unified LLM service with a provider fallback chain.

Providers are tried in priority order so the Brain stays functional even when
the fastest/primary provider is rate-limited or down. All providers are free-tier
compatible (Groq, Gemini, OpenRouter free models, HuggingFace).

Priority order (configurable via the providers list):
    1. Groq        — fastest, OpenAI-compatible, free
    2. Gemini      — high quality, free native REST
    3. OpenRouter   — free-tier models only (no paid/402)
    4. HuggingFace  — last-resort Inference API
"""

from typing import Optional, List, Dict, Any
import httpx

from app.core.config import settings
from app.core.logging import logger


class LLMError(Exception):
    """Raised when all providers in the chain fail."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"LLM error ({status_code}): {message}")


# ── Provider adapters ────────────────────────────────────────────────────────

class _GroqProvider:
    """OpenAI-compatible. Base URL: https://api.groq.com/openai/v1"""

    name = "groq"

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.base_url = settings.GROQ_BASE_URL
        self.fast_model = settings.GROQ_FAST_MODEL
        self.reasoning_model = settings.GROQ_REASONING_MODEL

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def map_model(self, kind: str) -> str:
        return self.reasoning_model if kind == "reasoning" else self.fast_model

    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def payload(self, model: str, messages, temperature, max_tokens, stream) -> dict:
        return {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }


class _GeminiProvider:
    """Native REST. URL: https://generativelanguage.googleapis.com/.../{model}:generateContent?key=..."""

    name = "gemini"

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.fast_model = settings.GEMINI_FAST_MODEL
        self.reasoning_model = settings.GEMINI_REASONING_MODEL

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def map_model(self, kind: str) -> str:
        return self.reasoning_model if kind == "reasoning" else self.fast_model

    def headers(self) -> dict:
        return {"Content-Type": "application/json"}

    def endpoint(self, model: str) -> str:
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
            f":generateContent?key={self.api_key}"
        )

    def payload(self, model, messages, temperature, max_tokens, stream) -> dict:
        # Convert OpenAI-style messages to Gemini content format.
        contents = []
        system_instruction = None
        for m in messages:
            role = m["role"]
            text = m["content"]
            if role == "system":
                system_instruction = {"parts": [{"text": text}]}
                continue
            contents.append({
                "role": "user" if role == "user" else "model",
                "parts": [{"text": text}],
            })
        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Hello"}]}]
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            body["systemInstruction"] = system_instruction
        return body

    def parse(self, data: dict) -> str:
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return data.get("text", "")


class _OpenRouterProvider:
    """OpenAI-compatible. Free models only to avoid 402."""

    name = "openrouter"

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        # Free-tier models only — never hit paid (avoids 402).
        self.fast_model = "google/gemma-4-26b-a4b-it:free"
        self.reasoning_model = "nousresearch/hermes-3-llama-3.1-405b:free"

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def map_model(self, kind: str) -> str:
        return self.reasoning_model if kind == "reasoning" else self.fast_model

    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://brain-agi.app",
            "X-Title": "BrainAGI",
        }

    def endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def payload(self, model, messages, temperature, max_tokens, stream) -> dict:
        return {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }


class _HuggingFaceProvider:
    """Inference API. POST https://api-inference.huggingface.co/models/{model}."""

    name = "huggingface"

    def __init__(self):
        self.api_key = settings.HF_API_KEY
        self.model = settings.HF_MODEL

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def map_model(self, kind: str) -> str:
        return self.model

    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def endpoint(self, model: str) -> str:
        return f"https://api-inference.huggingface.co/models/{model}"

    def payload(self, model, messages, temperature, max_tokens, stream) -> dict:
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        return {
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
        }

    def parse(self, data) -> str:
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "")
        if isinstance(data, dict):
            return data.get("generated_text", "")
        return str(data)


class LLMService:
    """Unified chat service with automatic provider fallback.

    Priority chain: Groq → Gemini → OpenRouter(free) → HuggingFace.
    On 429/402/timeout a provider is skipped and the next is tried.
    """

    def __init__(self):
        self.providers = [
            _GroqProvider(),
            _GeminiProvider(),
            _OpenRouterProvider(),
            _HuggingFaceProvider(),
        ]
        # Only providers with a key are eligible.
        self._active = [p for p in self.providers if p.available]
        logger.info(
            "LLMService initialized with providers: %s",
            [p.name for p in self._active] or ["NONE"],
        )

    # ── Model-type routing ────────────────────────────────────────────────
    def route_task(self, task_description: str, requires_tools: bool = False) -> str:
        """Return a model *type* token ('reasoning' | 'fast') for the task."""
        t = task_description.lower()
        if any(kw in t for kw in [
            "plan", "architect", "complex", "analyze", "strategy",
            "code", "refactor", "debug", "python", "typescript", "react",
        ]):
            return "reasoning"
        if requires_tools or "execute" in t or "tool" in t:
            return "reasoning"
        return "fast"

    # ── Chat with provider fallback ───────────────────────────────────────
    async def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict:
        """Send a chat completion, falling back across providers.

        `model` may be a provider model name (used for the primary attempt) or a
        type token ('reasoning'|'fast'). Returns OpenAI-shaped
        {"choices":[{"message":{"role":"assistant","content":...}}]}.
        """
        if not self._active:
            logger.warning("No LLM provider keys configured — dev mode response")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": (
                            "BrainAGI is running in development mode. "
                            "Configure a free provider key (GROQ_API_KEY, "
                            "GEMINI_API_KEY, etc.) in your .env to enable AI."
                        ),
                    }
                }]
            }

        # Resolve the requested kind/name.
        kind = model if model in ("reasoning", "fast") else "fast"

        last_err = None
        async with httpx.AsyncClient(timeout=120) as client:
            # Primary provider gets the explicit model if a real name was passed.
            ordered = list(self._active)
            for provider in ordered:
                try:
                    mdl = model if (model and model not in ("reasoning", "fast")) \
                        else provider.map_model(kind)
                    ok, content = await self._try_provider(
                        client, provider, mdl, messages,
                        temperature, max_tokens, stream,
                    )
                    if ok:
                        return self._openai_shape(content)
                    # provider signalled retryable failure -> continue
                except httpx.TimeoutException:
                    logger.warning("Provider %s timed out; trying next", provider.name)
                    last_err = LLMError(0, f"{provider.name}: timeout")
                    continue
                except LLMError as e:
                    if e.status_code in (429, 402):
                        logger.warning(
                            "Provider %s unavailable (%d); trying next",
                            provider.name, e.status_code,
                        )
                        last_err = e
                        continue
                    raise  # non-retryable
            if last_err:
                raise last_err
            raise LLMError(0, "All LLM providers failed")

    async def _try_provider(
        self, client, provider, model, messages, temperature, max_tokens, stream,
    ) -> tuple[bool, str]:
        """Attempt one provider. Returns (success, content)."""
        if provider.name == "gemini":
            url = provider.endpoint(model)
            body = provider.payload(model, messages, temperature, max_tokens, stream)
            r = await client.post(url, headers=provider.headers(), json=body)
            if r.status_code == 200:
                return True, provider.parse(r.json())
            raise LLMError(r.status_code, r.text[:300])

        if provider.name == "huggingface":
            url = provider.endpoint(model)
            body = provider.payload(model, messages, temperature, max_tokens, stream)
            r = await client.post(url, headers=provider.headers(), json=body)
            if r.status_code == 200:
                return True, provider.parse(r.json())
            raise LLMError(r.status_code, r.text[:300])

        # OpenAI-compatible (groq, openrouter)
        r = await client.post(
            provider.endpoint(),
            headers=provider.headers(),
            json=provider.payload(model, messages, temperature, max_tokens, stream),
        )
        if r.status_code == 200:
            return True, r.json()["choices"][0]["message"]["content"]
        raise LLMError(r.status_code, r.text[:300])

    @staticmethod
    def _openai_shape(content: str) -> dict:
        return {"choices": [{"message": {"role": "assistant", "content": content}}]}

    # ── Convenience wrappers (kept for call-site compatibility) ───────────
    async def reason(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        result = await self.chat(messages=messages, model="reasoning", temperature=0.3, max_tokens=8192)
        return result["choices"][0]["message"]["content"]

    async def agent_chat(self, messages: list, tools: Optional[list] = None) -> dict:
        """Agent execution uses the reasoning tier (best free model available)."""
        if not self._active:
            return {"choices": [{"message": {"role": "assistant", "content": "Dev mode — no AI."}}]}
        result = await self.chat(messages=messages, model="reasoning", temperature=0.5, max_tokens=8192)
        return result


# Backward-compatible alias so existing imports keep working.
OpenRouterService = LLMService
