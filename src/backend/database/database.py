from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database.models import Base
from core.config.manager import ConfigManager
from core.error_handling import handle_exceptions

class Database:
    def __init__(self):
        self.config = ConfigManager()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def _create_engine(self):
        return create_engine(
            self.config.get('database.url'),
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )

    @handle_exceptions(logger=db_logger.error)
    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @handle_exceptions(logger=db_logger.error)
    async def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close() 
