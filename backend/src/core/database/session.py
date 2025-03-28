"""
Database session management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.config.settings import get_settings

from .engine import engine, async_session

settings = get_settings()

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

__all__ = ['get_db'] 