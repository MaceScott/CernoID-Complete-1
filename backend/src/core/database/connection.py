"""Database connection management."""
from typing import Optional, Dict, Any
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from fastapi import Depends
from src.core.logging import get_logger
from src.core.config import settings
from src.core.base import BaseComponent

logger = get_logger(__name__)

class DatabasePool(BaseComponent):
    """Database connection pool manager."""

    def __init__(self) -> None:
        """Initialize database pool."""
        super().__init__()
        self._engine = None

    def _initialize_engine(self) -> None:
        """Initialize database engine with connection pool."""
        try:
            self._engine = create_async_engine(
                settings.database_url,
                echo=settings.sql_debug,
                future=True,
                poolclass=AsyncAdaptedQueuePool,
                pool_pre_ping=True,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
            )
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    @property
    def engine(self):
        """Get database engine instance."""
        if not self._engine:
            self._initialize_engine()
        return self._engine

    def get_session(self) -> AsyncSession:
        """Create new database session."""
        if not self._engine:
            self._initialize_engine()
        return AsyncSession(self._engine, expire_on_commit=False)

    async def dispose(self) -> None:
        """Dispose database engine."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine disposed")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a database query."""
        async with self.get_session() as session:
            result = await session.execute(query, params or {})
            await session.commit()
            return result

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database."""
        async with self.get_session() as session:
            result = await session.execute(query, params or {})
            row = result.fetchone()
            return dict(row) if row else None

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> list[Dict[str, Any]]:
        """Fetch all rows from the database."""
        async with self.get_session() as session:
            result = await session.execute(query, params or {})
            rows = result.fetchall()
            return [dict(row) for row in rows]

    async def execute_many(self, query: str, params_list: list[Dict[str, Any]]) -> None:
        """Execute multiple database queries."""
        async with self.get_session() as session:
            for params in params_list:
                await session.execute(query, params)
            await session.commit()

# Create a global database pool instance
db_pool = DatabasePool()

async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async with db_pool.get_session() as session:
        try:
            yield session
        finally:
            await session.close() 