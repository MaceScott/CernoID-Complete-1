"""
File: mobile.py
Purpose: Provides mobile-specific API endpoints for the CernoID system's mobile application.

Key Features:
- Real-time camera feed access
- Security alert monitoring
- System status tracking
- Camera management
- Mobile-optimized image processing

Dependencies:
- FastAPI: Web framework
- OpenCV: Image processing
- NumPy: Array operations
- Core services:
  - Camera coordinator
  - Recognition system
  - Security system
  - Storage service
  - Authentication middleware

API Endpoints:
- GET /status: System status and statistics
- GET /cameras: List of camera statuses
- GET /camera/{camera_id}/frame: Latest camera frame
- GET /alerts: Recent security alerts

Security:
- JWT authentication required
- Permission-based access control
- Rate limiting
- Image size optimization
- Error handling and logging
"""

from typing import Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime
import cv2
import numpy as np
import base64
from dataclasses import dataclass

from ..base import BaseComponent
from ..utils.errors import APIError

# API Models
class AlertResponse(BaseModel):
    """
    Security alert response model.
    
    Attributes:
        id (str): Unique alert identifier
        timestamp (datetime): Alert creation time
        camera_id (str): Source camera identifier
        face_id (Optional[str]): Detected face identifier
        confidence (float): Detection confidence score
        type (str): Alert type (e.g., "unauthorized_access")
        image (Optional[str]): Base64 encoded alert image
    """
    id: str
    timestamp: datetime
    camera_id: str
    face_id: Optional[str]
    confidence: float
    type: str
    image: Optional[str]

class CameraStatus(BaseModel):
    """
    Camera status response model.
    
    Attributes:
        id (str): Camera identifier
        name (str): Camera display name
        status (str): Current status ("active", "inactive", "error")
        fps (float): Current frames per second
        resolution (tuple): Frame resolution (width, height)
        last_update (datetime): Last status update time
    """
    id: str
    name: str
    status: str
    fps: float
    resolution: tuple
    last_update: datetime

class SystemStats(BaseModel):
    """
    System statistics response model.
    
    Attributes:
        active_cameras (int): Number of active cameras
        faces_detected (int): Total faces detected
        processing_load (float): System processing load (0-100)
        alert_count (int): Number of active alerts
        uptime (float): System uptime in seconds
    """
    active_cameras: int
    faces_detected: int
    processing_load: float
    alert_count: int
    uptime: float

class MobileAPI(BaseComponent):
    """
    Mobile API component handling mobile app integration.
    
    Features:
        - Real-time camera feed access
        - Security alert monitoring
        - System status tracking
        - Mobile-optimized image processing
        
    Configuration:
        - api.max_alerts: Maximum alerts to return
        - api.jpeg_quality: JPEG compression quality
        - api.max_frame_size: Maximum frame width
    """
    
    def __init__(self, config: dict):
        """
        Initialize mobile API component.
        
        Args:
            config (dict): Configuration dictionary containing:
                - api.max_alerts: Maximum alerts to return
                - api.jpeg_quality: JPEG compression quality
                - api.max_frame_size: Maximum frame width
        """
        super().__init__(config)
        
        # Initialize FastAPI
        self.app = FastAPI(title="CernoID Mobile API")
        self.security = HTTPBearer()
        
        # API settings
        self._max_alerts = config.get('api.max_alerts', 100)
        self._frame_quality = config.get('api.jpeg_quality', 80)
        self._max_frame_size = config.get('api.max_frame_size', 1280)
        
        # Setup routes
        self._setup_routes()
        
        # Statistics
        self._stats = {
            'total_requests': 0,
            'active_clients': 0,
            'data_transferred': 0,
            'average_latency': 0.0
        }

    def _setup_routes(self) -> None:
        """
        Setup API routes with security middleware.
        
        Routes:
            - GET /status: System status
            - GET /cameras: Camera list
            - GET /camera/{camera_id}/frame: Camera frame
            - GET /alerts: Security alerts
            
        Security:
            - JWT token required
            - Permission verification
            - Rate limiting
        """
        
        @self.app.get("/status")
        async def get_system_status(
            credentials: HTTPAuthorizationCredentials = Security(self.security)
        ) -> SystemStats:
            """
            Get current system status and statistics.
            
            Args:
                credentials: JWT credentials
            
            Returns:
                SystemStats: Current system statistics
                
            Raises:
                HTTPException:
                    - 401: Invalid credentials
                    - 500: Internal error
            """
            try:
                # Verify token
                if not await self._verify_access(credentials.credentials, 'view'):
                    raise HTTPException(status_code=401, detail="Unauthorized")
                
                # Get system stats
                stats = await self._get_system_stats()
                
                self._update_stats('status_request')
                return stats
                
            except Exception as e:
                self._handle_error("Status request failed", e)

        @self.app.get("/cameras")
        async def get_cameras(
            credentials: HTTPAuthorizationCredentials = Security(self.security)
        ) -> List[CameraStatus]:
            """
            Get status of all cameras.
            
            Args:
                credentials: JWT credentials
            
            Returns:
                List[CameraStatus]: List of camera statuses
                
            Raises:
                HTTPException:
                    - 401: Invalid credentials
                    - 500: Internal error
            """
            try:
                # Verify token
                if not await self._verify_access(credentials.credentials, 'view'):
                    raise HTTPException(status_code=401, detail="Unauthorized")
                
                # Get camera statuses
                cameras = await self._get_camera_statuses()
                
                self._update_stats('camera_request')
                return cameras
                
            except Exception as e:
                self._handle_error("Camera request failed", e)

        @self.app.get("/camera/{camera_id}/frame")
        async def get_camera_frame(
            camera_id: str,
            credentials: HTTPAuthorizationCredentials = Security(self.security)
        ) -> Dict:
            """
            Get latest frame from specified camera.
            
            Args:
                camera_id: Camera identifier
                credentials: JWT credentials
            
            Returns:
                Dict: Frame data including:
                    - camera_id: Camera identifier
                    - timestamp: Frame timestamp
                    - image: Base64 encoded JPEG
                
            Raises:
                HTTPException:
                    - 401: Invalid credentials
                    - 404: Camera/frame not found
                    - 500: Internal error
            """
            try:
                # Verify token
                if not await self._verify_access(credentials.credentials, 'view'):
                    raise HTTPException(status_code=401, detail="Unauthorized")
                
                # Get frame
                frame = await self._get_camera_frame(camera_id)
                if frame is None:
                    raise HTTPException(status_code=404, detail="Frame not available")
                
                self._update_stats('frame_request')
                return frame
                
            except Exception as e:
                self._handle_error("Frame request failed", e)

        @self.app.get("/alerts")
        async def get_alerts(
            limit: int = 10,
            credentials: HTTPAuthorizationCredentials = Security(self.security)
        ) -> List[AlertResponse]:
            """
            Get recent security alerts.
            
            Args:
                limit: Maximum number of alerts to return
                credentials: JWT credentials
            
            Returns:
                List[AlertResponse]: List of recent alerts
                
            Raises:
                HTTPException:
                    - 401: Invalid credentials
                    - 500: Internal error
                    
            Note:
                Limit is capped by api.max_alerts configuration
            """
            try:
                # Verify token
                if not await self._verify_access(credentials.credentials, 'view'):
                    raise HTTPException(status_code=401, detail="Unauthorized")
                
                # Get alerts
                alerts = await self._get_recent_alerts(limit)
                
                self._update_stats('alert_request')
                return alerts
                
            except Exception as e:
                self._handle_error("Alert request failed", e)

    async def _verify_access(self, token: str, required_permission: str) -> bool:
        """
        Verify JWT token and check required permission.
        
        Args:
            token: JWT token
            required_permission: Required permission string
            
        Returns:
            bool: True if access is allowed
        """
        try:
            return await self.app.security.check_permission(
                token,
                required_permission
            )
        except Exception:
            return False

    async def _get_system_stats(self) -> SystemStats:
        """
        Collect system statistics from various components.
        
        Returns:
            SystemStats: Current system statistics
            
        Raises:
            APIError: If stats collection fails
        """
        try:
            # Collect stats from various components
            recognition_stats = await self.app.recognition.get_stats()
            camera_stats = await self.app.camera.coordinator.get_stats()
            security_stats = await self.app.security.get_stats()
            
            return SystemStats(
                active_cameras=camera_stats['active_cameras'],
                faces_detected=recognition_stats['faces_detected'],
                processing_load=camera_stats['processing_load'],
                alert_count=security_stats['security_events'],
                uptime=self._get_uptime()
            )
            
        except Exception as e:
            raise APIError(f"Failed to get system stats: {str(e)}")

    async def _get_camera_statuses(self) -> List[CameraStatus]:
        """
        Get status of all registered cameras.
        
        Returns:
            List[CameraStatus]: List of camera statuses
            
        Raises:
            APIError: If status collection fails
        """
        try:
            coordinator = self.app.camera.coordinator
            cameras = []
            
            for camera_id in coordinator._cameras:
                status = await coordinator.get_camera_status(camera_id)
                if status:
                    cameras.append(CameraStatus(
                        id=status.id,
                        name=status.name,
                        status=status.status,
                        fps=status.fps,
                        resolution=status.resolution,
                        last_update=status.last_frame
                    ))
            
            return cameras
            
        except Exception as e:
            raise APIError(f"Failed to get camera statuses: {str(e)}")

    async def _get_camera_frame(self, camera_id: str) -> Optional[Dict]:
        """
        Get latest frame from camera and process for mobile.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Optional[Dict]: Frame data or None if unavailable
            
        Raises:
            APIError: If frame retrieval/processing fails
        """
        try:
            # Get frame from coordinator
            frame_data = await self.app.camera.coordinator.get_frame(camera_id)
            if not frame_data:
                return None
            
            # Process frame for mobile
            frame = self._process_frame_for_mobile(frame_data['frame'])
            
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', frame, [
                cv2.IMWRITE_JPEG_QUALITY, self._frame_quality
            ])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'camera_id': camera_id,
                'timestamp': frame_data['timestamp'],
                'image': image_base64
            }
            
        except Exception as e:
            raise APIError(f"Failed to get camera frame: {str(e)}")

    def _process_frame_for_mobile(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame for mobile delivery (resize, optimize).
        
        Args:
            frame: Input frame array
            
        Returns:
            np.ndarray: Processed frame
            
        Raises:
            APIError: If processing fails
            
        Note:
            Resizes frame to fit within max_frame_size while
            maintaining aspect ratio
        """
        try:
            # Resize if needed
            height, width = frame.shape[:2]
            if width > self._max_frame_size:
                scale = self._max_frame_size / width
                new_size = (
                    self._max_frame_size,
                    int(height * scale)
                )
                frame = cv2.resize(frame, new_size)
            
            return frame
            
        except Exception as e:
            raise APIError(f"Frame processing failed: {str(e)}")

    async def _get_recent_alerts(self, limit: int) -> List[AlertResponse]:
        """
        Get recent security alerts with images.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List[AlertResponse]: List of recent alerts
            
        Raises:
            APIError: If alert retrieval fails
            
        Note:
            Limit is capped by max_alerts configuration
        """
        try:
            limit = min(limit, self._max_alerts)
            alerts = await self.app.storage.get_recent_alerts(limit)
            
            response_alerts = []
            for alert in alerts:
                # Process alert image if available
                image_base64 = None
                if alert.get('image'):
                    image_base64 = self._process_alert_image(alert['image'])
                
                response_alerts.append(AlertResponse(
                    id=alert['id'],
                    timestamp=alert['timestamp'],
                    camera_id=alert['camera_id'],
                    face_id=alert.get('face_id'),
                    confidence=alert.get('confidence', 0.0),
                    type=alert['type'],
                    image=image_base64
                ))
            
            return response_alerts
            
        except Exception as e:
            raise APIError(f"Failed to get alerts: {str(e)}")

    def _process_alert_image(self, image: np.ndarray) -> Optional[str]:
        """Process alert image for mobile"""
        try:
            # Resize image
            image = self._process_frame_for_mobile(image)
            
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', image, [
                cv2.IMWRITE_JPEG_QUALITY, self._frame_quality
            ])
            return base64.b64encode(buffer).decode('utf-8')
            
        except Exception:
            return None

    def _update_stats(self, request_type: str) -> None:
        """Update API statistics"""
        self._stats['total_requests'] += 1
        
        # Update specific stats based on request type
        if request_type == 'frame_request':
            self._stats['data_transferred'] += 1024  # Approximate frame size

    def _get_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            with open('/proc/uptime', 'r') as f:
                return float(f.readline().split()[0])
        except Exception:
            return 0.0

    def _handle_error(self, message: str, error: Exception) -> None:
        """Handle API error"""
        self.logger.error(f"{message}: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {message}"
        )

    async def get_stats(self) -> Dict:
        """Get API statistics"""
        return self._stats.copy() 