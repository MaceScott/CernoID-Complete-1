"""
Video feed processing for face recognition.
"""
import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from .matcher import FaceMatcher, MatchResult
from .anti_spoofing import analyze_frame

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

@dataclass
class VideoFrame:
    """Processed video frame with face detection results"""
    frame: np.ndarray
    face_locations: List[Tuple[int, int, int, int]]
    face_encodings: List[np.ndarray]
    matches: List[Optional[MatchResult]]
    timestamp: datetime

class VideoProcessor:
    """Process video feed for face recognition"""
    
    def __init__(self, matcher: FaceMatcher, config: dict):
        self.matcher = matcher
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Video settings
        self._frame_scale = config.get('video.frame_scale', 0.25)
        self._display_size = config.get('video.display_size', (800, 600))
        self._max_faces = config.get('video.max_faces', 10)
        
        # Processing settings
        self._process_every_n_frames = config.get('video.process_every_n_frames', 1)
        self._frame_count = 0
        
        # Statistics
        self._stats = {
            'frames_processed': 0,
            'faces_detected': 0,
            'faces_matched': 0,
            'processing_time': 0.0
        }

    async def process_frame(self, frame: np.ndarray) -> VideoFrame:
        """Process a single frame for face recognition"""
        try:
            start_time = datetime.now()
            
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), 
                                   fx=self._frame_scale, 
                                   fy=self._frame_scale)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = self._detect_faces(rgb_frame)
            if not face_locations:
                return VideoFrame(frame, [], [], [], start_time)
            
            # Get face encodings
            face_encodings = self._get_face_encodings(rgb_frame, face_locations)
            
            # Match faces
            matches = await self._match_faces(face_encodings)
            
            # Update statistics
            self._update_stats(len(face_locations), len(matches))
            
            return VideoFrame(
                frame=frame,
                face_locations=face_locations,
                face_encodings=face_encodings,
                matches=matches,
                timestamp=start_time
            )
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")
            return VideoFrame(frame, [], [], [], datetime.now())

    def _detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces in frame"""
        try:
            # Anti-spoofing check
            if not analyze_frame(frame):
                self.logger.warning("Potential spoofing attempt detected")
                return []
            
            # Detect faces
            face_locations = self.matcher.detect_faces(frame)
            
            # Limit number of faces
            if len(face_locations) > self._max_faces:
                face_locations = face_locations[:self._max_faces]
            
            return face_locations
            
        except Exception as e:
            self.logger.error(f"Face detection error: {str(e)}")
            return []

    def _get_face_encodings(self, 
                          frame: np.ndarray,
                          face_locations: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
        """Get face encodings for detected faces"""
        try:
            return self.matcher.encode_faces(frame, face_locations)
        except Exception as e:
            self.logger.error(f"Face encoding error: {str(e)}")
            return []

    async def _match_faces(self, 
                         face_encodings: List[np.ndarray]) -> List[Optional[MatchResult]]:
        """Match face encodings against known faces"""
        try:
            matches = []
            for encoding in face_encodings:
                match = await self.matcher.find_matches(encoding)
                matches.append(match[0] if match else None)
            return matches
        except Exception as e:
            self.logger.error(f"Face matching error: {str(e)}")
            return [None] * len(face_encodings)

    def _update_stats(self, faces_detected: int, faces_matched: int) -> None:
        """Update processing statistics"""
        self._stats['frames_processed'] += 1
        self._stats['faces_detected'] += faces_detected
        self._stats['faces_matched'] += faces_matched

    def get_stats(self) -> dict:
        """Get current processing statistics"""
        return self._stats.copy()

    def draw_results(self, frame: np.ndarray, results: VideoFrame) -> np.ndarray:
        """Draw face detection and recognition results on frame"""
        try:
            # Scale coordinates back to original frame size
            scale = 1 / self._frame_scale
            
            for i, (location, match) in enumerate(zip(results.face_locations, results.matches)):
                # Scale coordinates
                top, right, bottom, left = [int(coord * scale) for coord in location]
                
                # Choose color based on match
                color = (0, 255, 0) if match else (0, 0, 255)
                
                # Draw rectangle
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Add label
                label = match.person_id if match else "Unknown"
                cv2.putText(frame, label, (left, top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Add confidence if available
                if match:
                    conf_text = f"{match.confidence:.2f}"
                    cv2.putText(frame, conf_text, (left, bottom + 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Resize for display
            return cv2.resize(frame, self._display_size)
            
        except Exception as e:
            self.logger.error(f"Error drawing results: {str(e)}")
            return frame 