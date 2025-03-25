"""
Face recognition package with advanced features.
"""
from .matcher import FaceMatcher, MatchResult
from .video_processor import VideoProcessor, VideoFrame
from .anti_spoofing import analyze_frame
from .core import FaceRecognitionSystem
from ..config import settings

# Create a singleton instance of FaceRecognitionSystem
face_recognition_system = FaceRecognitionSystem()

__all__ = [
    'FaceMatcher',
    'MatchResult',
    'VideoProcessor',
    'VideoFrame',
    'analyze_frame',
    'FaceRecognitionSystem',
    'face_recognition_system'
]
