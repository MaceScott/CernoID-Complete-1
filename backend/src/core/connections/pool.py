from typing import Dict, Optional, Any, TypeVar, Generic
import asyncio
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from ..base import BaseComponent
from ..utils.errors import handle_errors

T = TypeVar('T')

class PoolItem(Generic[T]):
    """Connection pool item"""
    
    def __init__(self, connection: T):
        self.connection = connection
        self.last_used = datetime.utcnow()
        self.in_use = False
        self.created = datetime.utcnow()

class ConnectionPool(BaseComponent, Generic[T]):
    """Generic connection pool"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._pool: Dict[str, PoolItem[T]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Pool configuration
        self._min_size = self.config.get('pool.min_size', 5)
        self._max_size = self.config.get('pool.max_size', 20)
        self._max_idle = self.config.get('pool.max_idle', 300)
        self._max_lifetime = self.config.get('pool.max_lifetime', 3600)
        self._connection_timeout = self.config.get('pool.timeout', 30.0)

    async def initialize(self) -> None:
        """Initialize connection pool"""
        # Create initial connections
        for _ in range(self._min_size):
            await self._create_connection()
            
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(
            self._cleanup_idle_connections()
        )
        self.add_cleanup_task(self._cleanup_task)

    async def cleanup(self) -> None:
        """Cleanup connection pool"""
        # Close all connections
        async with self._lock:
            for item in self._pool.values():
                await self._close_connection(item.connection)
        self._pool.clear()

    @asynccontextmanager
    async def acquire(self) -> T:
        """Acquire connection from pool"""
        connection = await self._acquire_connection()
        try:
            yield connection
        finally:
            await self._release_connection(connection)

    @handle_errors(logger=logging.getLogger('ConnectionPool'))
    async def _acquire_connection(self) -> T:
        """Acquire available connection"""
        async with self._lock:
            # Try to find available connection
            for item in self._pool.values():
                if not item.in_use:
                    item.in_use = True
                    item.last_used = datetime.utcnow()
                    return item.connection
                    
            # Create new connection if pool not full
            if len(self._pool) < self._max_size:
                connection = await self._create_connection()
                return connection
                
            # Wait for available connection
            raise TimeoutError("Connection pool exhausted")

    async def _release_connection(self, connection: T) -> None:
        """Release connection back to pool"""
        async with self._lock:
            for item in self._pool.values():
                if item.connection == connection:
                    item.in_use = False
                    item.last_used = datetime.utcnow()
                    break

    async def _create_connection(self) -> T:
        """Create new connection"""
        connection = await self._connect()
        item = PoolItem(connection)
        self._pool[id(connection)] = item
        return connection

    async def _cleanup_idle_connections(self) -> None:
        """Cleanup idle connections periodically"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                async with self._lock:
                    now = datetime.utcnow()
                    to_remove = []
                    
                    for conn_id, item in self._pool.items():
                        # Remove if idle too long
                        if not item.in_use and \
                           (now - item.last_used).total_seconds() > self._max_idle:
                            to_remove.append(conn_id)
                            
                        # Remove if too old
                        elif (now - item.created).total_seconds() > self._max_lifetime:
                            to_remove.append(conn_id)
                            
                    # Remove connections
                    for conn_id in to_remove:
                        item = self._pool[conn_id]
                        await self._close_connection(item.connection)
                        del self._pool[conn_id]
                        
                    # Create new connections if below minimum
                    while len(self._pool) < self._min_size:
                        await self._create_connection()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Connection cleanup failed: {str(e)}")

    @abstractmethod
    async def _connect(self) -> T:
        """Create new connection - to be implemented by subclasses"""
        pass

    @abstractmethod
    async def _close_connection(self, connection: T) -> None:
        """Close connection - to be implemented by subclasses"""
        pass 