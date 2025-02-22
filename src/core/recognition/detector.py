from typing import Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
import dlib
from ..base import BaseComponent
from ..utils.errors import DetectionError

class FaceDetector(BaseComponent):
    """Advanced face detection and analysis engine"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # Initialize detection models
        self._detector = dlib.get_frontal_face_detector()
        self._predictor = dlib.shape_predictor(
            config.get('recognition.landmark_model',
            'models/shape_predictor_68_face_landmarks.dat')
        )
        self._face_rec = dlib.face_recognition_model_v1(
            config.get('recognition.recognition_model',
            'models/dlib_face_recognition_resnet_model_v1.dat')
        )
        
        # Anti-spoofing settings
        self._min_face_size = config.get('recognition.min_face_size', 64)
        self._check_blinks = config.get('recognition.check_blinks', True)
        self._check_movement = config.get('recognition.check_movement', True)
        
        # Performance tracking
        self._stats = {
            'detections': 0,
            'spoof_attempts': 0,
            'processing_time': 0.0
        }

    async def detect_faces(self,
                          frame: np.ndarray,
                          anti_spoof: bool = True) -> List[Dict]:
        """Detect and analyze faces in frame"""
        try:
            import time
            start_time = time.time()
            
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self._detector(gray)
            results = []
            
            for face in faces:
                # Skip if face is too small
                if face.width() < self._min_face_size:
                    continue
                
                # Get face landmarks
                shape = self._predictor(gray, face)
                landmarks = self._shape_to_np(shape)
                
                # Get face encoding
                face_chip = dlib.get_face_chip(frame, shape)
                face_encoding = np.array(
                    self._face_rec.compute_face_descriptor(face_chip)
                )
                
                # Perform anti-spoofing checks if enabled
                if anti_spoof:
                    spoof_score = await self._check_anti_spoofing(
                        gray,
                        landmarks
                    )
                    if spoof_score > 0.8:  # High confidence it's real
                        self._stats['spoof_attempts'] += 1
                        continue
                
                # Create result dictionary
                result = {
                    'bbox': (
                        face.left(),
                        face.top(),
                        face.right(),
                        face.bottom()
                    ),
                    'landmarks': landmarks,
                    'encoding': face_encoding,
                    'confidence': self._calculate_confidence(face, landmarks)
                }
                
                results.append(result)
            
            # Update stats
            self._stats['detections'] += len(results)
            self._stats['processing_time'] = time.time() - start_time
            
            return results
            
        except Exception as e:
            raise DetectionError(f"Face detection failed: {str(e)}")

    async def _check_anti_spoofing(self,
                                 gray: np.ndarray,
                                 landmarks: np.ndarray) -> float:
        """Perform anti-spoofing checks"""
        score = 1.0
        
        if self._check_blinks:
            # Check eye aspect ratio for blink detection
            ear = self._get_eye_aspect_ratio(landmarks)
            if ear < 0.2:  # Eyes closed/photo
                score *= 0.5
        
        if self._check_movement:
            # Check facial landmarks for natural movement
            # This would track landmarks across multiple frames
            # Simplified for this example
            pass
        
        return score

    def _get_eye_aspect_ratio(self, landmarks: np.ndarray) -> float:
        """Calculate eye aspect ratio for blink detection"""
        # Eye landmarks indices
        left_eye = landmarks[36:42]
        right_eye = landmarks[42:48]
        
        # Calculate eye aspect ratios
        left_ear = self._eye_aspect_ratio(left_eye)
        right_ear = self._eye_aspect_ratio(right_eye)
        
        # Return average
        return (left_ear + right_ear) / 2.0

    def _eye_aspect_ratio(self, eye: np.ndarray) -> float:
        """Calculate single eye aspect ratio"""
        # Compute distances between vertical eye landmarks
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        
        # Compute distance between horizontal eye landmarks
        C = np.linalg.norm(eye[0] - eye[3])
        
        # Calculate eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear

    def _calculate_confidence(self,
                            face: dlib.rectangle,
                            landmarks: np.ndarray) -> float:
        """Calculate detection confidence score"""
        # Factors that influence confidence:
        # 1. Face size
        # 2. Face alignment
        # 3. Landmark stability
        
        # Size factor (larger faces = higher confidence)
        size_score = min(1.0, face.width() / self._min_face_size)
        
        # Alignment factor (how centered/upright the face is)
        alignment_score = self._calculate_alignment(landmarks)
        
        # Combined confidence score
        confidence = (size_score + alignment_score) / 2.0
        return min(1.0, confidence)

    def _calculate_alignment(self, landmarks: np.ndarray) -> float:
        """Calculate face alignment score"""
        # Get eye centers
        left_eye_center = landmarks[36:42].mean(axis=0)
        right_eye_center = landmarks[42:48].mean(axis=0)
        
        # Calculate eye angle
        dy = right_eye_center[1] - left_eye_center[1]
        dx = right_eye_center[0] - left_eye_center[0]
        angle = np.degrees(np.arctan2(dy, dx))
        
        # Score based on how level the eyes are
        return 1.0 - min(1.0, abs(angle) / 20.0)

    def _shape_to_np(self, shape: dlib.full_object_detection) -> np.ndarray:
        """Convert dlib shape to numpy array"""
        coords = np.zeros((68, 2), dtype=np.int32)
        for i in range(0, 68):
            coords[i] = (shape.part(i).x, shape.part(i).y)
        return coords

    async def get_stats(self) -> Dict:
        """Get detector statistics"""
        return self._stats.copy() 