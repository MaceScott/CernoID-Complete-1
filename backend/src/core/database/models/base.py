"""
Base model configuration for SQLAlchemy.
Provides common functionality for all models.
"""

from typing import Any, TypeVar, Type, Dict, Optional
from datetime import datetime
from sqlalchemy import MetaData, Column, Integer, DateTime, String, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, validates, DeclarativeMeta
import logging
from src.core.database.base import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variables for better type hints
ModelType = TypeVar("ModelType", bound="BaseModel")

# Naming convention for constraints and indexes
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=convention)

# Update Base metadata
Base.metadata = metadata

class BaseModel(Base):
    """Base model with common fields and methods."""
    
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @declared_attr
    def __tablename__(cls):
        """Generate __tablename__ automatically."""
        return cls.__name__.lower()

    def __init__(self, **kwargs: Any) -> None:
        """Initialize model with given attributes."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create(cls: Type[ModelType], session: Session, **kwargs: Any) -> ModelType:
        """Create a new model instance and add it to the session."""
        instance = cls(**kwargs)
        session.add(instance)
        session.commit()
        return instance

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create a model instance from a dictionary."""
        return cls(**data)

    def update(self, data: Dict[str, Any]) -> None:
        """Update model attributes from a dictionary."""
        for key, value in data.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    @classmethod
    def get_by_id(cls: Type[ModelType], session: Session, id: int) -> Optional[ModelType]:
        """Get model instance by ID."""
        return session.query(cls).filter(cls.id == id).first()

class MigrationHistory(BaseModel):
    """Track database migrations and their application timestamps."""
    __tablename__ = 'migration_history'

    version = Column(String(50), nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    @validates('version')
    def validate_version(self, key: str, value: str) -> str:
        """Validate migration version format."""
        if not value or not value.strip():
            raise ValueError("Version cannot be empty")
        return value.strip()

    def __init__(self, **kwargs: Any) -> None:
        """Initialize migration history."""
        super().__init__(**kwargs)

@event.listens_for(Session, 'after_commit')
def after_commit(session: Session) -> None:
    """Log successful commits."""
    logger.info("Transaction committed successfully")

@event.listens_for(Session, 'after_rollback')
def after_rollback(session: Session) -> None:
    """Log transaction rollbacks."""
    logger.warning("Transaction rolled back")

__all__ = ['Base', 'BaseModel', 'MigrationHistory', 'metadata'] 