from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, String
from datetime import datetime
import logging

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields for all database models."""
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.info(f"Initialized model {self.__class__.__name__} with ID {self.id}")

class MigrationHistory(BaseModel):
    """Track database migrations and their application timestamps."""
    __tablename__ = 'migration_history'

    version = Column(String(50), nullable=False)
    applied_at = Column(DateTime, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.info(f"Migration version {self.version} applied at {self.applied_at}") 