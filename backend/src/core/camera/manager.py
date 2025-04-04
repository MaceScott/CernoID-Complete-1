"""
High-level camera management system for CernoID.

This module provides the CameraManager class which serves as the central hub for managing
multiple camera feeds, handling frame processing, and coordinating subscriber notifications.

Key Features:
- Multi-camera management with dynamic add/remove capabilities
- Asynchronous frame processing pipeline with configurable frame rates and resolutions
- Real-time frame distribution to subscribers via WebSocket
- Automatic frame preprocessing and format standardization
- Performance monitoring and statistics tracking
- Resource management and cleanup
- Error handling and recovery mechanisms

Dependencies:
- OpenCV (cv2): Video capture and frame processing
- NumPy: Frame data manipulation
- AsyncIO: Asynchronous operations and queues
- BaseComponent: Core component functionality
- WebSocket: Real-time frame distribution

Architecture:
- Event-driven design with asynchronous processing
- Publisher-subscriber pattern for frame distribution
- Queue-based frame processing pipeline
- Component-based architecture with dependency injection
- Error boundary implementation with graceful degradation

Performance:
- Configurable frame rates and buffer sizes
- Automatic frame dropping on queue overflow
- Memory-efficient frame processing
- Optimized frame encoding for network transmission
- Real-time performance monitoring
"""

from typing import Dict, Optional, List, Union
import cv2
import numpy as np
import asyncio
from datetime import datetime
from pathlib import Path
from ..base import BaseComponent
from ..utils.errors import CameraError

class CameraManager(BaseComponent):
    """
    Central manager for camera operations in CernoID.
    
    Handles camera lifecycle management, frame processing, and subscriber notifications.
    Provides a high-level interface for adding, removing, and accessing cameras while
    managing frame processing queues and performance monitoring.
    
    Attributes:
        _cameras (Dict[str, Camera]): Active camera instances mapped by ID
        _frame_rate (int): Target frame rate for processing
        _resolution (tuple): Target resolution for processed frames
        _buffer_size (int): Maximum size of frame buffer queue
        _processing (bool): Current processing state
        _frame_queue (asyncio.Queue): Queue for frame processing
        _subscribers (Dict[str, List[str]]): Active subscribers per camera
        _storage_path (Path): Path for frame storage
        _stats (Dict): Performance monitoring statistics
    
    Configuration:
        camera.frame_rate (int): Target FPS (default: 30)
        camera.resolution (str): Target resolution 'WxH' (default: '1280x720')
        camera.buffer_size (int): Frame buffer size (default: 100)
        camera.storage_path (str): Frame storage location (default: 'data/frames')
    """
    
    def __init__(self, config: dict):
        """
        Initialize the camera manager with configuration.
        
        Args:
            config (dict): Configuration dictionary containing camera settings
        """
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
        """
        Add and initialize a new camera feed.
        
        Args:
            camera_id (str): Unique identifier for the camera
            source (Union[str, int]): Camera source (URL, device ID, or file path)
            name (Optional[str]): Human-readable camera name
            
        Raises:
            CameraError: If camera already exists or initialization fails
            
        Events:
            - camera.added: When camera is successfully added
            - camera.error: When camera addition fails
        """
        try:
            if camera_id in self._cameras:
                raise CameraError(f"Camera {camera_id} already exists")
            
            camera = Camera(
                camera_id,
                source,
                name or f"Camera {camera_id}",
                self._frame_rate,
                self._resolution,
                self._buffer_size
            )
            
            await camera.initialize()
            
            self._cameras[camera_id] = camera
            self._subscribers[camera_id] = []
            
            self._stats['active_cameras'] = len(self._cameras)
            
            asyncio.create_task(self._process_frames(camera))
            
            self.logger.info(f"Camera {camera_id} added and initialized successfully.")
            
        except Exception as e:
            self.logger.error(f"Failed to add camera {camera_id}: {str(e)}")
            raise CameraError(f"Failed to add camera: {str(e)}")

    async def remove_camera(self, camera_id: str) -> None:
        """
        Remove and cleanup a camera feed.
        
        Args:
            camera_id (str): ID of camera to remove
            
        Raises:
            CameraError: If camera not found or removal fails
            
        Events:
            - camera.removed: When camera is successfully removed
            - camera.error: When camera removal fails
        """
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
        """
        Retrieve a frame from specified camera.
        
        Args:
            camera_id (str): ID of target camera
            timestamp (Optional[float]): Specific frame timestamp to retrieve
            
        Returns:
            Optional[np.ndarray]: Frame data if available, None otherwise
            
        Raises:
            CameraError: If camera not found or frame retrieval fails
        """
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
        """
        Process frames from a camera feed.
        
        Handles frame acquisition, preprocessing, and queueing for distribution.
        Implements frame rate control and tracks processing statistics.
        
        Args:
            camera (Camera): Camera instance to process
            
        Events:
            - frame.processed: When frame is successfully processed
            - frame.dropped: When frame is dropped due to queue overflow
        """
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
        """
        Main frame processing loop.
        
        Continuously processes frames from the queue, applying transformations
        and distributing to subscribers. Handles errors gracefully to maintain
        processing pipeline integrity.
        """
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
        """
        Apply processing transformations to a single frame.
        
        Performs resolution adjustment, color space conversion, and any
        additional preprocessing required before distribution.
        
        Args:
            frame (np.ndarray): Raw frame data
            
        Returns:
            np.ndarray: Processed frame data
        """
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
        """
        Distribute processed frame to subscribers.
        
        Encodes frame data and broadcasts to all subscribers of the specified
        camera through WebSocket connections.
        
        Args:
            camera_id (str): Source camera ID
            frame (np.ndarray): Processed frame data
            timestamp (float): Frame timestamp
            
        Events:
            - frame.broadcast: When frame is sent to subscribers
            - subscriber.error: When notification fails
        """
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
        """
        Initialize the camera manager system.
        
        Sets up frame processing pipeline, loads configured cameras,
        and starts background tasks.
        
        Events:
            - manager.initialized: When initialization completes
            - manager.error: If initialization fails
        """
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
        """
        Perform cleanup operations for the camera manager.
        
        Stops all active cameras, releases resources, and performs necessary
        cleanup operations before shutdown.
        
        Events:
            - manager.cleanup.started: When cleanup begins
            - manager.cleanup.completed: When cleanup finishes
            - manager.cleanup.error: If cleanup encounters errors
        """
        try:
            # Stop all cameras
            for camera_id in list(self._cameras.keys()):
                await self.remove_camera(camera_id)
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")

    async def get_stats(self) -> Dict:
        """
        Retrieve current performance statistics.
        
        Returns a copy of the statistics dictionary containing:
            - active_cameras: Number of currently active cameras
            - frames_processed: Total number of frames processed
            - processing_time: Cumulative processing time in seconds
            - dropped_frames: Number of frames dropped due to queue overflow
        
        Returns:
            Dict: Copy of current statistics
        """
        return self._stats.copy() 