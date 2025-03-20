"""
Face recognition package with advanced features.
"""
from .matcher import FaceMatcher, MatchResult
from .video_processor import VideoProcessor, VideoFrame
from .anti_spoofing import analyze_frame

__all__ = [
    'FaceMatcher',
    'MatchResult',
    'VideoProcessor',
    'VideoFrame',
    'analyze_frame'
]
