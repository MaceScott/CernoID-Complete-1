"""Database session management module."""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config import settings
from core.logging.base import get_logger

logger = get_logger(__name__)

class DatabaseSession:
    """Database session manager."""
    
    def __init__(self, database_url: str):
        self.logger = get_logger(__name__)
        # Ensure we're using the asyncpg protocol
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        self._database_url = database_url
        self._engine = None
        self._session_factory = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database connection and session factory."""
        try:
            self.logger.info("Initializing database session...")
            
            # Create async engine
            self._engine = create_async_engine(
                self._database_url,
                echo=settings.DB_ECHO,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_recycle=settings.DB_POOL_RECYCLE
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
            self.logger.info("Database session initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database session: {str(e)}")
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """Cleanup database resources."""
        try:
            self.logger.info("Cleaning up database session...")
            
            if self._engine:
                await self._engine.dispose()
                self._engine = None
            
            self._session_factory = None
            self._initialized = False
            
            self.logger.info("Database session cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup database session: {str(e)}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if not self._initialized:
            raise RuntimeError("Database session not initialized")
            
        async with self._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Database session error: {str(e)}")
                raise
            finally:
                await session.close()

    @property
    def is_initialized(self) -> bool:
        """Check if database session is initialized."""
        return self._initialized

    async def create_all(self) -> None:
        """Create all database tables."""
        try:
            self.logger.info("Creating database tables...")
            
            if not self._initialized:
                await self.initialize()
            
            # Import models here to avoid circular imports
            from core.database.models import Base
            
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self.logger.info("Database tables created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {str(e)}")
            raise

# Create singleton instance
db_session = DatabaseSession(settings.DATABASE_URL) 