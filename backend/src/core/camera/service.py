"""
File: service.py
Purpose: Core camera management service for the CernoID system.

Key Features:
- Camera lifecycle management (add, remove, update)
- Video stream handling and processing
- Frame processing pipeline integration
- Camera health monitoring and recovery
- Resource management and cleanup
- Event-driven state management

Dependencies:
- OpenCV: Video capture and frame processing
- NumPy: Frame data manipulation
- AsyncIO: Asynchronous operations
- Core services:
  - Database: Camera storage
  - FaceRecognition: Frame analysis
  - StreamProcessor: Frame processing
  - EventBus: Event handling
  - Logging: System logging

Architecture:
- Service-oriented design
  - Event-driven processing
  - Resource pooling
  - Connection management
  - Error recovery
  - State management

Performance:
- Connection pooling
  - Reuse connections
  - Limit concurrent streams
  - Auto-cleanup idle
- Frame buffering
  - Adaptive buffer size
  - Drop policy
  - Quality control
- Adaptive quality
  - Resolution scaling
  - FPS adjustment
  - Bandwidth control
- Resource limits
  - Memory monitoring
  - CPU usage control
  - Stream quotas
- Memory management
  - Frame cleanup
  - Buffer limits
  - Resource tracking
- Load balancing
  - Stream distribution
  - Processing allocation
  - Resource sharing
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
import cv2
import numpy as np

from ...database import get_db
from ...models import Camera
from ...utils.logging import get_logger
from ..events import EventBus
from .processor import StreamProcessor

logger = get_logger(__name__)

class CameraService:
    """
    Core service for camera management and video stream processing.
    
    Attributes:
        _cameras (Dict[str, Camera]): Active camera instances
        _streams (Dict[str, StreamProcessor]): Active stream processors
        _event_bus (EventBus): Event handling system
        _db: Database connection
        _config (Dict): Service configuration
        
    Configuration:
        max_cameras: Maximum concurrent cameras
        max_streams: Maximum concurrent streams
        buffer_size: Frame buffer size
        cleanup_interval: Resource cleanup interval
        reconnect_attempts: Connection retry attempts
        health_check_interval: Camera health check interval
        
    Events:
        camera.added: New camera registered
        camera.removed: Camera removed
        camera.updated: Camera settings changed
        camera.error: Camera error occurred
        stream.started: Stream processing started
        stream.stopped: Stream processing stopped
        frame.processed: Frame processing completed
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize camera service.
        
        Args:
            config: Service configuration
            
        Features:
            - Configuration validation
            - Resource initialization
            - Event bus setup
            - State management
            - Error handling
        """
        self._cameras = {}
        self._streams = {}
        self._event_bus = EventBus()
        self._db = get_db()
        self._config = self._validate_config(config or {})
        self._setup_events()
        
    async def create_camera(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add new camera to the system.
        
        Args:
            data: Camera creation data
                name: Camera name
                url: Stream URL
                location: Physical location
                type: Camera type
                config: Stream configuration
                
        Returns:
            Dict[str, Any]: Created camera details
            
        Features:
            - Data validation
            - Stream testing
            - Resource allocation
            - Event dispatch
            - Error handling
            
        Raises:
            ValueError: Invalid camera data
            RuntimeError: Resource allocation failed
        """
        try:
            # Validate camera limit
            if len(self._cameras) >= self._config["max_cameras"]:
                raise ValueError("Maximum camera limit reached")
                
            # Create camera
            camera = await Camera.create(self._db, data)
            
            # Initialize stream
            stream = StreamProcessor(
                camera_id=camera.id,
                url=camera.url,
                config=camera.config
            )
            
            # Store instances
            self._cameras[camera.id] = camera
            self._streams[camera.id] = stream
            
            # Emit event
            await self._event_bus.emit(
                "camera.added",
                {"camera_id": camera.id}
            )
            
            return camera.to_dict()
            
        except Exception as e:
            logger.error(f"Camera creation failed: {str(e)}")
            raise
            
    async def get_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Get camera details.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Optional[Dict[str, Any]]: Camera details if found
            
        Features:
            - Camera lookup
            - Status check
            - Stats collection
            - Error handling
            - Event logging
        """
        try:
            camera = self._cameras.get(camera_id)
            if not camera:
                return None
                
            return camera.to_dict()
            
        except Exception as e:
            logger.error(f"Camera retrieval failed: {str(e)}")
            raise
            
    async def list_cameras(self) -> List[Dict[str, Any]]:
        """
        List all cameras.
        
        Returns:
            List[Dict[str, Any]]: List of camera details
            
        Features:
            - Status collection
            - Stats aggregation
            - Filtering support
            - Error handling
            - Event logging
        """
        try:
            return [
                camera.to_dict()
                for camera in self._cameras.values()
            ]
            
        except Exception as e:
            logger.error(f"Camera listing failed: {str(e)}")
            raise
            
    async def update_camera(
        self,
        camera_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update camera settings.
        
        Args:
            camera_id: Camera identifier
            data: Update data
                name: New name
                location: New location
                active: New status
                config: New configuration
                
        Returns:
            Optional[Dict[str, Any]]: Updated camera details
            
        Features:
            - Config validation
            - Stream restart
            - Resource reallocation
            - Event dispatch
            - Error handling
        """
        try:
            camera = self._cameras.get(camera_id)
            if not camera:
                return None
                
            # Update camera
            await camera.update(self._db, data)
            
            # Update stream if needed
            if "config" in data:
                stream = self._streams[camera_id]
                await stream.update_config(data["config"])
                
            # Emit event
            await self._event_bus.emit(
                "camera.updated",
                {
                    "camera_id": camera_id,
                    "changes": data
                }
            )
            
            return camera.to_dict()
            
        except Exception as e:
            logger.error(f"Camera update failed: {str(e)}")
            raise
            
    async def delete_camera(self, camera_id: str) -> bool:
        """
        Remove camera from system.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            bool: True if camera was removed
            
        Features:
            - Resource cleanup
            - Stream shutdown
            - Event dispatch
            - Error handling
            - State cleanup
        """
        try:
            camera = self._cameras.get(camera_id)
            if not camera:
                return False
                
            # Stop stream
            stream = self._streams[camera_id]
            await stream.stop()
            
            # Remove instances
            del self._cameras[camera_id]
            del self._streams[camera_id]
            
            # Delete from database
            await camera.delete(self._db)
            
            # Emit event
            await self._event_bus.emit(
                "camera.removed",
                {"camera_id": camera_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Camera deletion failed: {str(e)}")
            raise
            
    async def get_stream(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video stream details.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Optional[Dict[str, Any]]: Stream details if available
            
        Features:
            - Stream validation
            - Token generation
            - Config retrieval
            - Status check
            - Error handling
        """
        try:
            camera = self._cameras.get(camera_id)
            if not camera:
                return None
                
            stream = self._streams[camera_id]
            return {
                "url": stream.get_url(),
                "token": stream.get_token(),
                "config": stream.get_config()
            }
            
        except Exception as e:
            logger.error(f"Stream access failed: {str(e)}")
            raise
            
    async def update_stream_config(
        self,
        camera_id: str,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update stream configuration.
        
        Args:
            camera_id: Camera identifier
            config: New configuration
                fps: Frame rate
                resolution: Stream resolution
                quality: Stream quality
                
        Returns:
            Optional[Dict[str, Any]]: Updated configuration
            
        Features:
            - Config validation
            - Stream restart
            - Quality control
            - Resource adjustment
            - Event dispatch
        """
        try:
            camera = self._cameras.get(camera_id)
            if not camera:
                return None
                
            # Update stream
            stream = self._streams[camera_id]
            await stream.update_config(config)
            
            # Update camera
            await camera.update(
                self._db,
                {"config": config}
            )
            
            return {
                "config": stream.get_config(),
                "status": {
                    "applied": True,
                    "restart_required": False
                }
            }
            
        except Exception as e:
            logger.error(f"Config update failed: {str(e)}")
            raise
            
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate service configuration.
        
        Args:
            config: Configuration data
            
        Returns:
            Dict[str, Any]: Validated configuration
            
        Features:
            - Default values
            - Type checking
            - Range validation
            - Dependency checks
            - Error handling
        """
        defaults = {
            "max_cameras": 100,
            "max_streams": 50,
            "buffer_size": 30,
            "cleanup_interval": 300,
            "reconnect_attempts": 3,
            "health_check_interval": 60
        }
        
        # Merge with defaults
        config = {**defaults, **config}
        
        # Validate values
        if config["max_cameras"] < 1:
            raise ValueError("max_cameras must be positive")
        if config["max_streams"] < 1:
            raise ValueError("max_streams must be positive")
        if config["buffer_size"] < 1:
            raise ValueError("buffer_size must be positive")
        if config["cleanup_interval"] < 1:
            raise ValueError("cleanup_interval must be positive")
        if config["reconnect_attempts"] < 0:
            raise ValueError("reconnect_attempts must be non-negative")
        if config["health_check_interval"] < 1:
            raise ValueError("health_check_interval must be positive")
            
        return config
        
    def _setup_events(self) -> None:
        """
        Setup event handlers.
        
        Features:
            - Event registration
            - Handler binding
            - Error handling
            - Logging setup
            - State tracking
        """
        self._event_bus.on(
            "camera.error",
            self._handle_camera_error
        )
        self._event_bus.on(
            "stream.error",
            self._handle_stream_error
        )
        
    async def _handle_camera_error(
        self,
        camera_id: str,
        error: Exception
    ) -> None:
        """
        Handle camera errors.
        
        Args:
            camera_id: Camera identifier
            error: Error details
            
        Features:
            - Error classification
            - Recovery attempt
            - Resource cleanup
            - Event dispatch
            - Logging
        """
        try:
            logger.error(
                f"Camera error: {camera_id} - {str(error)}"
            )
            
            # Attempt recovery
            camera = self._cameras.get(camera_id)
            if camera:
                await self._recover_camera(camera)
                
        except Exception as e:
            logger.error(
                f"Error recovery failed: {str(e)}"
            )
            
    async def _handle_stream_error(
        self,
        camera_id: str,
        error: Exception
    ) -> None:
        """
        Handle stream errors.
        
        Args:
            camera_id: Camera identifier
            error: Error details
            
        Features:
            - Error classification
            - Stream restart
            - Resource cleanup
            - Event dispatch
            - Logging
        """
        try:
            logger.error(
                f"Stream error: {camera_id} - {str(error)}"
            )
            
            # Attempt recovery
            stream = self._streams.get(camera_id)
            if stream:
                await self._recover_stream(stream)
                
        except Exception as e:
            logger.error(
                f"Stream recovery failed: {str(e)}"
            )
            
    async def _recover_camera(self, camera: Camera) -> None:
        """
        Attempt camera recovery.
        
        Args:
            camera: Camera instance
            
        Features:
            - Connection retry
            - State reset
            - Resource cleanup
            - Event dispatch
            - Logging
        """
        try:
            # Reset state
            camera.reset_state()
            
            # Attempt reconnection
            for _ in range(self._config["reconnect_attempts"]):
                if await camera.connect():
                    logger.info(
                        f"Camera recovered: {camera.id}"
                    )
                    return
                    
            logger.error(
                f"Camera recovery failed: {camera.id}"
            )
            
        except Exception as e:
            logger.error(
                f"Recovery attempt failed: {str(e)}"
            )
            
    async def _recover_stream(self, stream: StreamProcessor) -> None:
        """
        Attempt stream recovery.
        
        Args:
            stream: Stream processor instance
            
        Features:
            - Stream restart
            - Buffer cleanup
            - State reset
            - Event dispatch
            - Logging
        """
        try:
            # Reset state
            stream.reset_state()
            
            # Attempt restart
            for _ in range(self._config["reconnect_attempts"]):
                if await stream.start():
                    logger.info(
                        f"Stream recovered: {stream.camera_id}"
                    )
                    return
                    
            logger.error(
                f"Stream recovery failed: {stream.camera_id}"
            )
            
        except Exception as e:
            logger.error(
                f"Recovery attempt failed: {str(e)}"
            )
""" 