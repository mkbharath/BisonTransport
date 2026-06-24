"""Database session factory for async SQLAlchemy."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://orderuser:orderpass@localhost:5432/orderdb",
)

DATABASE_URL_SYNC = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql://orderuser:orderpass@localhost:5432/orderdb",
)

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session. Use as a dependency in FastAPI."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_engine():
    """Create a synchronous engine (used by Alembic migrations)."""
    return create_engine(DATABASE_URL_SYNC, echo=False)
