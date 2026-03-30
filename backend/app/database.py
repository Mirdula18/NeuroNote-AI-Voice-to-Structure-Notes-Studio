"""NeuroNote AI - Database Setup"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create all database tables."""
    from app.models import note  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_used_fallback_column(conn)


async def get_db() -> AsyncSession:
    """Dependency for getting DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def _ensure_used_fallback_column(conn):
    """Add used_fallback column if missing (SQLite-safe)."""
    result = await conn.execute(text("PRAGMA table_info(notes)"))
    columns = {row[1] for row in result.fetchall()}
    if "used_fallback" not in columns:
        await conn.execute(text("ALTER TABLE notes ADD COLUMN used_fallback BOOLEAN DEFAULT 0"))
