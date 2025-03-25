from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from ..config import settings
from ..logging.base import get_logger

logger = get_logger(__name__)

class DatabaseConnection:
    """Database connection manager implemented as a singleton."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
            self._initializing = False
            self.engine: Optional[AsyncEngine] = None
            self.async_session: Optional[sessionmaker] = None
            self.db_url = None
            self.logger = logger

    async def initialize(self) -> None:
        """Initialize database connection."""
        if self._initialized:
            self.logger.info("Database already initialized")
            return
            
        if self._initializing:
            self.logger.info("Database initialization already in progress")
            return
            
        try:
            self._initializing = True
            
            # Get database URL from settings
            self.db_url = settings.DATABASE_URL
            
            # Create engine
            self.engine = create_async_engine(
                self.db_url,
                poolclass=NullPool,
                echo=False,
            )
            
            # Create session factory
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            
            self._initialized = True
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
        finally:
            self._initializing = False

    async def cleanup(self) -> None:
        """Clean up database resources."""
        if not self._initialized:
            return
            
        try:
            if self.engine:
                await self.engine.dispose()
                self.engine = None
                self.async_session = None
            self._initialized = False
            self.logger.info("Database cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Failed to clean up database: {e}")
            raise

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        if not self._initialized:
            await self.initialize()
        return self.async_session()
        
    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._initialized

    async def is_connected(self) -> bool:
        """Check database connection."""
        if not self._initialized:
            return False
            
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception:
            return False

# Create singleton instance
db_pool = DatabaseConnection()

async def get_db() -> AsyncSession:
    """FastAPI dependency for getting database sessions."""
    async with db_pool.get_session() as session:
        try:
            yield session
        finally:
            await session.close() 