"""Supabase REST API adapter — replaces SQLAlchemy for Vercel deployments.
Uses httpx to call Supabase's PostgREST API over HTTPS (port 443, IPv4-compatible).
"""
from typing import Any, Optional
import httpx


class SupabaseClient:
    """Thin client over Supabase REST API (PostgREST)."""

    _ENUM_VALUES = {"high","medium","low","critical","pending","in_progress",
                    "completed","failed","cancelled","blocked","active",
                    "creating","sleeping","paused","free","pro","admin",
                    "working","episodic","semantic","procedural","knowledge","project"}

    def __init__(self, url: str, service_key: str):
        self._base = f"{url.rstrip('/')}/rest/v1"
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "return=representation",
        }

    @staticmethod
    def _normalize(val: Any) -> Any:
        """Uppercase enum-like strings for Supabase."""
        if isinstance(val, str) and val.lower() in SupabaseClient._ENUM_VALUES:
            return val.upper()
        return val

    async def get(self, table: str, filters: dict | None = None,
                  columns: str | None = None, single: bool = False,
                  order: str | None = None, limit: int = 100) -> list[dict]:
        """Select rows. filters {'col': val} — exact match via eq."""
        params = {"select": columns or "*", "limit": str(limit)}
        if filters:
            for col, val in filters.items():
                params[col] = f"eq.{self._normalize(val)}"
        if order:
            params["order"] = order
        if single:
            params["limit"] = "1"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self._base}/{table}", headers=self._headers, params=params)
            r.raise_for_status()
            data = r.json()
            return data[0] if single and data else data

    async def create(self, table: str, data: dict) -> dict:
        """Insert a row and return the created record."""
        import uuid
        from datetime import datetime, timezone

        payload = {k: self._normalize(v) for k, v in data.items()}
        if "id" not in payload:
            payload["id"] = str(uuid.uuid4())
        if "created_at" not in payload:
            payload["created_at"] = datetime.now(timezone.utc).isoformat()
        # updated_at for tables known to have it
        _has_ts = {"users","brains","conversations","tasks","goals","automations",
                   "documents","document_chunks","learning_entries","memory_entries",
                   "api_keys","user_sessions","brain_modules"}
        if table in _has_ts and "updated_at" not in payload:
            payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        # Table-specific required defaults
        if table == "users":
            payload.setdefault("is_mfa_enabled", False)
        elif table == "brains":
            payload.setdefault("preferences", {}); payload.setdefault("coding_style", {})
            payload.setdefault("communication_style", "balanced")
            payload.setdefault("total_conversations", 0); payload.setdefault("total_memories", 0)
            payload.setdefault("total_tasks", 0); payload.setdefault("uptime_hours", 0)
            payload.setdefault("auto_learn", True); payload.setdefault("auto_index", True)
            payload.setdefault("require_approval_deploy", True)
            payload.setdefault("require_approval_write", False)
        elif table in ("conversations", "messages"):
            payload.setdefault("metadata", {}); payload.setdefault("token_count", 0)
        if table == "conversations":
            payload.setdefault("is_archived", False); payload.setdefault("summary", None)
        elif table == "goals":
            payload.setdefault("progress", 0)
        elif table == "tasks":
            payload.setdefault("current_step", 0)
            payload.setdefault("total_steps", 0)
            payload.setdefault("plan", {})
            payload.setdefault("result", {})
        elif table == "memory_entries":
            payload.setdefault("summary", None)
            payload.setdefault("access_count", 0)
            payload.setdefault("tags", {})
            payload.setdefault("is_shared", False)

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{self._base}/{table}", headers=self._headers, json=payload)
            if r.status_code >= 400:
                raise Exception(f"Supabase POST {table} {r.status_code}: {r.text[:200]}")
            rows = r.json()
            return rows[0] if rows else data

    async def update(self, table: str, filters: dict, data: dict) -> list[dict]:
        """Update rows matching filters. Returns updated rows."""
        payload = {k: self._normalize(v) for k, v in data.items()}
        params = {col: f"eq.{self._normalize(val)}" for col, val in filters.items()}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.patch(f"{self._base}/{table}", headers=self._headers, params=params, json=payload)
            r.raise_for_status()
            return r.json()

    async def delete(self, table: str, filters: dict) -> list[dict]:
        """Delete rows matching filters. Returns deleted rows."""
        params = {col: f"eq.{self._normalize(val)}" for col, val in filters.items()}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.delete(f"{self._base}/{table}", headers=self._headers, params=params)
            r.raise_for_status()
            return r.json()

    async def ping(self) -> bool:
        try:
            await self.get("users", limit=1)
            return True
        except Exception:
            return False


def supabase_client_from_settings():
    from app.core.config import settings
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
        return SupabaseClient(str(settings.SUPABASE_URL), str(settings.SUPABASE_SERVICE_KEY))
    return None
