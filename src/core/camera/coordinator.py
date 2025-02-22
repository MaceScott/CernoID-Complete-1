from typing import Dict, List, Optional, Set
import asyncio
from datetime import datetime
import numpy as np
from dataclasses import dataclass
import cv2

from ..base import BaseComponent
from ..utils.errors import CameraError

@dataclass
class CameraStatus:
    """Camera status information"""
    id: str
    name: str
    status: str  # 'active', 'inactive', 'error'
    resolution: tuple
    fps: float
    load: float
    last_frame: datetime
    error: Optional[str] = None

class CameraCoordinator(BaseComponent):
    """Multi-camera coordination system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Camera settings
        self._max_cameras = config.get('camera.max_cameras', 16)
        self._frame_interval = 1.0 / config.get('camera.target_fps', 30)
        self._resolution = self._parse_resolution(
            config.get('camera.resolution', '1280x720')
        )
        
        # Active cameras
        self._cameras: Dict[str, Dict] = {}
        self._active_feeds: Set[str] = set()
        
        # Processing queues
        self._frame_queues: Dict[str, asyncio.Queue] = {}
        self._priority_queues: Dict[str, asyncio.Queue] = {}
        
        # Load balancing
        self._camera_loads: Dict[str, float] = {}
        self._last_rebalance = datetime.utcnow()
        self._rebalance_interval = config.get('camera.rebalance_interval', 60)
        
        # Performance monitoring
        self._stats = {
            'active_cameras': 0,
            'total_frames': 0,
            'dropped_frames': 0,
            'average_latency': 0.0,
            'processing_load': 0.0
        }

    def _parse_resolution(self, resolution: str) -> tuple:
        """Parse resolution string (WxH)"""
        try:
            width, height = map(int, resolution.split('x'))
            return (width, height)
        except Exception:
            return (1280, 720)

    async def add_camera(self,
                        camera_id: str,
                        name: str,
                        source: str,
                        priority: int = 1) -> None:
        """Add new camera to coordinator"""
        try:
            if len(self._cameras) >= self._max_cameras:
                raise CameraError("Maximum number of cameras reached")
            
            if camera_id in self._cameras:
                raise CameraError(f"Camera {camera_id} already exists")
            
            # Initialize camera
            camera = {
                'id': camera_id,
                'name': name,
                'source': source,
                'priority': priority,
                'status': 'inactive',
                'resolution': self._resolution,
                'fps': 0.0,
                'frame_count': 0,
                'last_frame': None,
                'error': None
            }
            
            # Create queues
            self._frame_queues[camera_id] = asyncio.Queue(maxsize=100)
            if priority > 1:
                self._priority_queues[camera_id] = asyncio.Queue(maxsize=50)
            
            # Store camera
            self._cameras[camera_id] = camera
            
            # Start camera feed
            await self._start_camera_feed(camera_id)
            
            self._stats['active_cameras'] = len(self._active_feeds)
            
        except Exception as e:
            raise CameraError(f"Failed to add camera: {str(e)}")

    async def remove_camera(self, camera_id: str) -> None:
        """Remove camera from coordinator"""
        try:
            if camera_id not in self._cameras:
                return
                
            # Stop camera feed
            await self._stop_camera_feed(camera_id)
            
            # Clean up queues
            self._frame_queues.pop(camera_id, None)
            self._priority_queues.pop(camera_id, None)
            
            # Remove camera
            self._cameras.pop(camera_id)
            self._active_feeds.discard(camera_id)
            self._camera_loads.pop(camera_id, None)
            
            self._stats['active_cameras'] = len(self._active_feeds)
            
        except Exception as e:
            self.logger.error(f"Failed to remove camera: {str(e)}")

    async def _start_camera_feed(self, camera_id: str) -> None:
        """Start camera feed processing"""
        try:
            camera = self._cameras[camera_id]
            
            # Initialize video capture
            cap = cv2.VideoCapture(camera['source'])
            if not cap.isOpened():
                raise CameraError(f"Failed to open camera source: {camera['source']}")
            
            # Set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._resolution[1])
            
            # Start feed processor
            camera['capture'] = cap
            camera['status'] = 'active'
            self._active_feeds.add(camera_id)
            
            # Start processing task
            asyncio.create_task(
                self._process_feed(camera_id)
            )
            
        except Exception as e:
            camera['status'] = 'error'
            camera['error'] = str(e)
            self.logger.error(f"Failed to start camera feed: {str(e)}")

    async def _process_feed(self, camera_id: str) -> None:
        """Process camera feed"""
        camera = self._cameras[camera_id]
        cap = camera['capture']
        
        last_frame_time = datetime.utcnow()
        frame_times = []
        
        while camera_id in self._active_feeds:
            try:
                # Check frame interval
                now = datetime.utcnow()
                if (now - last_frame_time).total_seconds() < self._frame_interval:
                    await asyncio.sleep(0.001)
                    continue
                
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    raise CameraError("Failed to read frame")
                
                # Update timing
                last_frame_time = now
                frame_times.append(now)
                if len(frame_times) > 30:
                    frame_times.pop(0)
                
                # Calculate FPS
                if len(frame_times) > 1:
                    fps = len(frame_times) / (frame_times[-1] - frame_times[0]).total_seconds()
                    camera['fps'] = fps
                
                # Process frame
                await self._handle_frame(camera_id, frame)
                
                # Update statistics
                camera['frame_count'] += 1
                camera['last_frame'] = now
                self._stats['total_frames'] += 1
                
            except Exception as e:
                camera['status'] = 'error'
                camera['error'] = str(e)
                self.logger.error(f"Feed processing error: {str(e)}")
                await asyncio.sleep(1)

    async def _handle_frame(self, camera_id: str, frame: np.ndarray) -> None:
        """Handle incoming frame"""
        try:
            camera = self._cameras[camera_id]
            
            # Resize if needed
            if frame.shape[:2] != self._resolution:
                frame = cv2.resize(frame, self._resolution)
            
            # Add to queues
            frame_data = {
                'camera_id': camera_id,
                'frame': frame,
                'timestamp': datetime.utcnow().timestamp(),
                'priority': camera['priority']
            }
            
            # Try priority queue first
            if camera_id in self._priority_queues:
                try:
                    self._priority_queues[camera_id].put_nowait(frame_data)
                    return
                except asyncio.QueueFull:
                    pass
            
            # Try regular queue
            try:
                self._frame_queues[camera_id].put_nowait(frame_data)
            except asyncio.QueueFull:
                self._stats['dropped_frames'] += 1
            
        except Exception as e:
            self.logger.error(f"Frame handling error: {str(e)}")

    async def get_frame(self, camera_id: str) -> Optional[Dict]:
        """Get next frame from camera"""
        try:
            if camera_id not in self._cameras:
                return None
                
            # Check priority queue first
            if camera_id in self._priority_queues:
                try:
                    return self._priority_queues[camera_id].get_nowait()
                except asyncio.QueueEmpty:
                    pass
            
            # Check regular queue
            try:
                return self._frame_queues[camera_id].get_nowait()
            except asyncio.QueueEmpty:
                return None
                
        except Exception as e:
            self.logger.error(f"Frame retrieval error: {str(e)}")
            return None

    async def get_camera_status(self, camera_id: str) -> Optional[CameraStatus]:
        """Get camera status"""
        try:
            if camera_id not in self._cameras:
                return None
                
            camera = self._cameras[camera_id]
            return CameraStatus(
                id=camera['id'],
                name=camera['name'],
                status=camera['status'],
                resolution=camera['resolution'],
                fps=camera['fps'],
                load=self._camera_loads.get(camera_id, 0.0),
                last_frame=camera['last_frame'],
                error=camera['error']
            )
            
        except Exception as e:
            self.logger.error(f"Status retrieval error: {str(e)}")
            return None

    async def get_stats(self) -> Dict:
        """Get coordinator statistics"""
        return self._stats.copy() 