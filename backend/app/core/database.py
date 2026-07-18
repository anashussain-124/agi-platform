"""Database engine and session management.
Supports PostgreSQL (production) and SQLite (local/dev).
PostgreSQL: DATABASE_URL env var required. SSL auto-enabled for Supabase.
SQLite: Default fallback when DATABASE_URL is not set.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine, text
from app.core.config import settings


def _build_async_url() -> str:
    """Prepare the async database URL with appropriate SSL settings."""
    url = settings.DATABASE_URL
    # Strip sslmode param from URL since asyncpg handles SSL via connect_args
    import re
    url = re.sub(r'[?&]sslmode=[^&]*', '', url)
    # Clean up any trailing ? left over
    url = url.rstrip('?')
    return url


def _build_connect_args() -> dict:
    """Connection args for async engine — disables prepared stmt cache for Supabase pooler."""
    import ssl as _ssl
    args: dict = {}
    is_supabase = "supabase.co" in settings.DATABASE_URL or "pooler.supabase.com" in settings.DATABASE_URL
    if is_supabase:
        # Create an SSL context that doesn't verify certs (Supabase uses self-signed in pooler)
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        args["ssl"] = ctx
    if "pooler.supabase.com" in settings.DATABASE_URL:
        args["prepared_statement_cache_size"] = 0
        args["statement_cache_size"] = 0
    return args


async_engine = create_async_engine(
    _build_async_url(),
    echo=settings.DEBUG,
    connect_args=_build_connect_args(),
)

# Sync engine for alembic / local scripts — only created if a sync URL is configured
sync_engine = (
    create_engine(settings.DATABASE_URL_SYNC, echo=settings.DEBUG)
    if settings.DATABASE_URL_SYNC
    else None
)

AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncSession:  # type: ignore[misc]
    """Dependency: yields a committed async DB session, rolls back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables defined by models that inherit from Base."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_pgvector() -> bool:
    """Return True if the 'vector' PG extension is available."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        return result.scalar() is not None


async def check_connection() -> dict:
    """Return a dict describing the database connection status. Safe for API exposure."""
    import time

    result = {"type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgres"}
    result["url_prefix"] = settings.DATABASE_URL[:25] + "..."
    try:
        t0 = time.time()
        async with AsyncSessionLocal() as session:
            row = await session.execute(text("SELECT 1 AS ok"))
            val = row.fetchone()
            result["status"] = "connected"
            result["latency_ms"] = round((time.time() - t0) * 1000)
            result["detail"] = dict(val._mapping) if val else None
    except Exception as exc:
        result["status"] = "error"
        result["detail"] = str(exc)[:200]
    return result
