"""
Database connection management with connection pooling.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from .service import DatabaseService

# Global database service instance
db_service = DatabaseService()

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session from connection pool.
    To be used as FastAPI dependency.
    """
    async with db_service.session() as session:
        yield session

async def initialize_database():
    """Initialize database on application startup."""
    await db_service.initialize()

async def cleanup_database():
    """Cleanup database connections on application shutdown."""
    await db_service.cleanup() 