from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    face_encodings = relationship("FaceEncoding", back_populates="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime)
    metadata = Column(JSON)

class FaceEncoding(Base):
    """Face encoding storage"""
    __tablename__ = 'face_encodings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    encoding = Column(JSON, nullable=False)  # Store as JSON array
    quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)
    user = relationship("User", back_populates="face_encodings")

class AccessLog(Base):
    """Access logging for security"""
    __tablename__ = 'access_logs'
    
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    camera_id = Column(String(50))
    confidence_score = Column(Float)
    access_granted = Column(Boolean)
    person = relationship("Person", back_populates="access_logs")

# Additional models to be implemented:
# - EventLog
# - SystemSettings
# - Camera
# - Alert
# - AccessControl 