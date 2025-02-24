"""
Face encoding module with advanced features and optimizations.
"""
from typing import List, Optional, Dict, Any
import numpy as np
import dlib
import cv2
from dataclasses import dataclass
from pathlib import Path
import pickle
from concurrent.futures import ThreadPoolExecutor
from ..utils.config import get_settings
from ..utils.logging import get_logger
from .detector import DetectionResult

@dataclass
class EncodingResult:
    """Face encoding result with metadata"""
    encoding: np.ndarray
    quality_score: float
    metadata: Dict[str, Any]
    timestamp: float

class FaceEncoder:
    """
    Advanced face encoder with quality assessment
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize face recognition model
        model_path = Path(self.settings.face_recognition_model_path)
        if not model_path.exists():
            raise ValueError(f"Model not found at {model_path}")
            
        self.face_encoder = dlib.face_recognition_model_v1(str(model_path))
        
        # Initialize quality assessment
        self.quality_detector = self._init_quality_detector()
        
        # Thread pool for parallel processing
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.settings.encoder_threads
        )
        
        # Cache for frequently used encodings
        self.encoding_cache = {}
        
    def _init_quality_detector(self):
        """Initialize face quality assessment model"""
        try:
            quality_model_path = Path(self.settings.quality_model_path)
            if quality_model_path.exists():
                return cv2.dnn.readNet(
                    str(quality_model_path),
                    self.settings.quality_config_path
                )
        except Exception as e:
            self.logger.warning(f"Failed to load quality model: {e}")
        return None
        
    async def encode_face(self,
                         detection: DetectionResult,
                         frame: np.ndarray,
                         enhance: bool = True) -> Optional[EncodingResult]:
        """
        Generate face encoding for single detection
        
        Args:
            detection: Face detection result
            frame: Original image frame
            enhance: Whether to enhance face quality
            
        Returns:
            Encoding result if successful
        """
        try:
            # Extract face region
            x1, y1, x2, y2 = detection.bbox
            face = frame[y1:y2, x1:x2]
            
            # Enhance face quality if requested
            if enhance:
                face = self.enhance_face(face)
            
            # Generate encoding
            shape = detection.landmarks
            encoding = np.array(
                self.face_encoder.compute_face_descriptor(frame, shape)
            )
            
            # Assess quality
            quality_score = self.assess_quality(face, shape)
            
            # Generate metadata
            metadata = {
                "quality_score": quality_score,
                "face_size": (x2 - x1) * (y2 - y1),
                "enhanced": enhance,
                "confidence": detection.confidence
            }
            
            return EncodingResult(
                encoding=encoding,
                quality_score=quality_score,
                metadata=metadata,
                timestamp=cv2.getTickCount() / cv2.getTickFrequency()
            )
            
        except Exception as e:
            self.logger.error(f"Face encoding failed: {str(e)}")
            return None
            
    async def encode_faces(self,
                          detections: List[DetectionResult],
                          frame: np.ndarray) -> List[EncodingResult]:
        """
        Generate encodings for multiple detections in parallel
        
        Args:
            detections: List of face detections
            frame: Original image frame
            
        Returns:
            List of encoding results
        """
        # Process faces in parallel
        futures = [
            self.thread_pool.submit(
                self.encode_face, detection, frame
            )
            for detection in detections
        ]
        
        # Collect results
        results = []
        for future in futures:
            try:
                result = await future.result()
                if result is not None:
                    results.append(result)
            except Exception as e:
                self.logger.error(f"Parallel encoding failed: {str(e)}")
                
        return results
        
    def enhance_face(self, face: np.ndarray) -> np.ndarray:
        """
        Enhance face image quality
        
        Args:
            face: Face image region
            
        Returns:
            Enhanced face image
        """
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
            
            # CLAHE on L channel
            clahe = cv2.createCLAHE(
                clipLimit=2.0,
                tileGridSize=(8, 8)
            )
            lab[..., 0] = clahe.apply(lab[..., 0])
            
            # Convert back to BGR
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # Denoise if needed
            if self.settings.apply_denoising:
                enhanced = cv2.fastNlMeansDenoisingColored(
                    enhanced,
                    None,
                    10,
                    10,
                    7,
                    21
                )
                
            return enhanced
            
        except Exception as e:
            self.logger.warning(f"Face enhancement failed: {str(e)}")
            return face
            
    def assess_quality(self,
                      face: np.ndarray,
                      landmarks: np.ndarray) -> float:
        """
        Assess face image quality
        
        Args:
            face: Face image region
            landmarks: Facial landmarks
            
        Returns:
            Quality score (0-1)
        """
        scores = []
        
        # Check resolution
        face_size = face.shape[0] * face.shape[1]
        size_score = min(face_size / self.settings.min_face_size, 1.0)
        scores.append(size_score)
        
        # Check blur
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(blur_score / self.settings.blur_threshold, 1.0)
        scores.append(blur_score)
        
        # Check pose using landmarks
        pose_score = self.assess_pose(landmarks)
        scores.append(pose_score)
        
        # Use quality model if available
        if self.quality_detector is not None:
            model_score = self.get_quality_prediction(face)
            scores.append(model_score)
            
        return np.mean(scores)
        
    def assess_pose(self, landmarks: np.ndarray) -> float:
        """Assess face pose using landmarks"""
        try:
            # Calculate face symmetry
            left_eye = landmarks[36:42].mean(axis=0)
            right_eye = landmarks[42:48].mean(axis=0)
            
            # Eye line angle
            angle = np.abs(np.arctan2(
                right_eye[1] - left_eye[1],
                right_eye[0] - left_eye[0]
            ))
            
            # Convert to score (0-1)
            return 1.0 - (angle / (np.pi / 4))
            
        except Exception as e:
            self.logger.warning(f"Pose assessment failed: {str(e)}")
            return 1.0
            
    def get_quality_prediction(self, face: np.ndarray) -> float:
        """Get quality score from ML model"""
        try:
            # Preprocess image
            blob = cv2.dnn.blobFromImage(
                face,
                1.0,
                (112, 112),
                (0, 0, 0),
                swapRB=True,
                crop=False
            )
            
            # Get prediction
            self.quality_detector.setInput(blob)
            score = self.quality_detector.forward()[0][0]
            
            return float(score)
            
        except Exception as e:
            self.logger.warning(f"Quality prediction failed: {str(e)}")
            return 1.0 