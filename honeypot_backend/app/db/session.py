"""
Async database engine and session management.

Provides:
- ``create_engine_and_session`` — build an ``AsyncEngine`` + ``async_sessionmaker``
- ``dispose_engine``            — gracefully close the engine pool
- ``get_db``                    — FastAPI dependency yielding an ``AsyncSession``
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level references (populated on first call to create_engine_and_session)
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine_and_session(
    settings: Settings,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create and return an async engine and session factory.

    Args:
        settings: Application settings containing ``DATABASE_URL``,
                  ``DB_POOL_SIZE``, and ``DB_MAX_OVERFLOW``.

    Returns:
        A ``(AsyncEngine, async_sessionmaker)`` tuple.
    """
    global _engine, _async_session_factory  # noqa: PLW0603

    _engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

    _async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info(
        "Async engine created",
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
    )

    return _engine, _async_session_factory


async def dispose_engine(engine: AsyncEngine) -> None:
    """Dispose of the async engine, closing all pooled connections.

    Args:
        engine: The ``AsyncEngine`` to dispose.
    """
    await engine.dispose()
    logger.info("Database engine disposed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an ``AsyncSession``.

    Usage::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...

    Raises:
        RuntimeError: If the session factory has not been initialised yet
            (i.e. ``create_engine_and_session`` was never called).
    """
    if _async_session_factory is None:
        raise RuntimeError(
            "Database session factory not initialised. "
            "Call create_engine_and_session() during application startup."
        )

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
