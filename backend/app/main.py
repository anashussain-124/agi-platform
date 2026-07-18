"""Brain AGI Platform — Main Application Entry Point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.database import init_db, check_pgvector
from app.api import auth, brain, tasks, memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle."""
    logger.info("%s v%s starting...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Debug mode: %s", settings.DEBUG)

    # Try to init database (will fail gracefully if no DB)
    try:
        await init_db()
        logger.info("Database tables initialized")
        try:
            has_vector = await check_pgvector()
            logger.info("pgvector: %s", "available" if has_vector else "NOT available")
        except Exception:
            logger.warning("pgvector: not checked (no DB connection)")
    except Exception as e:
        logger.warning("Database init skipped: %s", e)
        logger.info("Run with a PostgreSQL database for full functionality.")

    yield
    logger.info("%s shutting down...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS — use explicit origins instead of wildcard "*"
_cors_origins = list(settings.CORS_ORIGINS)
if settings.FRONTEND_URL and settings.FRONTEND_URL not in _cors_origins:
    _cors_origins.append(settings.FRONTEND_URL)
if settings.DEBUG:
    # In dev, also allow common local addresses
    for origin in ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]:
        if origin not in _cors_origins:
            _cors_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https://.*|http://localhost:3000",
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


# ──────────────────────────────────────────────────────────
# Debug endpoints — gated behind DEBUG=true
# ──────────────────────────────────────────────────────────
if settings.DEBUG:
    @app.get("/debug/env")
    async def debug_env():
        """Debug endpoint to check env (safe fields only — never reveal secrets)."""
        return {
            "db_type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgres",
            "has_jwt_secret": bool(settings.JWT_SECRET),
            "has_openrouter_key": bool(settings.OPENROUTER_API_KEY),
            "frontend_url": settings.FRONTEND_URL,
            "debug": settings.DEBUG,
            "model": settings.OPENROUTER_MODEL,
        }

    @app.get("/debug/db")
    async def debug_db():
        """Test database connection."""
        from app.core.database import check_connection
        return await check_connection()

    @app.get("/debug/supabase")
    async def debug_supabase():
        """Test Supabase REST API connection."""
        from app.core.supabase_adapter import supabase_client_from_settings
        client = supabase_client_from_settings()
        if not client:
            return {"status": "no_config", "detail": "SUPABASE_URL or SUPABASE_SERVICE_KEY not set"}
        try:
            ok = await client.ping()
            return {"status": "ok" if ok else "fail", "detail": "Connected and authenticated" if ok else "Ping failed"}
        except Exception as e:
            return {"status": "error", "detail": str(e)[:200]}

    @app.get("/debug/openrouter")
    async def debug_openrouter():
        """Test OpenRouter API key directly."""
        import httpx

        key = settings.OPENROUTER_API_KEY
        result = {
            "has_key": bool(key),
            "key_prefix": (key[:10] + "...") if key else "none",
            "key_length": len(key) if key else 0,
        }

        if key:
            try:
                r = httpx.get(
                    "https://openrouter.ai/api/v1/auth/key",
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=10,
                )
                result["openrouter_status"] = r.status_code
                result["openrouter_response"] = r.text[:200]
            except Exception as e:
                result["error"] = str(e)[:200]

        return result

    @app.get("/debug/token")
    async def debug_token(token: str = ""):
        """Test JWT token decoding. Pass ?token=... to test a specific token."""
        from app.core.security import decode_access_token_debug, create_access_token
        if not token:
            t = create_access_token({"sub": "test-user-id"})
            return {"generated_preview": t[:40] + "...", "length": len(t)}
        return {"result": decode_access_token_debug(token)}
