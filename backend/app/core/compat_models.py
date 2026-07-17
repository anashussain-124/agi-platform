"""Convert Supabase REST API dict responses to attribute-access objects compatible with SQLAlchemy model usage."""
from types import SimpleNamespace


def row_to_obj(row: dict) -> SimpleNamespace:
    """Convert a Supabase REST API response dict to an object with attribute access.

    In SQLAlchemy the endpoints access e.g. user.id, brain.name, brain.status.value.
    This wrapper preserves that pattern when the backend is Supabase REST API.
    """
    return SimpleNamespace(**{k: _maybe_wrap(v) for k, v in row.items()})


def _maybe_wrap(val):
    """If val is a dict with an expected `.value` pattern (like enums), wrap it."""
    if isinstance(val, str) and val.isupper() and "_" not in val:
        # Looks like an enum string — wrap so .value works
        return SimpleNamespace(value=val)
    return val
