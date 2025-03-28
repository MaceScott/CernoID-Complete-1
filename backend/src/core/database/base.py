"""
SQLAlchemy base class for all database models.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from fastapi import Depends

from .engine import engine, async_session

# Create the declarative base
Base = declarative_base()

async def init_db():
    """Initialize the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session using an async context manager."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session as a FastAPI dependency."""
    async with get_session_context() as session:
        yield session

# Dependency for FastAPI endpoints
DatabaseSession = Depends(get_session)

__all__ = ['Base', 'init_db', 'get_session', 'get_session_context', 'DatabaseSession'] 