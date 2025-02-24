from sqlalchemy import create_engine
from contextlib import contextmanager

class DatabasePool:
    def __init__(self, url: str, pool_size: int = 20):
        self.engine = create_engine(
            url,
            pool_size=pool_size,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=1800
        )

    @contextmanager
    def get_connection(self):
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close() 