"""
Database migrations service.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from ...utils.config import get_settings

def get_sync_engine() -> Engine:
    """Get synchronous database engine for migrations."""
    settings = get_settings()
    return create_engine(
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
        pool_pre_ping=True
    )

def get_sync_session():
    """Get synchronous database session for migrations."""
    engine = get_sync_engine()
    Session = sessionmaker(bind=engine)
    return Session() 