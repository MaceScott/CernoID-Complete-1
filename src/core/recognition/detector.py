"""
Face detection module with anti-spoofing capabilities.
"""
from typing import List, Tuple, Optional
import cv2
import dlib
import numpy as np
from dataclasses import dataclass
from ..utils.config import get_settings
from ..utils.logging import get_logger

@dataclass
class DetectionResult:
    """Face detection result with additional metadata"""
    bbox: Tuple[int, int, int, int]
    confidence: float
    landmarks: Optional[np.ndarray] = None
    anti_spoof_score: Optional[float] = None
    depth_map: Optional[np.ndarray] = None

class FaceDetector:
    """
    Advanced face detector with anti-spoofing capabilities
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize detectors
        self.hog_detector = dlib.get_frontal_face_detector()
        self.cnn_detector = dlib.cnn_face_detection_model_v1(
            self.settings.cnn_model_path
        )
        self.landmark_predictor = dlib.shape_predictor(
            self.settings.landmark_model_path
        )
        
        # Initialize anti-spoofing
        self.initialize_anti_spoofing()
        
    def initialize_anti_spoofing(self):
        """Initialize anti-spoofing models with additional techniques"""
        try:
            self.blink_detector = cv2.dnn.readNet(
                self.settings.blink_model_path,
                self.settings.blink_config_path
            )
            self.texture_analyzer = cv2.dnn.readNet(
                self.settings.texture_model_path,
                self.settings.texture_config_path
            )
            self.depth_estimator = cv2.dnn.readNet(
                self.settings.depth_model_path,
                self.settings.depth_config_path
            )
            self.logger.info("Anti-spoofing models loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load anti-spoofing models: {str(e)}")
        
    async def detect_faces(self, 
                         frame: np.ndarray,
                         use_cnn: bool = False,
                         check_anti_spoofing: bool = True) -> List[DetectionResult]:
        """
        Detect faces in frame with enhanced anti-spoofing checks
        
        Args:
            frame: Input image frame
            use_cnn: Whether to use CNN detector
            check_anti_spoofing: Whether to perform anti-spoofing checks
            
        Returns:
            List of detection results
        """
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            if use_cnn:
                detections = self.cnn_detector(gray)
            else:
                detections = self.hog_detector(gray)
                
            if not detections:
                self.logger.warning("No faces detected.")
                return []
                
            results = []
            for detection in detections:
                # Perform additional anti-spoofing checks
                if check_anti_spoofing:
                    if not self.perform_anti_spoofing_checks(frame, detection):
                        self.logger.info("Anti-spoofing check failed.")
                        continue
                results.append(detection)
            return results
        except Exception as e:
            self.logger.error(f"Face detection failed: {str(e)}")
            return []

    def perform_anti_spoofing_checks(self, frame: np.ndarray, detection) -> bool:
        try:
            blob = cv2.dnn.blobFromImage(frame, 1.0, (224, 224), (104.0, 177.0, 123.0))
            self.texture_analyzer.setInput(blob)
            texture_pass = self.texture_analyzer.forward()

            self.depth_estimator.setInput(blob)
            depth_pass = self.depth_estimator.forward()

            spoof_score = np.mean([texture_pass, depth_pass])
            self.logger.debug(f"Anti-spoofing score: {spoof_score}")

            return spoof_score > self.settings.anti_spoof_threshold
        except Exception as e:
            self.logger.error(f"Anti-spoofing check failed: {str(e)}")
            return False
        
    def check_anti_spoofing(self,
                           frame: np.ndarray,
                           bbox: Tuple[int, int, int, int],
                           landmarks: np.ndarray) -> float:
        """
        Perform anti-spoofing checks
        
        Args:
            frame: Input image frame
            bbox: Face bounding box
            landmarks: Facial landmarks
            
        Returns:
            Anti-spoofing confidence score (0-1)
        """
        scores = []
        
        # Check blink
        blink_score = self.detect_blink(frame, landmarks)
        scores.append(blink_score)
        
        # Check head movement
        movement_score = self.check_head_movement(landmarks)
        scores.append(movement_score)
        
        # Additional checks can be added here
        
        return np.mean(scores)
        
    def detect_blink(self,
                    frame: np.ndarray,
                    landmarks: np.ndarray) -> float:
        """Detect natural eye blinking"""
        # Extract eye regions using landmarks
        left_eye = landmarks[36:42]
        right_eye = landmarks[42:48]
        
        # Calculate eye aspect ratio
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        
        # Average eye aspect ratio
        ear = (left_ear + right_ear) / 2.0
        
        # Return blink probability
        return 1.0 if ear < self.settings.blink_threshold else 0.0
        
    def check_head_movement(self, landmarks: np.ndarray) -> float:
        """Check for natural head movement"""
        movement_score = self.calculate_head_pose(landmarks)
        return movement_score > self.settings.head_movement_threshold
        
    @staticmethod
    def eye_aspect_ratio(eye: np.ndarray) -> float:
        """Calculate eye aspect ratio"""
        # Compute euclidean distances
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        C = np.linalg.norm(eye[0] - eye[3])
        
        # Calculate eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear 

    def calculate_head_pose(self, landmarks: np.ndarray) -> float:
        try:
            # Placeholder for actual head pose estimation logic
            head_pose_score = np.random.uniform(0.8, 1.0)  # Simulated score for demonstration
            self.logger.debug(f"Head pose score: {head_pose_score}")
            return head_pose_score
        except Exception as e:
            self.logger.error(f"Head pose estimation failed: {str(e)}")
            return 0.0 