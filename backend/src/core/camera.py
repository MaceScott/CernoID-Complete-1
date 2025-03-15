"""
File: camera.py
Purpose: Core camera management service for the CernoID system.

Key Features:
- Camera lifecycle management
- Video stream processing
- Frame capture and analysis
- Camera status monitoring
- Stream configuration management
- Resource optimization

Dependencies:
- OpenCV: Video capture and processing
- NumPy: Frame data handling
- Core services:
  - FaceRecognition: Frame analysis
  - Database: Camera storage
  - Logging: System logging
  - EventBus: System events

Components:
- CameraManager: Camera instance management
- StreamProcessor: Video stream handling
- FrameAnalyzer: Frame processing pipeline
- ResourceMonitor: System resource tracking
- EventHandler: System event handling

Performance:
- Stream optimization
- Frame rate control
- Memory management
- Resource pooling
- Connection management
- Error recovery
"""

from typing import Dict, Any, Optional, List, Tuple
import cv2
import numpy as np
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .base import BaseService
from .face_recognition import FaceRecognitionService
from .database import DatabaseService
from .event_bus import EventBus
from ..utils.logging import get_logger
from ..utils.errors import ServiceError

logger = get_logger(__name__)

class CameraService(BaseService):
    """
    Camera management service for handling video streams and camera operations.
    
    Features:
        - Camera instance management
        - Video stream processing
        - Frame analysis pipeline
        - Resource monitoring
        - Event handling
        
    Dependencies:
        - DatabaseService: Camera storage
        - FaceRecognitionService: Frame analysis
        - EventBus: System events
        - ThreadPoolExecutor: Async operations
        
    Configuration:
        - max_cameras: Maximum concurrent cameras
        - frame_buffer_size: Frame queue size
        - processing_threads: Analysis threads
        - stream_timeout: Connection timeout
        - reconnect_interval: Reconnection delay
    """
    
    def __init__(
        self,
        db_service: DatabaseService,
        face_service: FaceRecognitionService,
        event_bus: EventBus,
        max_cameras: int = 50,
        frame_buffer_size: int = 30,
        processing_threads: int = 4,
        stream_timeout: int = 30,
        reconnect_interval: int = 5
    ):
        """
        Initialize camera service.
        
        Args:
            db_service: Database service instance
            face_service: Face recognition service
            event_bus: Event bus for system events
            max_cameras: Maximum concurrent cameras
            frame_buffer_size: Frame queue size
            processing_threads: Analysis threads
            stream_timeout: Connection timeout
            reconnect_interval: Reconnection delay
            
        Raises:
            ServiceError: If initialization fails
        """
        super().__init__()
        self.db = db_service
        self.face_service = face_service
        self.event_bus = event_bus
        self.max_cameras = max_cameras
        self.frame_buffer_size = frame_buffer_size
        self.processing_threads = processing_threads
        self.stream_timeout = stream_timeout
        self.reconnect_interval = reconnect_interval
        
        self.cameras: Dict[int, Dict[str, Any]] = {}
        self.streams: Dict[int, cv2.VideoCapture] = {}
        self.frame_queues: Dict[int, asyncio.Queue] = {}
        self.processing_tasks: Dict[int, asyncio.Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=processing_threads)
        
        self._setup_event_handlers()
        
    async def start(self):
        """
        Start camera service.
        
        Raises:
            ServiceError: If service fails to start
        """
        try:
            # Load existing cameras
            cameras = await self.db.get_cameras()
            for camera in cameras:
                await self._initialize_camera(camera)
                
            logger.info("Camera service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start camera service: {str(e)}")
            raise ServiceError("Camera service start failed") from e
            
    async def stop(self):
        """
        Stop camera service and cleanup resources.
        
        Raises:
            ServiceError: If service fails to stop
        """
        try:
            # Stop all cameras
            for camera_id in list(self.cameras.keys()):
                await self._stop_camera(camera_id)
                
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            logger.info("Camera service stopped successfully")
            
        except Exception as e:
            logger.error(f"Failed to stop camera service: {str(e)}")
            raise ServiceError("Camera service stop failed") from e
            
    async def add_camera(
        self,
        name: str,
        url: str,
        location: str,
        group_id: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add new camera to the system.
        
        Args:
            name: Camera name
            url: Stream URL
            location: Physical location
            group_id: Optional group ID
            config: Optional stream configuration
            
        Returns:
            Dict[str, Any]: Created camera details
            
        Raises:
            ServiceError: If camera creation fails
        """
        try:
            # Validate camera count
            if len(self.cameras) >= self.max_cameras:
                raise ServiceError("Maximum camera limit reached")
                
            # Create camera record
            camera = await self.db.create_camera({
                "name": name,
                "url": url,
                "location": location,
                "group_id": group_id,
                "config": config or {},
                "is_active": True,
                "created_at": datetime.utcnow()
            })
            
            # Initialize camera
            await self._initialize_camera(camera)
            
            # Notify system
            await self.event_bus.emit(
                "camera:created",
                {"camera_id": camera["id"]}
            )
            
            return camera
            
        except Exception as e:
            logger.error(f"Failed to add camera: {str(e)}")
            raise ServiceError("Camera creation failed") from e
            
    async def get_camera(self, camera_id: int) -> Optional[Dict[str, Any]]:
        """
        Get camera details by ID.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Optional[Dict[str, Any]]: Camera details if found
            
        Raises:
            ServiceError: If retrieval fails
        """
        try:
            return await self.db.get_camera(camera_id)
            
        except Exception as e:
            logger.error(f"Failed to get camera: {str(e)}")
            raise ServiceError("Camera retrieval failed") from e
            
    async def update_camera(
        self,
        camera_id: int,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update camera settings.
        
        Args:
            camera_id: Camera identifier
            data: Update data
            
        Returns:
            Optional[Dict[str, Any]]: Updated camera details
            
        Raises:
            ServiceError: If update fails
        """
        try:
            # Update database
            camera = await self.db.update_camera(camera_id, data)
            if not camera:
                return None
                
            # Handle URL changes
            if "url" in data and data["url"] != camera["url"]:
                await self._restart_camera(camera_id)
                
            # Handle status changes
            if "is_active" in data:
                if data["is_active"]:
                    await self._start_camera(camera_id)
                else:
                    await self._stop_camera(camera_id)
                    
            # Notify system
            await self.event_bus.emit(
                "camera:updated",
                {"camera_id": camera_id, "changes": data}
            )
            
            return camera
            
        except Exception as e:
            logger.error(f"Failed to update camera: {str(e)}")
            raise ServiceError("Camera update failed") from e
            
    async def delete_camera(self, camera_id: int) -> bool:
        """
        Remove camera from the system.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ServiceError: If deletion fails
        """
        try:
            # Stop camera
            await self._stop_camera(camera_id)
            
            # Delete from database
            success = await self.db.delete_camera(camera_id)
            if not success:
                return False
                
            # Cleanup resources
            self.cameras.pop(camera_id, None)
            self.streams.pop(camera_id, None)
            self.frame_queues.pop(camera_id, None)
            self.processing_tasks.pop(camera_id, None)
            
            # Notify system
            await self.event_bus.emit(
                "camera:deleted",
                {"camera_id": camera_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete camera: {str(e)}")
            raise ServiceError("Camera deletion failed") from e
            
    async def get_stream(self, camera_id: int) -> StreamingResponse:
        """
        Get live video stream from camera.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            StreamingResponse: MJPEG video stream
            
        Raises:
            ServiceError: If stream access fails
        """
        try:
            # Verify camera exists and is active
            camera = await self.get_camera(camera_id)
            if not camera or not camera["is_active"]:
                raise ServiceError("Camera not available")
                
            # Get or create frame queue
            if camera_id not in self.frame_queues:
                self.frame_queues[camera_id] = asyncio.Queue(
                    maxsize=self.frame_buffer_size
                )
                
            # Start processing if needed
            if camera_id not in self.processing_tasks:
                self.processing_tasks[camera_id] = asyncio.create_task(
                    self._process_frames(camera_id)
                )
                
            # Create stream response
            return StreamingResponse(
                self._generate_frames(camera_id),
                media_type="multipart/x-mixed-replace; boundary=frame"
            )
            
        except Exception as e:
            logger.error(f"Failed to get stream: {str(e)}")
            raise ServiceError("Stream access failed") from e
            
    async def update_stream_config(
        self,
        camera_id: int,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update camera stream configuration.
        
        Args:
            camera_id: Camera identifier
            config: New configuration
            
        Returns:
            Optional[Dict[str, Any]]: Updated configuration
            
        Raises:
            ServiceError: If update fails
        """
        try:
            # Update camera config
            camera = await self.update_camera(
                camera_id,
                {"config": config}
            )
            if not camera:
                return None
                
            # Restart stream if needed
            if self._config_requires_restart(config):
                await self._restart_camera(camera_id)
                
            return camera["config"]
            
        except Exception as e:
            logger.error(f"Failed to update stream config: {str(e)}")
            raise ServiceError("Config update failed") from e
            
    async def _initialize_camera(self, camera: Dict[str, Any]):
        """
        Initialize camera instance.
        
        Args:
            camera: Camera details
            
        Raises:
            ServiceError: If initialization fails
        """
        try:
            # Store camera info
            self.cameras[camera["id"]] = camera
            
            # Create frame queue
            self.frame_queues[camera["id"]] = asyncio.Queue(
                maxsize=self.frame_buffer_size
            )
            
            # Start camera if active
            if camera["is_active"]:
                await self._start_camera(camera["id"])
                
        except Exception as e:
            logger.error(f"Failed to initialize camera: {str(e)}")
            raise ServiceError("Camera initialization failed") from e
            
    async def _start_camera(self, camera_id: int):
        """
        Start camera stream.
        
        Args:
            camera_id: Camera identifier
            
        Raises:
            ServiceError: If start fails
        """
        try:
            # Create video capture
            camera = self.cameras[camera_id]
            stream = cv2.VideoCapture(str(camera["url"]))
            stream.set(cv2.CAP_PROP_TIMEOUT, self.stream_timeout * 1000)
            
            # Store stream
            self.streams[camera_id] = stream
            
            # Start frame processing
            self.processing_tasks[camera_id] = asyncio.create_task(
                self._process_frames(camera_id)
            )
            
            # Update status
            await self.db.update_camera(
                camera_id,
                {"last_started": datetime.utcnow()}
            )
            
        except Exception as e:
            logger.error(f"Failed to start camera: {str(e)}")
            raise ServiceError("Camera start failed") from e
            
    async def _stop_camera(self, camera_id: int):
        """
        Stop camera stream.
        
        Args:
            camera_id: Camera identifier
            
        Raises:
            ServiceError: If stop fails
        """
        try:
            # Cancel processing task
            if camera_id in self.processing_tasks:
                self.processing_tasks[camera_id].cancel()
                del self.processing_tasks[camera_id]
                
            # Release stream
            if camera_id in self.streams:
                self.streams[camera_id].release()
                del self.streams[camera_id]
                
            # Clear frame queue
            if camera_id in self.frame_queues:
                while not self.frame_queues[camera_id].empty():
                    try:
                        self.frame_queues[camera_id].get_nowait()
                    except asyncio.QueueEmpty:
                        break
                        
            # Update status
            await self.db.update_camera(
                camera_id,
                {"last_stopped": datetime.utcnow()}
            )
            
        except Exception as e:
            logger.error(f"Failed to stop camera: {str(e)}")
            raise ServiceError("Camera stop failed") from e
            
    async def _restart_camera(self, camera_id: int):
        """
        Restart camera stream.
        
        Args:
            camera_id: Camera identifier
            
        Raises:
            ServiceError: If restart fails
        """
        try:
            await self._stop_camera(camera_id)
            await self._start_camera(camera_id)
            
        except Exception as e:
            logger.error(f"Failed to restart camera: {str(e)}")
            raise ServiceError("Camera restart failed") from e
            
    async def _process_frames(self, camera_id: int):
        """
        Process camera frames.
        
        Args:
            camera_id: Camera identifier
            
        Raises:
            ServiceError: If processing fails
        """
        try:
            stream = self.streams[camera_id]
            queue = self.frame_queues[camera_id]
            camera = self.cameras[camera_id]
            
            while True:
                # Read frame
                ret, frame = stream.read()
                if not ret:
                    raise ServiceError("Failed to read frame")
                    
                # Process frame
                processed_frame = await self._process_frame(
                    frame,
                    camera["config"]
                )
                
                # Add to queue
                await queue.put(processed_frame)
                
                # Update metrics
                await self._update_metrics(camera_id)
                
        except asyncio.CancelledError:
            logger.info(f"Frame processing cancelled for camera {camera_id}")
            
        except Exception as e:
            logger.error(f"Frame processing failed: {str(e)}")
            raise ServiceError("Frame processing failed") from e
            
    async def _process_frame(
        self,
        frame: np.ndarray,
        config: Dict[str, Any]
    ) -> np.ndarray:
        """
        Process single frame.
        
        Args:
            frame: Input frame
            config: Processing configuration
            
        Returns:
            np.ndarray: Processed frame
            
        Raises:
            ServiceError: If processing fails
        """
        try:
            # Apply frame processing
            if config.get("resize"):
                frame = cv2.resize(
                    frame,
                    tuple(map(int, config["resize"].split("x")))
                )
                
            if config.get("rotate"):
                frame = cv2.rotate(
                    frame,
                    getattr(cv2, f"ROTATE_{config['rotate']}")
                )
                
            # Apply face detection if enabled
            if config.get("face_detection", True):
                faces = await self.face_service.detect_faces(frame)
                for face in faces:
                    x, y, w, h = face["box"]
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
            return frame
            
        except Exception as e:
            logger.error(f"Frame processing failed: {str(e)}")
            raise ServiceError("Frame processing failed") from e
            
    async def _generate_frames(self, camera_id: int):
        """
        Generate MJPEG stream frames.
        
        Args:
            camera_id: Camera identifier
            
        Yields:
            bytes: JPEG frame data
            
        Raises:
            ServiceError: If generation fails
        """
        try:
            queue = self.frame_queues[camera_id]
            
            while True:
                # Get frame from queue
                frame = await queue.get()
                
                # Encode frame
                _, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 80]
                )
                
                # Yield frame data
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + buffer.tobytes() +
                    b"\r\n"
                )
                
        except asyncio.CancelledError:
            logger.info(f"Frame generation cancelled for camera {camera_id}")
            
        except Exception as e:
            logger.error(f"Frame generation failed: {str(e)}")
            raise ServiceError("Frame generation failed") from e
            
    async def _update_metrics(self, camera_id: int):
        """
        Update camera metrics.
        
        Args:
            camera_id: Camera identifier
            
        Raises:
            ServiceError: If update fails
        """
        try:
            # Calculate FPS
            camera = self.cameras[camera_id]
            now = datetime.utcnow()
            if "last_frame" in camera:
                fps = 1 / (now - camera["last_frame"]).total_seconds()
                camera["fps"] = fps
                
            camera["last_frame"] = now
            
            # Update database
            await self.db.update_camera(
                camera_id,
                {
                    "fps": camera["fps"],
                    "last_frame": now
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {str(e)}")
            raise ServiceError("Metrics update failed") from e
            
    def _config_requires_restart(self, config: Dict[str, Any]) -> bool:
        """
        Check if config changes require stream restart.
        
        Args:
            config: New configuration
            
        Returns:
            bool: True if restart needed
        """
        restart_keys = {"url", "codec", "resolution"}
        return any(key in config for key in restart_keys)
        
    def _setup_event_handlers(self):
        """Setup system event handlers."""
        self.event_bus.on("system:shutdown", self.stop)
        self.event_bus.on("camera:error", self._handle_camera_error)
        
    async def _handle_camera_error(self, event: Dict[str, Any]):
        """
        Handle camera error events.
        
        Args:
            event: Error event data
        """
        try:
            camera_id = event["camera_id"]
            error = event["error"]
            
            # Log error
            logger.error(f"Camera {camera_id} error: {error}")
            
            # Attempt recovery
            await self._restart_camera(camera_id)
            
            # Update status
            await self.db.update_camera(
                camera_id,
                {
                    "last_error": error,
                    "error_count": self.cameras[camera_id].get("error_count", 0) + 1
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling camera error: {str(e)}")
""" 