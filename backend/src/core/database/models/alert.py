"""
Alert model for managing security incidents and notifications.
"""

from typing import Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..base import Base

class Alert(Base):
    """Alert model for managing security incidents and notifications."""
    
    __tablename__ = 'alerts'

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    severity = Column(String, nullable=False)
    status = Column(String, default='open')
    source_type = Column(String, nullable=False)
    camera_id = Column(String, ForeignKey('cameras.id'))
    access_point_id = Column(String, ForeignKey('access_points.id'))
    meta_info = Column(JSON)
    assigned_to = Column(String, ForeignKey('users.id'))
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    updated_by = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = relationship('User', foreign_keys=[created_by], back_populates='created_alerts')
    updater = relationship('User', foreign_keys=[updated_by])
    assigned_user = relationship('User', foreign_keys=[assigned_to], back_populates='assigned_alerts')
    camera = relationship('Camera', back_populates='alerts')
    access_point = relationship('AccessPoint', back_populates='alerts')

    def to_dict(self) -> dict:
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'source_type': self.source_type,
            'camera_id': self.camera_id,
            'access_point_id': self.access_point_id,
            'meta_info': self.meta_info,
            'assigned_to': self.assigned_to,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        } 