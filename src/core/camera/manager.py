from typing import Dict, Optional, List, Union
import cv2
import numpy as np
import asyncio
from datetime import datetime
from pathlib import Path
from ..base import BaseComponent
from ..utils.errors import CameraError

class CameraManager(BaseComponent):
    """Camera feed management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # Camera settings
        self._cameras: Dict[str, 'Camera'] = {}
        self._frame_rate = config.get('camera.frame_rate', 30)
        self._resolution = self._parse_resolution(
            config.get('camera.resolution', '1280x720')
        )
        self._buffer_size = config.get('camera.buffer_size', 100)
        
        # Frame processing
        self._processing = False
        self._frame_queue: asyncio.Queue = asyncio.Queue()
        self._subscribers: Dict[str, List[str]] = {}
        
        # Storage settings
        self._storage_path = Path(config.get('camera.storage_path', 'data/frames'))
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self._stats = {
            'active_cameras': 0,
            'frames_processed': 0,
            'processing_time': 0,
            'dropped_frames': 0
        }

    def _parse_resolution(self, resolution: str) -> tuple:
        """Parse resolution string (WxH)"""
        try:
            width, height = map(int, resolution.split('x'))
            return (width, height)
        except Exception:
            return (1280, 720)  # Default resolution

    async def add_camera(self,
                        camera_id: str,
                        source: Union[str, int],
                        name: Optional[str] = None) -> None:
        """Add new camera"""
        try:
            if camera_id in self._cameras:
                raise CameraError(f"Camera {camera_id} already exists")
            
            # Create camera instance
            camera = Camera(
                camera_id,
                source,
                name or f"Camera {camera_id}",
                self._frame_rate,
                self._resolution,
                self._buffer_size
            )
            
            # Initialize camera
            await camera.initialize()
            
            # Add to cameras
            self._cameras[camera_id] = camera
            self._subscribers[camera_id] = []
            
            # Update statistics
            self._stats['active_cameras'] = len(self._cameras)
            
            # Start frame processing
            asyncio.create_task(self._process_frames(camera))
            
        except Exception as e:
            raise CameraError(f"Failed to add camera: {str(e)}")

    async def remove_camera(self, camera_id: str) -> None:
        """Remove camera"""
        try:
            if camera_id not in self._cameras:
                raise CameraError(f"Camera {camera_id} not found")
            
            # Stop camera
            await self._cameras[camera_id].stop()
            
            # Remove camera
            del self._cameras[camera_id]
            del self._subscribers[camera_id]
            
            # Update statistics
            self._stats['active_cameras'] = len(self._cameras)
            
        except Exception as e:
            raise CameraError(f"Failed to remove camera: {str(e)}")

    async def get_frame(self,
                       camera_id: str,
                       timestamp: Optional[float] = None) -> Optional[np.ndarray]:
        """Get camera frame"""
        try:
            if camera_id not in self._cameras:
                raise CameraError(f"Camera {camera_id} not found")
            
            return await self._cameras[camera_id].get_frame(timestamp)
            
        except Exception as e:
            raise CameraError(f"Failed to get frame: {str(e)}")

    async def subscribe(self, camera_id: str, subscriber_id: str) -> None:
        """Subscribe to camera feed"""
        try:
            if camera_id not in self._cameras:
                raise CameraError(f"Camera {camera_id} not found")
            
            if subscriber_id not in self._subscribers[camera_id]:
                self._subscribers[camera_id].append(subscriber_id)
            
        except Exception as e:
            raise CameraError(f"Failed to subscribe: {str(e)}")

    async def unsubscribe(self, camera_id: str, subscriber_id: str) -> None:
        """Unsubscribe from camera feed"""
        try:
            if camera_id in self._subscribers:
                self._subscribers[camera_id].remove(subscriber_id)
            
        except Exception as e:
            raise CameraError(f"Failed to unsubscribe: {str(e)}")

    async def _process_frames(self, camera: 'Camera') -> None:
        """Process camera frames"""
        try:
            while camera.is_running:
                start_time = datetime.utcnow()
                
                # Get frame
                frame = await camera.get_frame()
                if frame is None:
                    continue
                
                # Add to processing queue
                try:
                    self._frame_queue.put_nowait({
                        'camera_id': camera.id,
                        'frame': frame,
                        'timestamp': start_time.timestamp()
                    })
                except asyncio.QueueFull:
                    self._stats['dropped_frames'] += 1
                
                # Update statistics
                self._stats['frames_processed'] += 1
                self._stats['processing_time'] += (
                    datetime.utcnow() - start_time
                ).total_seconds()
                
                # Control frame rate
                await asyncio.sleep(1 / self._frame_rate)
                
        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")

    async def _frame_processor(self) -> None:
        """Process frames from queue"""
        while True:
            try:
                # Get frame from queue
                frame_data = await self._frame_queue.get()
                
                # Process frame
                processed_frame = await self._process_frame(frame_data['frame'])
                
                # Notify subscribers
                await self._notify_subscribers(
                    frame_data['camera_id'],
                    processed_frame,
                    frame_data['timestamp']
                )
                
            except Exception as e:
                self.logger.error(f"Frame processor error: {str(e)}")
                await asyncio.sleep(1)

    async def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process single frame"""
        try:
            # Basic preprocessing
            processed = cv2.resize(
                frame,
                self._resolution,
                interpolation=cv2.INTER_AREA
            )
            
            # Convert to RGB
            if len(processed.shape) == 2:
                processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)
            elif processed.shape[2] == 4:
                processed = cv2.cvtColor(processed, cv2.COLOR_RGBA2RGB)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")
            return frame

    async def _notify_subscribers(self,
                                camera_id: str,
                                frame: np.ndarray,
                                timestamp: float) -> None:
        """Notify camera subscribers"""
        try:
            if camera_id in self._subscribers:
                # Encode frame
                success, encoded = cv2.imencode('.jpg', frame)
                if not success:
                    return
                
                # Create message
                message = {
                    'camera_id': camera_id,
                    'frame': encoded.tobytes(),
                    'timestamp': timestamp
                }
                
                # Send to subscribers
                for subscriber_id in self._subscribers[camera_id]:
                    try:
                        await self.app.websocket.broadcast(
                            'camera',
                            message
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to notify subscriber {subscriber_id}: {str(e)}"
                        )
                        
        except Exception as e:
            self.logger.error(f"Subscriber notification error: {str(e)}")

    async def initialize(self) -> None:
        """Initialize camera manager"""
        try:
            # Start frame processor
            asyncio.create_task(self._frame_processor())
            
            # Load configured cameras
            cameras = self.config.get('cameras', [])
            for camera in cameras:
                await self.add_camera(
                    camera['id'],
                    camera['source'],
                    camera.get('name')
                )
            
        except Exception as e:
            raise CameraError(f"Initialization failed: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup camera manager"""
        try:
            # Stop all cameras
            for camera_id in list(self._cameras.keys()):
                await self.remove_camera(camera_id)
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get camera statistics"""
        return self._stats.copy() 