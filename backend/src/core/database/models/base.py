"""
Base model configuration for SQLAlchemy.
Provides common functionality for all models.
"""

from typing import Any, TypeVar, Type, Dict, Optional
from datetime import datetime
from sqlalchemy import MetaData, Column, Integer, DateTime, String, event
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session, validates, DeclarativeMeta
import logging

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

class _Base:
    """Base mixin class with common functionality."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    @validates('created_at', 'updated_at')
    def validate_datetime(self, key: str, value: Optional[datetime]) -> datetime:
        """Validate datetime fields."""
        if value is None:
            value = datetime.utcnow()
        if not isinstance(value, datetime):
            raise ValueError(f"{key} must be a datetime object")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """String representation of model."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    @classmethod
    def get_by_id(cls: Type[ModelType], session: Session, id: int) -> Optional[ModelType]:
        """Get model instance by ID."""
        return session.query(cls).filter(cls.id == id).first()

# Create base with metadata
Base: DeclarativeMeta = declarative_base(
    metadata=metadata,
    cls=_Base,
    constructor=_Base.__init__ if hasattr(_Base, '__init__') else None
)

class BaseModel(Base):
    """Base model with common fields and methods."""
    
    __abstract__ = True

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize model with custom fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"Ignoring unknown attribute {key} for {self.__class__.__name__}")

    @classmethod
    def create(cls: Type[ModelType], session: Session, **kwargs: Any) -> ModelType:
        """Create a new model instance."""
        instance = cls(**kwargs)
        session.add(instance)
        return instance

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model instance from dictionary."""
        return cls(**data)

    def update(self, data: Dict[str, Any]) -> None:
        """Update model with dictionary data."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class MigrationHistory(BaseModel):
    """Track database migrations and their application timestamps."""
    __tablename__ = 'migration_history'

    version = Column(String(50), nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    @validates('version')
    def validate_version(self, key: str, value: str) -> str:
        """Validate version string."""
        if not value:
            raise ValueError("Version cannot be empty")
        return value

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        logger.info(f"Migration version {self.version} applied at {self.applied_at}")

# Set up event listeners for logging
@event.listens_for(Session, 'after_commit')
def after_commit(session: Session) -> None:
    """Log after successful commit."""
    logger.debug("Transaction committed successfully")

@event.listens_for(Session, 'after_rollback')
def after_rollback(session: Session) -> None:
    """Log after rollback."""
    logger.warning("Transaction rolled back")

__all__ = ['Base', 'BaseModel', 'MigrationHistory', 'metadata'] 