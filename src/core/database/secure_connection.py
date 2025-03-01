from typing import Optional
import ssl
from asyncpg import create_pool
from asyncpg.pool import Pool
from core.error_handling import handle_exceptions

class SecureDatabase:
    def __init__(self):
        self.pool: Optional[Pool] = None
        self.ssl_context = self._create_ssl_context()

    def _create_ssl_context(self) -> ssl.SSLContext:
        try:
            ssl_context = ssl.create_default_context(
                purpose=ssl.Purpose.SERVER_AUTH,
                cafile=self.config.get('database.ca_cert')
            )
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            # Client certificate authentication
            ssl_context.load_cert_chain(
                certfile=self.config.get('database.client_cert'),
                keyfile=self.config.get('database.client_key')
            )
            
            db_logger.info("SSL context created successfully.")
            return ssl_context
        except Exception as e:
            db_logger.error(f"Failed to create SSL context: {str(e)}")
            raise

    @handle_exceptions(logger=db_logger.error)
    async def initialize(self):
        self.pool = await create_pool(
            self.config.get('database.url'),
            ssl=self.ssl_context,
            max_size=20,
            min_size=5,
            statement_cache_size=0,  # Disable statement cache for security
            max_cached_statement_lifetime=0,
            command_timeout=60
        )

    async def execute_query(self, query: str, *args, timeout: Optional[float] = None):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await conn.fetch(query, *args, timeout=timeout)

    async def close(self):
        if self.pool:
            await self.pool.close()
