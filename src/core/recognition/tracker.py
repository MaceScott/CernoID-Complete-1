from typing import Dict, List, Optional, Tuple
import numpy as np
import cv2
from dataclasses import dataclass
from datetime import datetime
import asyncio
from collections import deque

from ..base import BaseComponent
from ..utils.errors import TrackingError

@dataclass
class TrackingInfo:
    """Face tracking information"""
    track_id: str
    bbox: Tuple[int, int, int, int]
    confidence: float
    velocity: Tuple[float, float]
    age: int  # track age in frames
    last_seen: datetime
    face_id: Optional[str] = None
    features: Optional[np.ndarray] = None

class FaceTracker(BaseComponent):
    """Advanced face tracking system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Tracking settings
        self._max_age = config.get('tracking.max_age', 30)
        self._min_hits = config.get('tracking.min_hits', 3)
        self._iou_threshold = config.get('tracking.iou_threshold', 0.3)
        self._max_tracks = config.get('tracking.max_tracks', 50)
        
        # Initialize Kalman filter parameters
        self._init_kalman_parameters()
        
        # Active tracks
        self._tracks: Dict[str, TrackingInfo] = {}
        self._next_track_id = 0
        
        # Track history for motion analysis
        self._track_history: Dict[str, deque] = {}
        self._history_size = config.get('tracking.history_size', 30)
        
        # Motion prediction
        self._prediction_enabled = config.get('tracking.predict_motion', True)
        self._prediction_horizon = config.get('tracking.prediction_frames', 5)
        
        # Statistics
        self._stats = {
            'active_tracks': 0,
            'total_tracks': 0,
            'average_track_length': 0.0,
            'track_switches': 0
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

    async def update(self,
                    detections: List[Dict],
                    frame: np.ndarray) -> List[TrackingInfo]:
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

    def _predict_tracks(self) -> None:
        """Predict track locations using Kalman filter"""
        try:
            for track_id, state in self._kalman_states.items():
                if track_id not in self._tracks:
                    continue
                
                # Predict next state
                predicted_state = np.dot(
                    self._state_matrix,
                    state['state']
                )
                predicted_cov = np.dot(
                    np.dot(self._state_matrix, state['covariance']),
                    self._state_matrix.T
                ) + self._process_noise
                
                # Update state
                state['state'] = predicted_state
                state['covariance'] = predicted_cov
                
                # Update track bbox
                track = self._tracks[track_id]
                x, y, w, h = track.bbox
                dx, dy = predicted_state[2:4]
                
                new_bbox = (
                    int(x + dx),
                    int(y + dy),
                    w, h
                )
                self._tracks[track_id].bbox = new_bbox
                
        except Exception as e:
            self.logger.error(f"Track prediction failed: {str(e)}")

    async def _match_detections(self,
                              detections: List[Dict]) -> Tuple[List, List, List]:
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
                        det['bbox']
                    )
            
            # Apply Hungarian algorithm
            from scipy.optimize import linear_sum_assignment
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

    async def _update_track(self,
                          track_id: str,
                          detection: Dict,
                          frame: np.ndarray) -> None:
        """Update matched track"""
        try:
            track = self._tracks[track_id]
            
            # Update bbox and confidence
            track.bbox = detection['bbox']
            track.confidence = detection['confidence']
            track.last_seen = datetime.utcnow()
            track.age += 1
            
            # Update Kalman filter
            if track_id in self._kalman_states:
                measurement = np.array([
                    [detection['bbox'][0]],
                    [detection['bbox'][1]]
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

    async def _update_unmatched_track(self, track_id: str) -> None:
        """Update unmatched track"""
        try:
            track = self._tracks[track_id]
            track.age += 1
            
            # Predict location using velocity
            if self._prediction_enabled and track.velocity != (0, 0):
                x, y, w, h = track.bbox
                dx, dy = track.velocity
                track.bbox = (int(x + dx), int(y + dy), w, h)
            
        except Exception as e:
            self.logger.error(f"Unmatched track update failed: {str(e)}")

    async def _create_track(self, detection: Dict, frame: np.ndarray) -> None:
        """Create new track from detection"""
        try:
            track_id = str(self._next_track_id)
            self._next_track_id += 1
            
            # Create track
            track = TrackingInfo(
                track_id=track_id,
                bbox=detection['bbox'],
                confidence=detection['confidence'],
                velocity=(0, 0),
                age=1,
                last_seen=datetime.utcnow()
            )
            
            # Initialize Kalman filter
            self._kalman_states[track_id] = {
                'state': np.array([
                    [detection['bbox'][0]],
                    [detection['bbox'][1]],
                    [0],
                    [0]
                ]),
                'covariance': np.eye(4)
            }
            
            # Initialize track history
            self._track_history[track_id] = deque(maxlen=self._history_size)
            self._track_history[track_id].append(detection['bbox'])
            
            # Add track
            self._tracks[track_id] = track
            self._stats['total_tracks'] += 1
            
        except Exception as e:
            self.logger.error(f"Track creation failed: {str(e)}")

    async def _remove_old_tracks(self) -> None:
        """Remove old tracks"""
        try:
            current_time = datetime.utcnow()
            
            remove_ids = []
            for track_id, track in self._tracks.items():
                time_since_update = (current_time - track.last_seen).total_seconds()
                
                if (time_since_update > self._max_age or 
                    track.age < self._min_hits):
                    remove_ids.append(track_id)
            
            # Remove tracks
            for track_id in remove_ids:
                self._tracks.pop(track_id)
                self._kalman_states.pop(track_id, None)
                self._track_history.pop(track_id, None)
            
        except Exception as e:
            self.logger.error(f"Track removal failed: {str(e)}")

    def _calculate_iou(self,
                      bbox1: Tuple[int, int, int, int],
                      bbox2: Tuple[int, int, int, int]) -> float:
        """Calculate IoU between two bounding boxes"""
        try:
            x1, y1, w1, h1 = bbox1
            x2, y2, w2, h2 = bbox2
            
            # Calculate intersection
            x_left = max(x1, x2)
            y_top = max(y1, y2)
            x_right = min(x1 + w1, x2 + w2)
            y_bottom = min(y1 + h1, y2 + h2)
            
            if x_right < x_left or y_bottom < y_top:
                return 0.0
            
            intersection = (x_right - x_left) * (y_bottom - y_top)
            
            # Calculate union
            area1 = w1 * h1
            area2 = w2 * h2
            union = area1 + area2 - intersection
            
            return intersection / union
            
        except Exception:
            return 0.0

    def _update_stats(self) -> None:
        """Update tracking statistics"""
        self._stats['active_tracks'] = len(self._tracks)
        
        if self._stats['total_tracks'] > 0:
            total_age = sum(track.age for track in self._tracks.values())
            self._stats['average_track_length'] = \
                total_age / self._stats['total_tracks']

    async def get_stats(self) -> Dict:
        """Get tracker statistics"""
        return self._stats.copy() 