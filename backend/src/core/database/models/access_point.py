"""
Access point model for managing physical access control points.
"""

from typing import Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..base import Base

class AccessPoint(Base):
    """Access point model for managing physical access control points."""
    
    __tablename__ = 'access_points'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String)
    status = Column(String, default='offline')
    type = Column(String, default='door')
    last_access = Column(DateTime)
    settings = Column(JSON)
    zone_id = Column(String, ForeignKey('zones.id'), nullable=False)
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    updated_by = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = relationship('User', foreign_keys=[created_by], back_populates='access_points')
    updater = relationship('User', foreign_keys=[updated_by])
    zone = relationship('Zone', back_populates='access_points')
    alerts = relationship('Alert', back_populates='access_point')

    def to_dict(self) -> dict:
        """Convert access point to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'status': self.status,
            'type': self.type,
            'last_access': self.last_access.isoformat() if self.last_access else None,
            'settings': self.settings,
            'zone_id': self.zone_id,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        } 