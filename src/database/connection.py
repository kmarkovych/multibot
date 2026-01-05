"""Database connection management using asyncpg."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._pool: asyncpg.Pool | None = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the SQLAlchemy async engine."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self._session_factory

    @property
    def pool(self) -> asyncpg.Pool:
        """Get the raw asyncpg pool for direct queries."""
        if self._pool is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self._pool

    async def connect(self) -> None:
        """Initialize database connections."""
        logger.info("Connecting to database...")

        # Create SQLAlchemy async engine
        # Convert postgresql:// to postgresql+asyncpg://
        url = self.config.url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self._engine = create_async_engine(
            url,
            pool_size=self.config.pool_size,
            max_overflow=self.config.pool_max_overflow,
            pool_recycle=self.config.pool_recycle,
            pool_timeout=self.config.pool_timeout,
            echo=False,
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        # Also create a raw asyncpg pool for direct queries if needed
        # Parse connection string for asyncpg
        # asyncpg uses postgresql:// not postgresql+asyncpg://
        asyncpg_url = self.config.url
        self._pool = await asyncpg.create_pool(
            asyncpg_url,
            min_size=2,
            max_size=self.config.pool_size,
            max_inactive_connection_lifetime=self.config.pool_recycle,
        )

        logger.info("Database connection established")

    async def disconnect(self) -> None:
        """Close all database connections."""
        logger.info("Disconnecting from database...")

        if self._pool:
            await self._pool.close()
            self._pool = None

        if self._engine:
            await self._engine.dispose()
            self._engine = None

        self._session_factory = None
        logger.info("Database disconnected")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session context manager."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
