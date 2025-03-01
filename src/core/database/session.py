from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import logging

class DatabaseSession:
    """Database session management"""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=10
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        session: AsyncSession = self.SessionLocal()
        try:
            self.logger.info("Database session created successfully.")
            yield session
        except Exception as e:
            self.logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()
            self.logger.info("Database session closed successfully.")

    async def create_all(self):
        """Create all database tables"""
        from .models.base import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self):
        """Drop all database tables"""
        from .models.base import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all) 