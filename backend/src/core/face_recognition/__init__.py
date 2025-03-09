"""
Face recognition module exports.
"""

from typing import Optional
from fastapi import Depends
from .core import FaceRecognitionSystem, FaceDetection, FaceFeatures, FaceMatch

class FaceRecognitionManager:
    """Singleton manager for face recognition system."""
    _instance: Optional[FaceRecognitionSystem] = None
    
    @classmethod
    def get_instance(cls) -> FaceRecognitionSystem:
        """Get or create face recognition system instance."""
        if cls._instance is None:
            cls._instance = FaceRecognitionSystem()
        return cls._instance

# Create global face recognition system instance
face_recognition_system = FaceRecognitionManager.get_instance()

def get_recognition_service() -> FaceRecognitionSystem:
    """Get face recognition service instance."""
    return FaceRecognitionManager.get_instance()

__all__ = [
    'FaceRecognitionSystem',
    'FaceDetection',
    'FaceFeatures',
    'FaceMatch',
    'get_recognition_service',
    'face_recognition_system'
]
