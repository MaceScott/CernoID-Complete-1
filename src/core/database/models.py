from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Person(Base):
    """Person model for face recognition"""
    __tablename__ = 'persons'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    face_encodings = relationship("FaceEncoding", back_populates="person")
    access_logs = relationship("AccessLog", back_populates="person")

class FaceEncoding(Base):
    """Face encoding storage"""
    __tablename__ = 'face_encodings'
    
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'))
    encoding_data = Column(String, nullable=False)  # Stored as base64
    created_at = Column(DateTime, default=datetime.utcnow)
    quality_score = Column(Float)
    person = relationship("Person", back_populates="face_encodings")

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