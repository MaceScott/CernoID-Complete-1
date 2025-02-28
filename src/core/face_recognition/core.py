"""
Unified face recognition system with centralized error handling and configuration.
"""

from typing import List, Optional, Dict, Union
import numpy as np
import cv2
from dataclasses import dataclass
from functools import lru_cache
import logging
from weakref import WeakValueDictionary
from core.events.manager import EventManager
from core.error_handling import handle_exceptions
from core.config.manager import ConfigManager
from core.database import DatabasePool
from core.recognition.processor import BatchDetector

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class FaceDetection:
    """Face detection result"""
    bbox: tuple[int, int, int, int]
    confidence: float
    frame_index: int
    face_image: np.ndarray

@dataclass
class FaceMatch:
    """Face matching result"""
    user_id: str
    confidence: float
    metadata: Optional[Dict] = None

class FaceRecognitionSystem:
    """Unified face recognition system"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.event_manager = EventManager()
        self.db_pool = DatabasePool()
        
        # Initialize components
        self._detector = self._init_detector()
        self._encoder = self._init_encoder()
        self._matcher = self._init_matcher()
        
        # Cache settings
        self._encoding_cache = WeakValueDictionary()
        self.matching_threshold = self.config.get('face_recognition.matching_threshold', 0.6)

    def _init_detector(self) -> cv2.CascadeClassifier:
        """Initialize face detector"""
        cascade_path = self.config.get('face_detection.cascade_path')
        detector = cv2.CascadeClassifier(cascade_path)
        if detector.empty():
            raise ValueError(f"Failed to load cascade classifier from {cascade_path}")
        return detector

    def _init_encoder(self) -> 'dlib.face_recognition_model_v1':
        """Initialize face encoder"""
        try:
            import dlib
            model_path = self.config.get('face_encoding.model_path')
            return dlib.face_recognition_model_v1(model_path)
        except ImportError as e:
            logger.error("Failed to import dlib. Face encoding will not work.")
            raise ImportError("dlib is required for face encoding") from e

    def _init_matcher(self) -> BatchDetector:
        """Initialize face matcher"""
        return BatchDetector(
            batch_size=self.config.get('face_detection.batch_size', 4)
        )

    @handle_exceptions(logger=logger.error)
    async def detect_faces(self, 
                         frames: Union[np.ndarray, List[np.ndarray]]) -> List[FaceDetection]:
        """
        Detect faces in one or more frames
        
        Args:
            frames: Single frame or list of frames
            
        Returns:
            List of FaceDetection objects
        """
        if isinstance(frames, np.ndarray):
            frames = [frames]
            
        detections = []
        min_confidence = self.config.get('face_detection.min_confidence', 0.8)
        
        for idx, frame in enumerate(frames):
            faces = self._detector.detectMultiScale(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            for (x, y, w, h) in faces:
                face_image = frame[y:y+h, x:x+w]
                confidence = self._compute_detection_confidence(face_image)
                
                if confidence > min_confidence:
                    detections.append(FaceDetection(
                        bbox=(x, y, w, h),
                        confidence=confidence,
                        frame_index=idx,
                        face_image=face_image
                    ))
                    
        return detections

    @lru_cache(maxsize=1000)
    def _compute_detection_confidence(self, face_image: np.ndarray) -> float:
        """Compute confidence score for detected face"""
        # Implement confidence computation logic
        return 0.95  # Placeholder

    @handle_exceptions(logger=logger.error)
    async def encode_faces(self, 
                         detections: List[FaceDetection]) -> List[np.ndarray]:
        """
        Generate encodings for detected faces
        
        Args:
            detections: List of face detections
            
        Returns:
            List of face encodings
        """
        encodings = []
        for detection in detections:
            cache_key = hash(detection.face_image.tobytes())
            
            if cache_key in self._encoding_cache:
                encoding = self._encoding_cache[cache_key]
            else:
                encoding = np.array(
                    self._encoder.compute_face_descriptor(detection.face_image)
                )
                self._encoding_cache[cache_key] = encoding
                
            encodings.append(encoding)
            
        return encodings

    @handle_exceptions(logger=logger.error)
    async def find_matches(self, encoding: np.ndarray) -> List[FaceMatch]:
        """
        Find matches for a face encoding
        
        Args:
            encoding: Face encoding to match
            
        Returns:
            List of FaceMatch objects
        """
        async with self.db_pool.get_connection() as conn:
            stored_encodings = await conn.execute(
                "SELECT user_id, encoding_data, metadata FROM face_encodings"
            )
            
            matches = []
            for stored in stored_encodings:
                similarity = 1 - np.linalg.norm(encoding - stored.encoding_data)
                
                if similarity > self.matching_threshold:
                    matches.append(FaceMatch(
                        user_id=stored.user_id,
                        confidence=float(similarity),
                        metadata=stored.metadata
                    ))
                    
            return sorted(matches, key=lambda x: x.confidence, reverse=True)

    @handle_exceptions(logger=logger.error)
    async def verify_face(self, frame: np.ndarray) -> Optional[FaceMatch]:
        """
        Complete face verification pipeline
        
        Args:
            frame: Image frame containing face
            
        Returns:
            FaceMatch if verified, None otherwise
        """
        # Detect face
        detections = await self.detect_faces(frame)
        if not detections:
            await self.event_manager.publish('face_not_detected', {'frame': frame})
            return None
            
        # Use best detection
        best_detection = max(detections, key=lambda d: d.confidence)
        
        # Generate encoding
        encodings = await self.encode_faces([best_detection])
        if not encodings:
            await self.event_manager.publish('face_encoding_failed', 
                                          {'detection': best_detection})
            return None
            
        # Find matches
        matches = await self.find_matches(encodings[0])
        
        if matches:
            best_match = matches[0]
            await self.event_manager.publish('face_verified', {'match': best_match})
            return best_match
            
        await self.event_manager.publish('face_unverified', 
                                       {'encoding': encodings[0]})
        return None

    def clear_caches(self) -> None:
        """Clear all internal caches"""
        self._encoding_cache.clear()
        self._compute_detection_confidence.cache_clear() 