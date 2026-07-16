"""Database engine and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine, text

from app.core.config import settings

async_engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
sync_engine = create_engine(settings.DATABASE_URL_SYNC, echo=settings.DEBUG)

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_pgvector():
    """Verify pgvector extension is available."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        return result.scalar() is not None
