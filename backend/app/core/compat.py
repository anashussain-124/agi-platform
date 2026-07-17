"""Database backend compatibility shim.
Patches PostgreSQL-specific types to work with SQLite.
Import this BEFORE any model imports when running on non-PostgreSQL backends.
"""
import os
import sys

from sqlalchemy import Uuid as _Uuid, JSON as _JSON
from sqlalchemy.dialects import postgresql as _pg


def _patch_postgresql_types():
    """Replace PostgreSQL-specific types with generic SQLAlchemy equivalents.
    
    - UUID → sqlalchemy.Uuid (works on PG, SQLite, MySQL, etc.)
    - ARRAY → sqlalchemy.JSON (cross-backend array emulation)
    """
    # Store originals in case we need them
    _patch_postgresql_types._original_uuid = _pg.UUID
    _patch_postgresql_types._original_array = _pg.ARRAY
    
    _pg.UUID = _Uuid
    _pg.ARRAY = _JSON


# Auto-patch when running on Vercel or SQLite
_should_patch = (
    os.environ.get("VERCEL_ENV") == "1"
    or os.environ.get("DATABASE_URL", "").startswith("sqlite")
    or any("sqlite" in arg for arg in sys.argv)
    or not os.environ.get("DATABASE_URL")  # defaults to SQLite
)

if _should_patch:
    _patch_postgresql_types()
