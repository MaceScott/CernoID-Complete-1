"""
Database service package.
Contains Data Access Objects (DAOs) and other database-related services.
"""

from typing import Optional, Dict, Any
from ..connection import DatabaseConnection
from ...utils.logging import get_logger
from ...utils.config import get_settings
from ...utils.decorators import handle_errors

logger = get_logger(__name__)

class DatabaseService:
    """High-level database service for managing database operations."""
    
    def __init__(self):
        """Initialize database service."""
        self._pool = DatabaseConnection(get_settings().DATABASE_URL)
        self._settings = get_settings()
        self._is_initialized = False
    
    @handle_errors
    async def initialize(self) -> None:
        """Initialize database connection and run migrations."""
        if self._is_initialized:
            logger.warning("Database service already initialized")
            return
            
        await self._pool.connect()
        self._is_initialized = True
        logger.info("Database service initialized successfully")
    
    @handle_errors
    async def close(self) -> None:
        """Close database connections."""
        if not self._is_initialized:
            logger.warning("Database service not initialized")
            return
            
        await self._pool.disconnect()
        self._is_initialized = False
        logger.info("Database service closed successfully")
    
    @handle_errors
    async def get_status(self) -> Dict[str, Any]:
        """Get database status information."""
        if not self._is_initialized:
            return {"status": "not_initialized"}
            
        return {"status": "connected" if self._pool.engine else "disconnected"}
    
    @property
    def pool(self) -> DatabaseConnection:
        """Get database pool."""
        return self._pool
    
    @property
    def is_initialized(self) -> bool:
        """Check if database service is initialized."""
        return self._is_initialized

from .dao import BaseDAO
from .user import UserService
from .connection import DatabasePool, get_db
from .migrations import get_sync_engine, get_sync_session

__all__ = [
    'BaseDAO',
    'UserService',
    'DatabasePool',
    'get_db',
    'get_sync_engine',
    'get_sync_session',
    'DatabaseService'
] 