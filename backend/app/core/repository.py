"""Repository pattern — abstracts data access for dual-mode (SQLAlchemy + Supabase).

Each concrete repository inherits from BaseRepository and implements the data access
methods using whichever backend is active (determined once at import time).
"""
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supabase_adapter import supabase_client_from_settings, SupabaseClient
from app.core.logging import logger

# Detect backend mode once at import time
_SUPABASE_CLIENT: Optional[SupabaseClient] = supabase_client_from_settings()


def is_supabase_mode() -> bool:
    """Return True if the app should use Supabase REST API instead of SQLAlchemy."""
    return _SUPABASE_CLIENT is not None


def get_supabase() -> Optional[SupabaseClient]:
    """Return the Supabase client singleton (or None)."""
    return _SUPABASE_CLIENT


class BaseRepository:
    """Base class for all repositories. Holds a reference to the DB session and Supabase client."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.supabase = _SUPABASE_CLIENT
        self.use_supabase = _SUPABASE_CLIENT is not None
