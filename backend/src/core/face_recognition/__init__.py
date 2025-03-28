"""
Face recognition package with advanced features.
"""
from .matcher import FaceMatcher, MatchResult
from .video_processor import VideoProcessor, VideoFrame
from .anti_spoofing import analyze_frame
from .core import FaceRecognitionSystem
from core.config.settings import get_settings

settings = get_settings()

# Lazy initialize the face recognition system
_face_recognition_system = None

def get_face_recognition_system():
    """Get or create the face recognition system instance."""
    global _face_recognition_system
    if _face_recognition_system is None:
        _face_recognition_system = FaceRecognitionSystem()
    return _face_recognition_system

__all__ = [
    'FaceMatcher',
    'MatchResult',
    'VideoProcessor',
    'VideoFrame',
    'analyze_frame',
    'FaceRecognitionSystem',
    'get_face_recognition_system'
]
