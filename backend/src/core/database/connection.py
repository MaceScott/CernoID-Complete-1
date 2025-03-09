"""Database connection pool."""
import asyncio
from typing import Optional, AsyncGenerator, Dict, Any
import asyncpg
from asyncpg.pool import Pool
from contextlib import asynccontextmanager
from fastapi import Depends
import os

from core.logging import get_logger
from core.config import Settings
from core.utils.errors import handle_errors

logger = get_logger(__name__)

class DatabasePool:
    """Database connection pool manager."""
    
    def __init__(self):
        """Initialize database pool."""
        self._pool: Optional[Pool] = None
        self._settings = Settings()
        self._is_connected = False
        self._last_error: Optional[str] = None
        self._stats: Dict[str, Any] = {
            'connections_created': 0,
            'connections_closed': 0,
            'active_connections': 0,
            'failed_connections': 0
        }
        self._in_memory = os.getenv('ENVIRONMENT') == 'development'
    
    @handle_errors
    async def create_pool(self) -> None:
        """Create database connection pool."""
        if self._pool is not None:
            logger.warning("Database pool already exists")
            return
        
        if self._in_memory:
            logger.info("Running in development mode with in-memory storage")
            self._is_connected = True
            return
            
        try:
            self._pool = await asyncpg.create_pool(
                host=self._settings.DB_HOST,
                port=self._settings.DB_PORT,
                user=self._settings.DB_USER,
                password=self._settings.DB_PASSWORD,
                database=self._settings.DB_NAME,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'application_name': 'CernoID',
                    'timezone': 'UTC'
                }
            )
            self._is_connected = True
            self._last_error = None
            self._stats['connections_created'] += 1
            logger.info("Database pool created successfully")
        except Exception as e:
            self._is_connected = False
            self._last_error = str(e)
            self._stats['failed_connections'] += 1
            logger.error(f"Failed to create database pool: {str(e)}")
            if not self._in_memory:
                raise
    
    @handle_errors
    async def close(self) -> None:
        """Close database connection pool."""
        if self._in_memory:
            return
            
        if self._pool is None:
            logger.warning("No database pool to close")
            return
        
        try:
            await self._pool.close()
            self._pool = None
            self._is_connected = False
            self._stats['connections_closed'] += 1
            logger.info("Database pool closed")
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Error closing database pool: {str(e)}")
            raise
    
    @property
    def pool(self) -> Pool:
        """Get database pool."""
        if self._in_memory:
            return None
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        return self._pool
    
    @handle_errors
    async def is_connected(self) -> bool:
        """Check if database is connected and responding."""
        if self._in_memory:
            return True
            
        if self._pool is None:
            return False
            
        try:
            # Try to execute a simple query
            async with self._pool.acquire() as conn:
                await conn.execute('SELECT 1')
            self._is_connected = True
            return True
        except Exception as e:
            self._is_connected = False
            self._last_error = str(e)
            logger.error(f"Database connection check failed: {str(e)}")
            return False
    
    @handle_errors
    async def get_status(self) -> Dict[str, Any]:
        """Get database connection status."""
        if self._in_memory:
            return {
                'is_connected': True,
                'last_error': None,
                'stats': self._stats,
                'pool_size': 0,
                'min_size': 0,
                'max_size': 0,
                'mode': 'in-memory'
            }
            
        is_connected = await self.is_connected()
        
        if self._pool is not None:
            self._stats['active_connections'] = len(self._pool._holders)
        
        return {
            'is_connected': is_connected,
            'last_error': self._last_error,
            'stats': self._stats,
            'pool_size': len(self._pool._holders) if self._pool else 0,
            'min_size': 5,
            'max_size': 20,
            'mode': 'postgres'
        }
    
    @asynccontextmanager
    async def connection(self):
        """Get database connection from pool."""
        if self._in_memory:
            yield None
            return
            
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        
        try:
            async with self._pool.acquire() as conn:
                yield conn
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Error acquiring database connection: {str(e)}")
            raise

# Create global database pool instance
db_pool = DatabasePool()

async def get_db() -> AsyncGenerator[Pool, None]:
    """Get database connection dependency."""
    if not db_pool._in_memory and db_pool._pool is None:
        await db_pool.create_pool()
    yield db_pool.pool 