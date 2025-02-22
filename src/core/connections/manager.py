from typing import Dict, Optional, Type
from ..base import BaseComponent
from .pool import ConnectionPool
from .redis import RedisPool
from .database import DatabasePool

class ConnectionManager(BaseComponent):
    """Connection manager for all database connections"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._pools: Dict[str, ConnectionPool] = {}
        self._pool_types = {
            'redis': RedisPool,
            'postgres': DatabasePool
        }

    async def initialize(self) -> None:
        """Initialize connection manager"""
        # Initialize configured connections
        connections = self.config.get('connections', {})
        for name, config in connections.items():
            pool_type = config.get('type')
            if pool_type in self._pool_types:
                pool_class = self._pool_types[pool_type]
                pool = pool_class(config)
                await pool.initialize()
                self._pools[name] = pool

    async def cleanup(self) -> None:
        """Cleanup all connections"""
        for pool in self._pools.values():
            await pool.cleanup()
        self._pools.clear()

    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get connection pool by name"""
        return self._pools.get(name)

    def register_pool_type(self,
                          name: str,
                          pool_class: Type[ConnectionPool]) -> None:
        """Register new pool type"""
        self._pool_types[name] = pool_class

    async def create_pool(self,
                         name: str,
                         pool_type: str,
                         config: dict) -> ConnectionPool:
        """Create new connection pool"""
        if name in self._pools:
            raise ValueError(f"Pool {name} already exists")
            
        if pool_type not in self._pool_types:
            raise ValueError(f"Unknown pool type: {pool_type}")
            
        pool_class = self._pool_types[pool_type]
        pool = pool_class(config)
        await pool.initialize()
        self._pools[name] = pool
        return pool 