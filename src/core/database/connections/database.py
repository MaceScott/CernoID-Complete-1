from typing import Optional, Any, Dict
import asyncpg
from asyncpg import Pool, Connection
from ..utils.errors import handle_errors
from .pool import ConnectionPool

class DatabasePool(ConnectionPool[Connection]):
    """PostgreSQL connection pool"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._db_config = {
            'host': self.config.get('database.host', 'localhost'),
            'port': self.config.get('database.port', 5432),
            'user': self.config.get('database.user', 'postgres'),
            'password': self.config.get('database.password', ''),
            'database': self.config.get('database.name', 'postgres'),
            'min_size': self.config.get('database.pool.min_size', 5),
            'max_size': self.config.get('database.pool.max_size', 20)
        }
        self._pool: Optional[Pool] = None

    async def initialize(self) -> None:
        """Initialize database pool"""
        try:
            self._pool = await asyncpg.create_pool(**self._db_config)
            self.logger.info("Database connection pool initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize database connection pool: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup database pool"""
        if self._pool:
            await self._pool.close()
            self.logger.info("Database connection pool closed successfully.")

    @handle_errors(logger=None)
    async def _connect(self) -> Connection:
        """Create new database connection"""
        if not self._pool:
            raise RuntimeError("Database pool not initialized")
        return await self._pool.acquire()

    async def _close_connection(self, connection: Connection) -> None:
        """Release connection back to pool"""
        if self._pool:
            await self._pool.release(connection)

    @handle_errors(logger=None)
    async def execute(self,
                     query: str,
                     *args,
                     timeout: Optional[float] = None) -> str:
        """Execute single query"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    @handle_errors(logger=None)
    async def fetch(self,
                   query: str,
                   *args,
                   timeout: Optional[float] = None) -> list:
        """Fetch all rows"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)

    @handle_errors(logger=None)
    async def fetchrow(self,
                      query: str,
                      *args,
                      timeout: Optional[float] = None) -> Optional[Dict]:
        """Fetch single row"""
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args, timeout=timeout)
            return dict(row) if row else None

    @handle_errors(logger=None)
    async def transaction(self):
        """Start database transaction"""
        conn = await self._connect()
        try:
            tr = conn.transaction()
            await tr.start()
            return conn, tr
        except Exception:
            await self._close_connection(conn)
            raise 