from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, String
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MigrationHistory(BaseModel):
    """Track database migrations"""
    __tablename__ = 'migration_history'

    version = Column(String(50), nullable=False)
    applied_at = Column(DateTime, nullable=False) 