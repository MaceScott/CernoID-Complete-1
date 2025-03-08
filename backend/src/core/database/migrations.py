"""Database connection for migrations."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

def get_sync_engine() -> Engine:
    """Get synchronous database engine for migrations."""
    return create_engine(
        "postgresql://postgres:postgres@db:5432/cernoid",
        pool_pre_ping=True
    )

def get_sync_session():
    """Get synchronous database session for migrations."""
    engine = get_sync_engine()
    Session = sessionmaker(bind=engine)
    return Session() 