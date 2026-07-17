"""Vercel serverless entry point for the BrainAGI FastAPI backend.
Imports the compat shim first to patch PostgreSQL types for SQLite compatibility.
"""
# Apply PostgreSQL→SQLite type patches before any model imports
from app.core import compat  # noqa: F401

from app.main import app as _app

# Vercel Python runtime requires 'app' at module level
app = _app
