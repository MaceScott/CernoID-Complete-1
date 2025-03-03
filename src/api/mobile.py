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
    id: str
    timestamp: datetime
    camera_id: str
    face_id: Optional[str]
    confidence: float
    type: str
    image: Optional[str]

class CameraStatus(BaseModel):
    id: str
    name: str
    status: str
    fps: float
    resolution: tuple
    last_update: datetime

class SystemStats(BaseModel):
    active_cameras: int
    faces_detected: int
    processing_load: float
    alert_count: int
    uptime: float

class MobileAPI(BaseComponent):
    """Mobile integration API"""
    
    def __init__(self, config: dict):
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
        """Setup API routes"""
        
        @self.app.get("/status")
        async def get_system_status(
            credentials: HTTPAuthorizationCredentials = Security(self.security)
        ) -> SystemStats:
            """Get system status"""
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
            """Get all camera statuses"""
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
            """Get latest frame from camera"""
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
            """Get recent alerts"""
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
        """Verify token and check permission"""
        try:
            return await self.app.security.check_permission(
                token,
                required_permission
            )
        except Exception:
            return False

    async def _get_system_stats(self) -> SystemStats:
        """Get system statistics"""
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
        """Get all camera statuses"""
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
        """Get latest frame from camera"""
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
        """Process frame for mobile delivery"""
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
        """Get recent security alerts"""
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