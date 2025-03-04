from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import aiohttp
import asyncpg
import aiomysql
import aioredis
from contextlib import asynccontextmanager

@dataclass
class PoolConfig:
    """Connection pool configuration"""
    pool_type: str  # http, postgres, mysql, redis
    min_size: int = 5
    max_size: int = 20
    max_idle: int = 300  # seconds
    max_lifetime: int = 3600  # seconds
    connection_timeout: float = 30.0
    idle_timeout: float = 60.0
    retry_limit: int = 3
    connection_params: Dict = None

class ConnectionPool:
    """Generic connection pool implementation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('ConnectionPool')
        self._pools: Dict[str, Any] = {}
        self._pool_configs: Dict[str, PoolConfig] = {}
        self._pool_stats: Dict[str, Dict] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize connection pool"""
        try:
            # Start background tasks
            self._cleanup_task = asyncio.create_task(
                self._cleanup_idle_connections()
            )
            self._monitor_task = asyncio.create_task(
                self._monitor_pools()
            )
            
            self.logger.info("Connection pool initialized")
            
        except Exception as e:
            self.logger.error(f"Connection pool initialization failed: {str(e)}")
            raise

    async def create_pool(self,
                         name: str,
                         config: PoolConfig) -> None:
        """Create new connection pool"""
        try:
            if name in self._pools:
                raise ValueError(f"Pool already exists: {name}")
                
            self._pool_configs[name] = config
            
            if config.pool_type == "http":
                pool = await self._create_http_pool(config)
            elif config.pool_type == "postgres":
                pool = await self._create_postgres_pool(config)
            elif config.pool_type == "mysql":
                pool = await self._create_mysql_pool(config)
            elif config.pool_type == "redis":
                pool = await self._create_redis_pool(config)
            else:
                raise ValueError(f"Unsupported pool type: {config.pool_type}")
                
            self._pools[name] = pool
            self._pool_stats[name] = {
                "created_at": datetime.utcnow(),
                "total_connections": 0,
                "active_connections": 0,
                "idle_connections": 0,
                "wait_count": 0,
                "wait_time": 0.0
            }
            
            self.logger.info(f"Created pool: {name}")
            
        except Exception as e:
            self.logger.error(f"Pool creation failed: {str(e)}")
            raise

    @asynccontextmanager
    async def acquire(self,
                     pool_name: str,
                     timeout: Optional[float] = None) -> Any:
        """Acquire connection from pool"""
        start_time = datetime.utcnow()
        connection = None
        
        try:
            pool = self._pools.get(pool_name)
            if not pool:
                raise ValueError(f"Pool not found: {pool_name}")
                
            self._pool_stats[pool_name]["wait_count"] += 1
            
            config = self._pool_configs[pool_name]
            timeout = timeout or config.connection_timeout
            
            if config.pool_type == "http":
                connection = pool
            else:
                connection = await asyncio.wait_for(
                    pool.acquire(),
                    timeout=timeout
                )
                
            self._pool_stats[pool_name]["active_connections"] += 1
            
            yield connection
            
        finally:
            if connection:
                try:
                    if config.pool_type != "http":
                        await pool.release(connection)
                    self._pool_stats[pool_name]["active_connections"] -= 1
                except Exception as e:
                    self.logger.error(f"Connection release failed: {str(e)}")
                    
            end_time = datetime.utcnow()
            self._pool_stats[pool_name]["wait_time"] += \
                (end_time - start_time).total_seconds()

    async def cleanup(self) -> None:
        """Cleanup connection pool resources"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._monitor_task:
                self._monitor_task.cancel()
                
            for name, pool in self._pools.items():
                try:
                    if isinstance(pool, aiohttp.ClientSession):
                        await pool.close()
                    else:
                        await pool.close()
                except Exception as e:
                    self.logger.error(
                        f"Pool cleanup failed for {name}: {str(e)}"
                    )
                    
            self.logger.info("Connection pool cleaned up")
            
        except Exception as e:
            self.logger.error(f"Pool cleanup failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get pool statistics"""
        return {
            name: {
                **stats,
                "config": {
                    "pool_type": config.pool_type,
                    "min_size": config.min_size,
                    "max_size": config.max_size,
                    "max_idle": config.max_idle
                }
            }
            for name, (stats, config) in zip(
                self._pool_stats.items(),
                self._pool_configs.items()
            )
        }

    async def _create_http_pool(self,
                               config: PoolConfig) -> aiohttp.ClientSession:
        """Create HTTP connection pool"""
        timeout = aiohttp.ClientTimeout(
            total=config.connection_timeout
        )
        return aiohttp.ClientSession(
            timeout=timeout,
            **(config.connection_params or {})
        )

    async def _create_postgres_pool(self,
                                  config: PoolConfig) -> asyncpg.Pool:
        """Create PostgreSQL connection pool"""
        return await asyncpg.create_pool(
            min_size=config.min_size,
            max_size=config.max_size,
            max_inactive_connection_lifetime=config.max_idle,
            timeout=config.connection_timeout,
            **(config.connection_params or {})
        )

    async def _create_mysql_pool(self,
                               config: PoolConfig) -> aiomysql.Pool:
        """Create MySQL connection pool"""
        return await aiomysql.create_pool(
            minsize=config.min_size,
            maxsize=config.max_size,
            connect_timeout=config.connection_timeout,
            **(config.connection_params or {})
        )

    async def _create_redis_pool(self,
                               config: PoolConfig) -> aioredis.Redis:
        """Create Redis connection pool"""
        return await aioredis.create_redis_pool(
            timeout=config.connection_timeout,
            minsize=config.min_size,
            maxsize=config.max_size,
            **(config.connection_params or {})
        )

    async def _cleanup_idle_connections(self) -> None:
        """Cleanup idle connections periodically"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                for name, pool in self._pools.items():
                    config = self._pool_configs[name]
                    if isinstance(pool, (asyncpg.Pool, aiomysql.Pool)):
                        # These pools handle idle cleanup internally
                        continue
                        
                    # Custom idle cleanup logic can be added here
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Connection cleanup failed: {str(e)}")

    async def _monitor_pools(self) -> None:
        """Monitor pool statistics"""
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                
                for name, pool in self._pools.items():
                    stats = self._pool_stats[name]
                    
                    if isinstance(pool, asyncpg.Pool):
                        stats.update({
                            "total_connections": len(pool._holders),
                            "idle_connections": len(pool._queue._queue)
                        })
                    elif isinstance(pool, aiomysql.Pool):
                        stats.update({
                            "total_connections": pool.size,
                            "idle_connections": pool.freesize
                        })
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Pool monitoring failed: {str(e)}") 