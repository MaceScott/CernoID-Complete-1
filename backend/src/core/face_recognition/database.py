from typing import Dict, Optional, List
import numpy as np
from datetime import datetime
import json
import base64

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import ARRAY

Base = declarative_base()

class FaceEncoding(Base):
    """Database model for face encodings"""
    __tablename__ = 'face_encodings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    encoding = Column(ARRAY(Float), nullable=False)
    quality_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="face_encodings")

class User(Base):
    """Database model for users"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    face_encodings = relationship("FaceEncoding", back_populates="user")

class FaceDatabase:
    """Database service for face recognition"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def store_encoding(self, user_id: int, encoding: np.ndarray, quality_score: float) -> bool:
        """Store a face encoding in the database"""
        try:
            session = self.Session()
            face_encoding = FaceEncoding(
                user_id=user_id,
                encoding=encoding.tolist(),
                quality_score=quality_score
            )
            session.add(face_encoding)
            session.commit()
            return True
        except Exception as e:
            print(f"Error storing face encoding: {e}")
            return False
        finally:
            session.close()
    
    def get_encodings(self, user_id: int) -> List[np.ndarray]:
        """Get all face encodings for a user"""
        try:
            session = self.Session()
            encodings = session.query(FaceEncoding).filter_by(user_id=user_id).all()
            return [np.array(encoding.encoding) for encoding in encodings]
        except Exception as e:
            print(f"Error retrieving face encodings: {e}")
            return []
        finally:
            session.close()
    
    def get_all_encodings(self) -> Dict[int, List[np.ndarray]]:
        """Get all face encodings for all users"""
        try:
            session = self.Session()
            encodings = session.query(FaceEncoding).all()
            result = {}
            for encoding in encodings:
                if encoding.user_id not in result:
                    result[encoding.user_id] = []
                result[encoding.user_id].append(np.array(encoding.encoding))
            return result
        except Exception as e:
            print(f"Error retrieving all face encodings: {e}")
            return {}
        finally:
            session.close()
    
    def delete_encoding(self, encoding_id: int) -> bool:
        """Delete a face encoding from the database"""
        try:
            session = self.Session()
            encoding = session.query(FaceEncoding).filter_by(id=encoding_id).first()
            if encoding:
                session.delete(encoding)
                session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error deleting face encoding: {e}")
            return False
        finally:
            session.close()
    
    def get_user_encodings(self, username: str) -> List[np.ndarray]:
        """Get face encodings for a specific user"""
        try:
            session = self.Session()
            user = session.query(User).filter_by(username=username).first()
            if not user:
                return []
            encodings = session.query(FaceEncoding).filter_by(user_id=user.id).all()
            return [np.array(encoding.encoding) for encoding in encodings]
        except Exception as e:
            print(f"Error retrieving user face encodings: {e}")
            return []
        finally:
            session.close()
    
    def get_encoding_quality(self, encoding_id: int) -> Optional[float]:
        """Get quality score for a face encoding"""
        try:
            session = self.Session()
            encoding = session.query(FaceEncoding).filter_by(id=encoding_id).first()
            return encoding.quality_score if encoding else None
        except Exception as e:
            print(f"Error retrieving encoding quality: {e}")
            return None
        finally:
            session.close() 