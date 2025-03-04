"""Camera handler for facial recognition system"""

from typing import Dict, Optional, Any, List, Union, Tuple
import asyncio
import cv2
import numpy as np
from datetime import datetime
from ..base import BaseComponent
from ..utils.errors import handle_errors, CameraError
from .core import FaceRecognitionSystem

class Camera(BaseComponent):
    """Camera handler for facial recognition system"""
    
    def __init__(self,
                 camera_id: str,
                 config: Dict,
                 frame_interval: int,
                 recognition_system: FaceRecognitionSystem):
        super().__init__(config)
        self.id = camera_id
        self._recognition = recognition_system
        self._source = config.get('source', 0)  # Camera source/URL
        self._resolution = config.get('resolution', (1280, 720))
        self._fps = config.get('fps', 30)
        self._frame_interval = frame_interval
        self._frame_count = 0
        self._capture = None
        self._running = False
        self._current_frame = None
        self._last_frame_time = None
        self._processing_enabled = config.get('processing_enabled', True)
        self._recording_enabled = config.get('recording_enabled', False)
        self._recording_path = config.get('recording_path', 'recordings')
        self._writer = None
        self._stats = {
            'frames_captured': 0,
            'frames_processed': 0,
            'faces_detected': 0,
            'fps': 0.0,
            'uptime': 0
        }
        self._start_time = None

    async def initialize(self) -> None:
        """Initialize camera"""
        try:
            # Create capture object
            self._capture = cv2.VideoCapture(self._source)
            
            # Set camera properties
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._resolution[0])
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._resolution[1])
            self._capture.set(cv2.CAP_PROP_FPS, self._fps)
            
            if not self._capture.isOpened():
                raise CameraError(f"Failed to open camera: {self._source}")
            
            # Initialize recording if enabled
            if self._recording_enabled:
                await self._initialize_recording()
            
            # Start camera loop
            self._running = True
            self._start_time = datetime.utcnow()
            asyncio.create_task(self._camera_loop())
            
        except Exception as e:
            raise CameraError(f"Camera initialization failed: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup camera resources"""
        try:
            self._running = False
            
            if self._capture:
                self._capture.release()
                
            if self._writer:
                self._writer.release()
                
        except Exception as e:
            self.logger.error(f"Camera cleanup error: {str(e)}")

    async def get_frame(self) -> Optional[np.ndarray]:
        """Get current frame"""
        return self._current_frame

    async def get_processed_frame(self) -> Optional[np.ndarray]:
        """Get processed frame with recognition results"""
        try:
            frame = self._current_frame
            if frame is None:
                return None
            
            # Process frame if enabled
            if self._processing_enabled:
                frame = frame.copy()
                
                # Get recognition results
                match = await self._recognition.verify_face(frame)
                
                # Draw results on frame
                if match:
                    frame = await self._draw_results(frame, match)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")
            return self._current_frame

    async def enable_processing(self) -> None:
        """Enable face processing"""
        self._processing_enabled = True

    async def disable_processing(self) -> None:
        """Disable face processing"""
        self._processing_enabled = False

    async def enable_recording(self) -> None:
        """Enable video recording"""
        if not self._recording_enabled:
            self._recording_enabled = True
            await self._initialize_recording()

    async def disable_recording(self) -> None:
        """Disable video recording"""
        self._recording_enabled = False
        if self._writer:
            self._writer.release()
            self._writer = None

    async def get_stats(self) -> Dict[str, Any]:
        """Get camera statistics"""
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
            self._stats['uptime'] = uptime
            
            if uptime > 0:
                self._stats['fps'] = self._stats['frames_captured'] / uptime
                
        return self._stats.copy()

    async def _camera_loop(self) -> None:
        """Main camera loop"""
        while self._running:
            try:
                # Read frame
                ret, frame = self._capture.read()
                
                if not ret:
                    self.logger.error("Failed to read frame")
                    await asyncio.sleep(0.1)
                    continue
                
                # Update frame
                self._current_frame = frame
                self._last_frame_time = datetime.utcnow()
                self._frame_count += 1
                self._stats['frames_captured'] += 1
                
                # Record frame if enabled
                if self._recording_enabled and self._writer:
                    self._writer.write(frame)
                
                # Process frame if enabled and interval reached
                if (self._processing_enabled and 
                    self._frame_count % self._frame_interval == 0):
                    asyncio.create_task(self._process_frame(frame))
                
                # Control frame rate
                await asyncio.sleep(1.0 / self._fps)
                
            except Exception as e:
                self.logger.error(f"Camera loop error: {str(e)}")
                await asyncio.sleep(1)

    async def _process_frame(self, frame: np.ndarray) -> None:
        """Process frame for face detection"""
        try:
            match = await self._recognition.verify_face(frame)
            self._stats['frames_processed'] += 1
            
            if match:
                self._stats['faces_detected'] += 1
                await self.app.events.emit(
                    'vision.face_detected',
                    {
                        'camera_id': self.id,
                        'match': match,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")

    async def _draw_results(self,
                          frame: np.ndarray,
                          match: Dict) -> np.ndarray:
        """Draw recognition results on frame"""
        # Get face location from match
        bbox = match.get('bbox', None)
        if not bbox:
            return frame
            
        x, y, w, h = bbox
        
        # Set color based on confidence
        confidence = match.get('confidence', 0)
        if confidence > 0.8:
            color = (0, 255, 0)  # High confidence - green
        elif confidence > 0.6:
            color = (255, 165, 0)  # Medium confidence - orange
        else:
            color = (0, 0, 255)  # Low confidence - red
        
        # Draw box
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            color,
            2
        )
        
        # Draw label
        name = match.get('metadata', {}).get('name', 'Unknown')
        confidence_text = f"{confidence*100:.1f}%"
        cv2.putText(
            frame,
            f"{name} ({confidence_text})",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )
        
        return frame

    async def _initialize_recording(self) -> None:
        """Initialize video recording"""
        try:
            from pathlib import Path
            
            # Create recording directory
            recording_dir = Path(self._recording_path)
            recording_dir.mkdir(parents=True, exist_ok=True)
            
            # Create video writer
            filename = f"{self.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.avi"
            filepath = recording_dir / filename
            
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self._writer = cv2.VideoWriter(
                str(filepath),
                fourcc,
                self._fps,
                self._resolution
            )
            
            if not self._writer.isOpened():
                raise CameraError("Failed to initialize video writer")
                
            self.logger.info(f"Recording initialized: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Recording initialization failed: {str(e)}")
            self._recording_enabled = False 