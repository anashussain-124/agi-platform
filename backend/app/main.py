"""Brain AGI Platform - Main Application Entry Point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import init_db, check_pgvector
from app.api import auth, brain, tasks, memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle."""
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    print(f"  Debug mode: {settings.DEBUG}")

    # Try to init database (will fail gracefully if no DB)
    try:
        await init_db()
        print("  Database tables initialized")
        try:
            has_vector = await check_pgvector()
            print(f"  pgvector: {'available' if has_vector else 'NOT available'}")
        except Exception:
            print("  pgvector: not checked (no DB connection)")
    except Exception as e:
        print(f"  Database init skipped: {e}")
        print("  Run with a PostgreSQL database for full functionality.")

    yield
    print(f"  {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(auth.router)
app.include_router(brain.router)
app.include_router(tasks.router)
app.include_router(memory.router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "auth": "/api/auth",
            "brain": "/api/brain",
            "tasks": "/api/tasks",
            "memory": "/api/memory",
        },
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "uptime": "running",
    }
