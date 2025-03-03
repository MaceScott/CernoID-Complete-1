"""
Advanced face tracking system with anti-spoofing capabilities and Kalman filtering.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import cv2
from dataclasses import dataclass
from datetime import datetime
import asyncio
from collections import deque
import torch
from scipy.optimize import linear_sum_assignment

from .core import FaceDetection
from ..utils.errors import TrackingError
from ..utils.logging import get_logger
from ..config.manager import ConfigManager

@dataclass
class TrackingInfo:
    """Face tracking information with anti-spoofing metadata"""
    track_id: str
    bbox: Tuple[int, int, int, int]
    confidence: float
    velocity: Tuple[float, float]
    age: int  # track age in frames
    last_seen: datetime
    face_id: Optional[str] = None
    features: Optional[np.ndarray] = None
    anti_spoof_score: Optional[float] = None
    depth_map: Optional[np.ndarray] = None

class FaceTracker:
    """Advanced face tracking system with anti-spoofing"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.logger = get_logger(__name__)
        
        # Tracking settings
        self._max_age = self.config.get('tracking.max_age', 30)
        self._min_hits = self.config.get('tracking.min_hits', 3)
        self._iou_threshold = self.config.get('tracking.iou_threshold', 0.3)
        self._max_tracks = self.config.get('tracking.max_tracks', 50)
        
        # Initialize Kalman filter parameters
        self._init_kalman_parameters()
        
        # Active tracks
        self._tracks: Dict[str, TrackingInfo] = {}
        self._next_track_id = 0
        
        # Track history for motion analysis
        self._track_history: Dict[str, deque] = {}
        self._history_size = self.config.get('tracking.history_size', 30)
        
        # Motion prediction
        self._prediction_enabled = self.config.get('tracking.predict_motion', True)
        self._prediction_horizon = self.config.get('tracking.prediction_frames', 5)
        
        # Anti-spoofing models
        self._init_anti_spoofing()
        
        # Statistics
        self._stats = {
            'active_tracks': 0,
            'total_tracks': 0,
            'average_track_length': 0.0,
            'track_switches': 0,
            'spoof_attempts': 0
        }

    def _init_kalman_parameters(self) -> None:
        """Initialize Kalman filter parameters"""
        self._kalman_states: Dict[str, Dict] = {}
        
        # State transition matrix
        self._state_matrix = np.array([
            [1, 0, 1, 0],  # x
            [0, 1, 0, 1],  # y
            [0, 0, 1, 0],  # dx
            [0, 0, 0, 1]   # dy
        ], dtype=np.float32)
        
        # Measurement matrix
        self._measure_matrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float32)
        
        # Process noise
        self._process_noise = np.eye(4) * 0.1
        
        # Measurement noise
        self._measure_noise = np.eye(2) * 1.0

    def _init_anti_spoofing(self) -> None:
        """Initialize anti-spoofing models"""
        try:
            # Load models
            self._texture_analyzer = cv2.dnn.readNet(
                self.config.get('anti_spoofing.texture_model_path'),
                self.config.get('anti_spoofing.texture_config_path')
            )
            self._depth_estimator = cv2.dnn.readNet(
                self.config.get('anti_spoofing.depth_model_path'),
                self.config.get('anti_spoofing.depth_config_path')
            )
            self._blink_detector = cv2.dnn.readNet(
                self.config.get('anti_spoofing.blink_model_path'),
                self.config.get('anti_spoofing.blink_config_path')
            )
            
            # Load to GPU if available
            if torch.cuda.is_available():
                self._texture_analyzer.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self._depth_estimator.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self._blink_detector.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                
            self.logger.info("Anti-spoofing models loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load anti-spoofing models: {str(e)}")

    async def update(self, detections: List[FaceDetection], frame: np.ndarray) -> List[TrackingInfo]:
        """Update tracks with new detections"""
        try:
            # Predict new locations
            if self._prediction_enabled:
                self._predict_tracks()
            
            # Match detections to tracks
            matches, unmatched_tracks, unmatched_detections = \
                await self._match_detections(detections)
            
            # Update matched tracks
            for track_idx, det_idx in matches:
                await self._update_track(
                    list(self._tracks.keys())[track_idx],
                    detections[det_idx],
                    frame
                )
            
            # Handle unmatched tracks
            for track_idx in unmatched_tracks:
                track_id = list(self._tracks.keys())[track_idx]
                await self._update_unmatched_track(track_id)
            
            # Create new tracks
            for det_idx in unmatched_detections:
                await self._create_track(detections[det_idx], frame)
            
            # Remove old tracks
            await self._remove_old_tracks()
            
            # Update statistics
            self._update_stats()
            
            return list(self._tracks.values())
            
        except Exception as e:
            raise TrackingError(f"Track update failed: {str(e)}")

    async def _match_detections(self, detections: List[FaceDetection]) -> Tuple[List, List, List]:
        """Match detections to existing tracks"""
        try:
            if not self._tracks or not detections:
                return [], list(range(len(self._tracks))), list(range(len(detections)))
            
            # Calculate IoU matrix
            iou_matrix = np.zeros((len(self._tracks), len(detections)))
            for i, track in enumerate(self._tracks.values()):
                for j, det in enumerate(detections):
                    iou_matrix[i, j] = self._calculate_iou(
                        track.bbox,
                        det.bbox
                    )
            
            # Apply Hungarian algorithm
            track_indices, det_indices = linear_sum_assignment(-iou_matrix)
            
            # Filter matches using threshold
            matches = []
            unmatched_tracks = list(range(len(self._tracks)))
            unmatched_detections = list(range(len(detections)))
            
            for track_idx, det_idx in zip(track_indices, det_indices):
                if iou_matrix[track_idx, det_idx] >= self._iou_threshold:
                    matches.append((track_idx, det_idx))
                    unmatched_tracks.remove(track_idx)
                    unmatched_detections.remove(det_idx)
            
            return matches, unmatched_tracks, unmatched_detections
            
        except Exception as e:
            self.logger.error(f"Detection matching failed: {str(e)}")
            return [], [], list(range(len(detections)))

    async def _update_track(self, track_id: str, detection: FaceDetection, frame: np.ndarray) -> None:
        """Update matched track with anti-spoofing check"""
        try:
            track = self._tracks[track_id]
            
            # Update bbox and confidence
            track.bbox = detection.bbox
            track.confidence = detection.confidence
            track.last_seen = datetime.utcnow()
            track.age += 1
            
            # Perform anti-spoofing check
            anti_spoof_score = await self._check_anti_spoofing(frame, detection)
            track.anti_spoof_score = anti_spoof_score
            
            if anti_spoof_score < self.config.get('anti_spoofing.threshold', 0.8):
                self._stats['spoof_attempts'] += 1
                self.logger.warning(f"Possible spoof attempt detected for track {track_id}")
                return
            
            # Update Kalman filter
            if track_id in self._kalman_states:
                measurement = np.array([
                    [detection.bbox[0]],
                    [detection.bbox[1]]
                ])
                
                state = self._kalman_states[track_id]
                
                # Kalman update
                kalman_gain = np.dot(
                    np.dot(state['covariance'], self._measure_matrix.T),
                    np.linalg.inv(
                        np.dot(
                            np.dot(self._measure_matrix, state['covariance']),
                            self._measure_matrix.T
                        ) + self._measure_noise
                    )
                )
                
                state['state'] = state['state'] + np.dot(
                    kalman_gain,
                    (measurement - np.dot(self._measure_matrix, state['state']))
                )
                
                state['covariance'] = np.dot(
                    (np.eye(4) - np.dot(kalman_gain, self._measure_matrix)),
                    state['covariance']
                )
            
            # Update track history
            if track_id in self._track_history:
                self._track_history[track_id].append(track.bbox)
                if len(self._track_history[track_id]) > self._history_size:
                    self._track_history[track_id].popleft()
            
            # Update velocity
            if len(self._track_history[track_id]) >= 2:
                prev_box = self._track_history[track_id][-2]
                curr_box = track.bbox
                dx = curr_box[0] - prev_box[0]
                dy = curr_box[1] - prev_box[1]
                track.velocity = (dx, dy)
                
        except Exception as e:
            self.logger.error(f"Track update failed: {str(e)}")

    async def _check_anti_spoofing(self, frame: np.ndarray, detection: FaceDetection) -> float:
        """Perform comprehensive anti-spoofing check"""
        try:
            # Extract face region
            x, y, w, h = detection.bbox
            face = frame[y:y+h, x:x+w]
            
            # Prepare input blob
            blob = cv2.dnn.blobFromImage(
                face, 1.0, (224, 224),
                (104.0, 177.0, 123.0)
            )
            
            # Texture analysis
            self._texture_analyzer.setInput(blob)
            texture_score = float(self._texture_analyzer.forward())
            
            # Depth estimation
            self._depth_estimator.setInput(blob)
            depth_score = float(self._depth_estimator.forward())
            
            # Blink detection
            self._blink_detector.setInput(blob)
            blink_score = float(self._blink_detector.forward())
            
            # Combine scores
            scores = [texture_score, depth_score, blink_score]
            weights = [0.4, 0.4, 0.2]  # Adjustable weights
            
            final_score = sum(s * w for s, w in zip(scores, weights))
            
            return final_score
            
        except Exception as e:
            self.logger.error(f"Anti-spoofing check failed: {str(e)}")
            return 0.0

    async def _create_track(self, detection: FaceDetection, frame: np.ndarray) -> None:
        """Create new track"""
        try:
            track_id = str(self._next_track_id)
            self._next_track_id += 1
            
            # Initialize track
            self._tracks[track_id] = TrackingInfo(
                track_id=track_id,
                bbox=detection.bbox,
                confidence=detection.confidence,
                velocity=(0, 0),
                age=1,
                last_seen=datetime.utcnow()
            )
            
            # Initialize Kalman filter state
            self._kalman_states[track_id] = {
                'state': np.array([
                    [detection.bbox[0]],
                    [detection.bbox[1]],
                    [0],
                    [0]
                ]),
                'covariance': np.eye(4)
            }
            
            # Initialize track history
            self._track_history[track_id] = deque(maxlen=self._history_size)
            self._track_history[track_id].append(detection.bbox)
            
            # Perform initial anti-spoofing check
            anti_spoof_score = await self._check_anti_spoofing(frame, detection)
            self._tracks[track_id].anti_spoof_score = anti_spoof_score
            
            self.logger.info(f"Created new track {track_id}")
            
        except Exception as e:
            self.logger.error(f"Track creation failed: {str(e)}")

    async def _remove_old_tracks(self) -> None:
        """Remove old tracks"""
        try:
            current_time = datetime.utcnow()
            tracks_to_remove = []
            
            for track_id, track in self._tracks.items():
                time_since_update = (current_time - track.last_seen).total_seconds()
                
                if time_since_update > self._max_age:
                    tracks_to_remove.append(track_id)
                    
            for track_id in tracks_to_remove:
                del self._tracks[track_id]
                if track_id in self._kalman_states:
                    del self._kalman_states[track_id]
                if track_id in self._track_history:
                    del self._track_history[track_id]
                    
            if tracks_to_remove:
                self.logger.info(f"Removed {len(tracks_to_remove)} old tracks")
                
        except Exception as e:
            self.logger.error(f"Track removal failed: {str(e)}")

    def _calculate_iou(self, bbox1: Tuple[int, int, int, int], bbox2: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union between two bounding boxes"""
        try:
            # Convert to (x1, y1, x2, y2) format
            b1_x1, b1_y1 = bbox1[0], bbox1[1]
            b1_x2, b1_y2 = bbox1[0] + bbox1[2], bbox1[1] + bbox1[3]
            b2_x1, b2_y1 = bbox2[0], bbox2[1]
            b2_x2, b2_y2 = bbox2[0] + bbox2[2], bbox2[1] + bbox2[3]
            
            # Calculate intersection area
            inter_x1 = max(b1_x1, b2_x1)
            inter_y1 = max(b1_y1, b2_y1)
            inter_x2 = min(b1_x2, b2_x2)
            inter_y2 = min(b1_y2, b2_y2)
            
            if inter_x2 < inter_x1 or inter_y2 < inter_y1:
                return 0.0
                
            inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
            
            # Calculate union area
            b1_area = (b1_x2 - b1_x1) * (b1_y2 - b1_y1)
            b2_area = (b2_x2 - b2_x1) * (b2_y2 - b2_y1)
            union_area = b1_area + b2_area - inter_area
            
            return inter_area / union_area if union_area > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"IoU calculation failed: {str(e)}")
            return 0.0

    def _update_stats(self) -> None:
        """Update tracking statistics"""
        try:
            self._stats['active_tracks'] = len(self._tracks)
            self._stats['total_tracks'] = self._next_track_id
            
            if self._tracks:
                avg_age = sum(track.age for track in self._tracks.values()) / len(self._tracks)
                self._stats['average_track_length'] = avg_age
                
        except Exception as e:
            self.logger.error(f"Stats update failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get current tracking statistics"""
        return self._stats.copy() 