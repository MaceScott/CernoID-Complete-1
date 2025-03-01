from typing import List, Dict, Optional
import asyncpg
from asyncpg import Pool
from core.error_handling import handle_exceptions
from core.config.manager import ConfigManager

class OptimizedDatabase:
    def __init__(self):
        self.config = ConfigManager()
        self.pool: Optional[Pool] = None
        self._setup_indexes()

    async def initialize(self):
        try:
            self.pool = await asyncpg.create_pool(
                self.config.get('database.url'),
                min_size=5,
                max_size=20,
                command_timeout=60,
                max_queries=50000,
                max_cached_statement_lifetime=300,
                max_keepalive_idle=300
            )
            db_logger.info("Database connection pool initialized successfully.")
        except Exception as e:
            db_logger.error(f"Failed to initialize database connection pool: {str(e)}")
            raise

    @handle_exceptions(logger=db_logger.error)
    async def _setup_indexes(self):
        async with self.pool.acquire() as conn:
            # Create optimized indexes
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_face_encodings_user_id 
                ON face_encodings(user_id);
                
                CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp 
                ON access_logs(timestamp DESC);
                
                CREATE INDEX IF NOT EXISTS idx_security_events_type_timestamp 
                ON security_events(event_type, timestamp DESC);
                
                CREATE INDEX IF NOT EXISTS idx_users_face_encoding 
                ON users USING GIST (face_encoding gist_face_ops);
            ''')

    async def get_face_matches(self, encoding: bytes, threshold: float = 0.6) -> List[Dict]:
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT user_id, similarity(face_encoding, $1) as confidence
                FROM users
                WHERE similarity(face_encoding, $1) > $2
                ORDER BY confidence DESC
                LIMIT 5
            ''', encoding, threshold)

    async def batch_insert_events(self, events: List[Dict]):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany('''
                    INSERT INTO security_events 
                    (event_type, timestamp, data)
                    VALUES ($1, $2, $3)
                ''', [(e['type'], e['timestamp'], e['data']) for e in events])

    @handle_exceptions(logger=db_logger.error)
    async def get_user_access_history(self, user_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT al.*, z.name as zone_name
                FROM access_logs al
                JOIN security_zones z ON al.zone_id = z.id
                WHERE al.user_id = $1
                ORDER BY al.timestamp DESC
                LIMIT 100
            ''', user_id) 
