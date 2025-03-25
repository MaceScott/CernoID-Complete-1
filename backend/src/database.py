from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

class Database:
    def __init__(self, db_url: str):
        self.engine: Optional[AsyncEngine] = None
        self.async_session: Optional[sessionmaker] = None
        self.db_url = db_url

    async def connect(self) -> None:
        """Initialize database connection"""
        self.engine = create_async_engine(
            self.db_url,
            poolclass=NullPool,
            echo=False,
        )
        
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def disconnect(self) -> None:
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.async_session = None

    async def get_session(self) -> AsyncSession:
        """Get a database session"""
        if not self.async_session:
            await self.connect()
        return self.async_session() 