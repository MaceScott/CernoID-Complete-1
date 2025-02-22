from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    face_encodings = relationship("FaceEncoding", back_populates="user")
    permissions = relationship("Permission", back_populates="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class FaceEncoding(Base):
    __tablename__ = 'face_encodings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    encoding_data = Column(String)  # Store as base64
    user = relationship("User", back_populates="face_encodings")

class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    access_level = Column(Integer)
    user = relationship("User", back_populates="permissions")
