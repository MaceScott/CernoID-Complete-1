"""
Recognition model for tracking face recognition events.
"""

from typing import Optional
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import BaseModel

class Recognition(BaseModel):
    """Recognition model for tracking face recognition events."""
    
    __tablename__ = 'recognitions'

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    camera_id = Column(String, ForeignKey('cameras.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    confidence = Column(Float, nullable=False)
    metadata = Column(JSON)
    
    # Relationships
    user = relationship('User', back_populates='recognitions')
    camera = relationship('Camera', back_populates='recognitions')

    def to_dict(self) -> dict:
        """Convert recognition to dictionary with additional fields."""
        data = super().to_dict()
        data['confidence'] = self.confidence
        data['metadata'] = self.metadata
        return data 