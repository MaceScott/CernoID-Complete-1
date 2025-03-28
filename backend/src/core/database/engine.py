"""
SQLAlchemy engine initialization and session management.
"""

import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config.settings import get_settings

settings = get_settings()

# Create database directory for SQLite if needed
if settings.DATABASE_URL.startswith('sqlite') and not settings.TESTING:
    db_path = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
    if not db_path.parent.exists() and str(db_path) != ':memory:':
        db_path.parent.mkdir(parents=True)

# Determine the correct database URL based on the driver
database_url = settings.DATABASE_URL
if settings.DATABASE_URL.startswith('postgresql') and '+asyncpg' not in settings.DATABASE_URL:
    # Replace psycopg2 with asyncpg for PostgreSQL
    database_url = settings.DATABASE_URL.replace('postgresql', 'postgresql+asyncpg')
elif settings.DATABASE_URL.startswith('sqlite') and '+aiosqlite' not in settings.DATABASE_URL:
    # Replace sqlite with aiosqlite
    database_url = settings.DATABASE_URL.replace('sqlite', 'sqlite+aiosqlite')

# Configure engine arguments based on environment
engine_args = {
    'echo': settings.DB_ECHO,
}

if not settings.DATABASE_URL.startswith('sqlite'):
    engine_args.update({
        'pool_size': settings.DB_POOL_SIZE,
        'max_overflow': settings.DB_MAX_OVERFLOW,
        'pool_timeout': settings.DB_POOL_TIMEOUT,
        'pool_recycle': settings.DB_POOL_RECYCLE,
    })
else:
    engine_args['poolclass'] = NullPool

# Create the async engine
engine = create_async_engine(
    database_url,
    **engine_args
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Disable autoflush for better control in tests
)

__all__ = ['engine', 'async_session'] 