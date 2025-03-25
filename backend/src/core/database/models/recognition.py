"""
Recognition model for tracking face recognition events.
"""

from typing import Optional
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..base import Base

class Recognition(Base):
    """Recognition model for tracking face recognition events."""
    
    __tablename__ = 'recognitions'

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    camera_id = Column(String, ForeignKey('cameras.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    confidence = Column(Float, nullable=False)
    meta_info = Column(JSON)
    
    # Relationships
    user = relationship('User', back_populates='recognitions')
    camera = relationship('Camera', back_populates='recognitions')

    def to_dict(self) -> dict:
        """Convert recognition to dictionary with additional fields."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'camera_id': self.camera_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'confidence': self.confidence,
            'meta_info': self.meta_info
        }
        return data 