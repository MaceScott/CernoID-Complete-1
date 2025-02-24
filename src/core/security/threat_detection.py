"""
Advanced threat detection system with behavior analysis and anomaly detection.
"""
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import cv2
from dataclasses import dataclass
import time
from collections import deque
import tensorflow as tf
from ..utils.config import get_settings
from ..utils.logging import get_logger

@dataclass
class ThreatEvent:
    """Detected threat event with metadata"""
    event_type: str
    confidence: float
    location: Tuple[int, int, int, int]
    timestamp: float
    frame_id: int
    metadata: Dict[str, Any]

class ThreatDetector:
    """
    Advanced threat detection with multiple detection methods
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize detection models
        self.behavior_model = self._load_behavior_model()
        self.object_detector = self._load_object_detector()
        self.motion_detector = cv2.createBackgroundSubtractorMOG2()
        
        # Initialize tracking
        self.tracker = cv2.TrackerCSRT_create()
        
        # Motion history
        self.motion_history = deque(maxlen=self.settings.motion_history_frames)
        
        # Event history for pattern detection
        self.event_history = deque(maxlen=self.settings.event_history_size)
        
        # Zone definitions
        self.restricted_zones = self._load_zones()
        
    def _load_behavior_model(self) -> tf.keras.Model:
        """Load behavior analysis model"""
        try:
            model = tf.keras.models.load_model(
                self.settings.behavior_model_path
            )
            self.logger.info("Behavior model loaded successfully")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load behavior model: {str(e)}")
            return None
            
    def _load_object_detector(self) -> cv2.dnn.Net:
        """Load YOLO object detector"""
        try:
            net = cv2.dnn.readNet(
                self.settings.yolo_weights,
                self.settings.yolo_config
            )
            
            if self.settings.use_gpu:
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                
            self.logger.info("Object detector loaded successfully")
            return net
        except Exception as e:
            self.logger.error(f"Failed to load object detector: {str(e)}")
            return None
            
    def _load_zones(self) -> Dict[str, np.ndarray]:
        """Load restricted zone definitions"""
        try:
            zones = {}
            for zone_name, points in self.settings.restricted_zones.items():
                zones[zone_name] = np.array(points)
            return zones
        except Exception as e:
            self.logger.error(f"Failed to load zones: {str(e)}")
            return {}
            
    async def detect_threats(self,
                           frame: np.ndarray,
                           frame_id: int,
                           detected_faces: List[Dict]) -> List[ThreatEvent]:
        """
        Detect threats in frame
        
        Args:
            frame: Current video frame
            frame_id: Frame identifier
            detected_faces: List of detected faces with metadata
            
        Returns:
            List of detected threat events
        """
        threats = []
        timestamp = time.time()
        
        try:
            # Motion detection
            motion_threats = await self._detect_motion_threats(
                frame, frame_id, timestamp
            )
            threats.extend(motion_threats)
            
            # Object detection
            object_threats = await self._detect_object_threats(
                frame, frame_id, timestamp
            )
            threats.extend(object_threats)
            
            # Behavior analysis
            behavior_threats = await self._analyze_behavior(
                frame, frame_id, detected_faces, timestamp
            )
            threats.extend(behavior_threats)
            
            # Zone violations
            zone_threats = await self._check_zone_violations(
                frame, frame_id, detected_faces, timestamp
            )
            threats.extend(zone_threats)
            
            # Pattern detection
            pattern_threats = await self._detect_patterns(
                frame_id, detected_faces, timestamp
            )
            threats.extend(pattern_threats)
            
            # Update event history
            self.event_history.extend(threats)
            
            return threats
            
        except Exception as e:
            self.logger.error(f"Threat detection failed: {str(e)}")
            return []
            
    async def _detect_motion_threats(self,
                                   frame: np.ndarray,
                                   frame_id: int,
                                   timestamp: float) -> List[ThreatEvent]:
        """Detect suspicious motion patterns"""
        threats = []
        
        try:
            # Apply motion detection
            fgmask = self.motion_detector.apply(frame)
            
            # Calculate motion metrics
            motion_ratio = np.count_nonzero(fgmask) / fgmask.size
            self.motion_history.append(motion_ratio)
            
            # Check for sudden motion
            if len(self.motion_history) >= 2:
                motion_delta = abs(
                    self.motion_history[-1] - self.motion_history[-2]
                )
                
                if motion_delta > self.settings.motion_threshold:
                    # Get motion regions
                    contours, _ = cv2.findContours(
                        fgmask,
                        cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE
                    )
                    
                    for contour in contours:
                        if cv2.contourArea(contour) > self.settings.min_motion_area:
                            x, y, w, h = cv2.boundingRect(contour)
                            threats.append(ThreatEvent(
                                event_type="sudden_motion",
                                confidence=float(motion_delta),
                                location=(x, y, x+w, y+h),
                                timestamp=timestamp,
                                frame_id=frame_id,
                                metadata={
                                    "motion_ratio": float(motion_ratio),
                                    "area": float(cv2.contourArea(contour))
                                }
                            ))
                            
        except Exception as e:
            self.logger.error(f"Motion detection failed: {str(e)}")
            
        return threats
        
    async def _detect_object_threats(self,
                                   frame: np.ndarray,
                                   frame_id: int,
                                   timestamp: float) -> List[ThreatEvent]:
        """Detect threatening objects"""
        threats = []
        
        if self.object_detector is None:
            return threats
            
        try:
            # Prepare image for YOLO
            blob = cv2.dnn.blobFromImage(
                frame,
                1/255.0,
                (416, 416),
                swapRB=True,
                crop=False
            )
            
            self.object_detector.setInput(blob)
            outputs = self.object_detector.forward(
                self.object_detector.getUnconnectedOutLayersNames()
            )
            
            # Process detections
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    
                    if confidence > self.settings.object_threshold:
                        # Check if object class is threatening
                        if class_id in self.settings.threat_object_classes:
                            center_x = int(detection[0] * frame.shape[1])
                            center_y = int(detection[1] * frame.shape[0])
                            width = int(detection[2] * frame.shape[1])
                            height = int(detection[3] * frame.shape[0])
                            
                            x = int(center_x - width/2)
                            y = int(center_y - height/2)
                            
                            threats.append(ThreatEvent(
                                event_type="threatening_object",
                                confidence=float(confidence),
                                location=(x, y, x+width, y+height),
                                timestamp=timestamp,
                                frame_id=frame_id,
                                metadata={
                                    "class_id": int(class_id),
                                    "class_name": self.settings.class_names[class_id]
                                }
                            ))
                            
        except Exception as e:
            self.logger.error(f"Object detection failed: {str(e)}")
            
        return threats
        
    async def _analyze_behavior(self,
                              frame: np.ndarray,
                              frame_id: int,
                              detected_faces: List[Dict],
                              timestamp: float) -> List[ThreatEvent]:
        """Analyze behavior patterns"""
        threats = []
        
        if self.behavior_model is None:
            return threats
            
        try:
            for face in detected_faces:
                # Extract behavior features
                features = self._extract_behavior_features(face)
                
                # Predict behavior
                prediction = self.behavior_model.predict(
                    features.reshape(1, -1)
                )
                
                # Check for suspicious behavior
                if prediction[0] > self.settings.behavior_threshold:
                    threats.append(ThreatEvent(
                        event_type="suspicious_behavior",
                        confidence=float(prediction[0]),
                        location=face["bbox"],
                        timestamp=timestamp,
                        frame_id=frame_id,
                        metadata={
                            "person_id": face.get("person_id"),
                            "behavior_type": self._classify_behavior(prediction)
                        }
                    ))
                    
        except Exception as e:
            self.logger.error(f"Behavior analysis failed: {str(e)}")
            
        return threats
        
    def _extract_behavior_features(self, face: Dict) -> np.ndarray:
        """Extract features for behavior analysis"""
        # Implementation depends on specific behavior model
        # This is a placeholder
        return np.array([])
        
    def _classify_behavior(self, prediction: np.ndarray) -> str:
        """Classify behavior type from prediction"""
        # Implementation depends on behavior model
        return "unknown"
        
    async def _check_zone_violations(self,
                                   frame: np.ndarray,
                                   frame_id: int,
                                   detected_faces: List[Dict],
                                   timestamp: float) -> List[ThreatEvent]:
        """Check for restricted zone violations"""
        threats = []
        
        try:
            for face in detected_faces:
                bbox = face["bbox"]
                center = (
                    (bbox[0] + bbox[2]) // 2,
                    (bbox[1] + bbox[3]) // 2
                )
                
                for zone_name, zone_points in self.restricted_zones.items():
                    if cv2.pointPolygonTest(
                        zone_points,
                        center,
                        False
                    ) >= 0:
                        threats.append(ThreatEvent(
                            event_type="zone_violation",
                            confidence=1.0,
                            location=bbox,
                            timestamp=timestamp,
                            frame_id=frame_id,
                            metadata={
                                "person_id": face.get("person_id"),
                                "zone_name": zone_name
                            }
                        ))
                        
        except Exception as e:
            self.logger.error(f"Zone violation check failed: {str(e)}")
            
        return threats
        
    async def _detect_patterns(self,
                             frame_id: int,
                             detected_faces: List[Dict],
                             timestamp: float) -> List[ThreatEvent]:
        """Detect suspicious patterns in event history"""
        threats = []
        
        try:
            # Analyze event patterns
            if len(self.event_history) >= self.settings.min_pattern_length:
                pattern = self._analyze_event_pattern()
                
                if pattern["suspicious"]:
                    threats.append(ThreatEvent(
                        event_type="suspicious_pattern",
                        confidence=pattern["confidence"],
                        location=(0, 0, 0, 0),  # Global event
                        timestamp=timestamp,
                        frame_id=frame_id,
                        metadata=pattern
                    ))
                    
        except Exception as e:
            self.logger.error(f"Pattern detection failed: {str(e)}")
            
        return threats
        
    def _analyze_event_pattern(self) -> Dict[str, Any]:
        """Analyze pattern in event history"""
        # Implementation depends on specific pattern detection requirements
        return {
            "suspicious": False,
            "confidence": 0.0,
            "pattern_type": "none"
        } 