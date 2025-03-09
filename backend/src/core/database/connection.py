"""Database connection management."""
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from fastapi import Depends
from src.core.logging import get_logger
from src.core.config import settings
from src.core.base import BaseComponent

logger = get_logger(__name__)

class DatabasePool(BaseComponent):
    """Database connection pool manager."""

    def __init__(self) -> None:
        """Initialize database pool."""
        super().__init__()
        self._engine = None
        self._session_factory = None

    def _initialize_engine(self) -> None:
        """Initialize database engine with connection pool."""
        try:
            self._engine = create_engine(
                settings.DATABASE_URL,
                echo=False,
                future=True,
                poolclass=QueuePool,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
            self._session_factory = sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    @property
    def engine(self) -> Engine:
        """Get database engine instance."""
        if not self._engine:
            self._initialize_engine()
        return self._engine

    @contextmanager
    def get_session(self) -> Session:
        """Create new database session."""
        if not self._session_factory:
            self._initialize_engine()
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        """Dispose database engine."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database engine disposed")

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a database query."""
        with self.get_session() as session:
            result = session.execute(query, params or {})
            return result

    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database."""
        with self.get_session() as session:
            result = session.execute(query, params or {})
            row = result.fetchone()
            return dict(row) if row else None

    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> list[Dict[str, Any]]:
        """Fetch all rows from the database."""
        with self.get_session() as session:
            result = session.execute(query, params or {})
            rows = result.fetchall()
            return [dict(row) for row in rows]

    def execute_many(self, query: str, params_list: list[Dict[str, Any]]) -> None:
        """Execute multiple database queries."""
        with self.get_session() as session:
            for params in params_list:
                session.execute(query, params)

# Create a global database pool instance
db_pool = DatabasePool()

def get_db() -> Session:
    """Get database session dependency."""
    with db_pool.get_session() as session:
        yield session 