from typing import Optional, Any
import aioredis
from aioredis import Redis
from ..utils.errors import handle_errors
from .pool import ConnectionPool, T

class RedisPool(ConnectionPool[Redis]):
    """Redis connection pool"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._redis_url = self.config.get(
            'redis.url',
            'redis://localhost:6379'
        )
        self._db = self.config.get('redis.db', 0)
        self._password = self.config.get('redis.password')
        self._encoding = self.config.get('redis.encoding', 'utf-8')

    @handle_errors(logger=None)  # Logger set by parent class
    async def _connect(self) -> Redis:
        """Create new Redis connection"""
        return await aioredis.from_url(
            self._redis_url,
            db=self._db,
            password=self._password,
            encoding=self._encoding,
            decode_responses=True
        )

    async def _close_connection(self, connection: Redis) -> None:
        """Close Redis connection"""
        await connection.close()

    @handle_errors(logger=None)
    async def execute(self,
                     command: str,
                     *args,
                     **kwargs) -> Any:
        """Execute Redis command"""
        async with self.acquire() as redis:
            return await getattr(redis, command)(*args, **kwargs)

    @handle_errors(logger=None)
    async def pipeline(self, commands: list) -> list:
        """Execute multiple commands in pipeline"""
        async with self.acquire() as redis:
            pipe = redis.pipeline()
            for cmd, *args in commands:
                getattr(pipe, cmd)(*args)
            return await pipe.execute() 