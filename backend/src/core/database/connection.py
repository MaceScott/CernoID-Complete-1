"""Database connection management."""
from typing import Optional, Dict, Any
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from core.logging import get_logger
from core.config import config
from core.base import BaseComponent

logger = get_logger(__name__)

class DatabasePool(BaseComponent):
    """Manages database connection pool."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._engine = None
        self._session_factory = None
        self._pool_size = config.get('database.pool_size', 5)
        self._max_overflow = config.get('database.max_overflow', 10)

    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        try:
            database_url = config.get('database.url')
            if not database_url:
                raise ValueError("Database URL not configured")

            self._engine = create_async_engine(
                database_url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                echo=config.get('database.echo', False)
            )

            self._session_factory = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Clean up database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connections cleaned up")

    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if not self._session_factory:
            raise RuntimeError("Database pool not initialized")
        return self._session_factory()

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