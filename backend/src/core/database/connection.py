"""
Database connection management module.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class DatabasePool:
    """Database connection pool manager."""
    
    def __init__(self):
        """Initialize the database pool."""
        self._engine: Optional[AsyncEngine] = None
        self._session_factory = None
        self._initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the database pool."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            try:
                # Create engine
                self._engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DB_ECHO,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_timeout=settings.DB_POOL_TIMEOUT,
                    pool_recycle=settings.DB_POOL_RECYCLE,
                    poolclass=AsyncAdaptedQueuePool
                )
                
                # Create session factory
                self._session_factory = sessionmaker(
                    self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False
                )
                
                self._initialized = True
                logger.info("Database pool initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise
                
    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        if not self._initialized:
            await self.initialize()
        return self._session_factory()
        
    async def close(self) -> None:
        """Close the database pool."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("Database pool closed")

# Global database pool instance
db_pool = DatabasePool()

async def get_db() -> AsyncSession:
    """FastAPI dependency for getting database sessions."""
    async with db_pool.get_session() as session:
        try:
            yield session
        finally:
            await session.close() 