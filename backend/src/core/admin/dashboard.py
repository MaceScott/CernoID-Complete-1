from typing import Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
import numpy as np
import cv2

from ..base import BaseComponent
from ..utils.errors import DashboardError

class DashboardStats(BaseModel):
    """Dashboard statistics model"""
    total_faces: int
    active_cameras: int
    alerts_24h: int
    system_load: float
    uptime: str
    storage_usage: float

class CameraView(BaseModel):
    """Camera view model"""
    id: str
    name: str
    status: str
    fps: float
    faces_detected: int
    last_alert: Optional[datetime]

class AdminDashboard(BaseComponent):
    """Administrative dashboard system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Initialize FastAPI
        self.app = FastAPI(title="CernoID Admin Dashboard")
        self.security = HTTPBearer()
        
        # Setup templates
        self.templates = Jinja2Templates(directory="templates")
        
        # Serve static files
        self.app.mount(
            "/static",
            StaticFiles(directory="static"),
            name="static"
        )
        
        # Dashboard settings
        self._refresh_interval = config.get('dashboard.refresh', 5)
        self._max_alerts = config.get('dashboard.max_alerts', 100)
        self._max_logs = config.get('dashboard.max_logs', 1000)
        
        # Cache for dashboard data
        self._stats_cache: Optional[DashboardStats] = None
        self._last_cache_update = datetime.min
        self._cache_duration = timedelta(seconds=5)
        
        # Setup routes
        self._setup_routes()
        
        # Statistics
        self._stats = {
            'dashboard_views': 0,
            'active_sessions': 0,
            'last_access': None
        }

    def _setup_routes(self) -> None:
        """Setup dashboard routes"""
        
        @self.app.get("/")
        async def dashboard_home(request):
            """Render dashboard home page"""
            try:
                # Verify admin access
                await self._verify_admin(request)
                
                # Get dashboard data
                stats = await self._get_dashboard_stats()
                cameras = await self._get_camera_views()
                alerts = await self._get_recent_alerts()
                
                self._update_stats('view')
                
                return self.templates.TemplateResponse(
                    "dashboard.html",
                    {
                        "request": request,
                        "stats": stats,
                        "cameras": cameras,
                        "alerts": alerts,
                        "refresh": self._refresh_interval
                    }
                )
                
            except Exception as e:
                raise DashboardError(f"Dashboard error: {str(e)}")

        @self.app.get("/api/stats")
        async def get_stats():
            """Get dashboard statistics"""
            try:
                stats = await self._get_dashboard_stats()
                return stats.dict()
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )

        @self.app.get("/api/cameras")
        async def get_cameras():
            """Get camera views"""
            try:
                cameras = await self._get_camera_views()
                return [cam.dict() for cam in cameras]
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )

        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get recent alerts"""
            try:
                alerts = await self._get_recent_alerts()
                return alerts
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )

        @self.app.get("/api/logs")
        async def get_logs():
            """Get system logs"""
            try:
                logs = await self._get_system_logs()
                return logs
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )

        @self.app.post("/api/camera/{camera_id}/toggle")
        async def toggle_camera(camera_id: str):
            """Toggle camera status"""
            try:
                result = await self._toggle_camera(camera_id)
                return {"success": result}
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )

    async def _verify_admin(self, request) -> None:
        """Verify admin access"""
        try:
            token = request.headers.get('Authorization')
            if not token:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized"
                )
            
            # Verify admin permission
            if not await self.app.security.check_permission(token, 'admin'):
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
            
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=str(e)
            )

    async def _get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics"""
        try:
            # Check cache
            if (self._stats_cache and 
                datetime.utcnow() - self._last_cache_update < self._cache_duration):
                return self._stats_cache
            
            # Collect stats from components
            recognition_stats = await self.app.recognition.get_stats()
            camera_stats = await self.app.camera.coordinator.get_stats()
            monitor_stats = await self.app.monitor.get_metrics()
            
            # Calculate uptime
            uptime = self._format_uptime(monitor_stats[0].timestamp)
            
            # Create stats
            stats = DashboardStats(
                total_faces=recognition_stats['total_faces'],
                active_cameras=camera_stats['active_cameras'],
                alerts_24h=await self._count_recent_alerts(),
                system_load=monitor_stats[0].cpu_usage,
                uptime=uptime,
                storage_usage=self._get_storage_usage()
            )
            
            # Update cache
            self._stats_cache = stats
            self._last_cache_update = datetime.utcnow()
            
            return stats
            
        except Exception as e:
            raise DashboardError(f"Failed to get stats: {str(e)}")

    async def _get_camera_views(self) -> List[CameraView]:
        """Get camera views"""
        try:
            coordinator = self.app.camera.coordinator
            cameras = []
            
            for camera_id in coordinator._cameras:
                status = await coordinator.get_camera_status(camera_id)
                if status:
                    # Get camera stats
                    stats = await coordinator.get_camera_stats(camera_id)
                    
                    cameras.append(CameraView(
                        id=status.id,
                        name=status.name,
                        status=status.status,
                        fps=status.fps,
                        faces_detected=stats.get('faces_detected', 0),
                        last_alert=stats.get('last_alert')
                    ))
            
            return cameras
            
        except Exception as e:
            raise DashboardError(f"Failed to get cameras: {str(e)}")

    async def _get_recent_alerts(self) -> List[Dict]:
        """Get recent alerts"""
        try:
            alerts = await self.app.storage.get_recent_alerts(
                limit=self._max_alerts
            )
            
            # Process alerts for display
            processed = []
            for alert in alerts:
                processed.append({
                    'id': alert['id'],
                    'timestamp': alert['timestamp'],
                    'type': alert['type'],
                    'camera': alert['camera_id'],
                    'details': alert.get('details', ''),
                    'image': self._process_alert_image(alert.get('image'))
                })
            
            return processed
            
        except Exception as e:
            raise DashboardError(f"Failed to get alerts: {str(e)}")

    async def _get_system_logs(self) -> List[Dict]:
        """Get system logs"""
        try:
            log_path = Path('logs/system.log')
            if not log_path.exists():
                return []
            
            logs = []
            with open(log_path, 'r') as f:
                for line in f.readlines()[-self._max_logs:]:
                    try:
                        logs.append(json.loads(line))
                    except:
                        continue
            
            return logs
            
        except Exception as e:
            raise DashboardError(f"Failed to get logs: {str(e)}")

    async def _toggle_camera(self, camera_id: str) -> bool:
        """Toggle camera status"""
        try:
            coordinator = self.app.camera.coordinator
            status = await coordinator.get_camera_status(camera_id)
            
            if not status:
                return False
            
            if status.status == 'active':
                await coordinator.stop_camera(camera_id)
            else:
                await coordinator.start_camera(camera_id)
            
            return True
            
        except Exception as e:
            raise DashboardError(f"Failed to toggle camera: {str(e)}")

    def _format_uptime(self, start_time: datetime) -> str:
        """Format uptime string"""
        delta = datetime.utcnow() - start_time
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        return f"{days}d {hours}h {minutes}m"

    def _get_storage_usage(self) -> float:
        """Get storage usage percentage"""
        try:
            import psutil
            usage = psutil.disk_usage('/')
            return usage.percent
        except:
            return 0.0

    def _process_alert_image(self, image: Optional[np.ndarray]) -> Optional[str]:
        """Process alert image for display"""
        try:
            if image is None:
                return None
                
            # Resize image
            max_size = 400
            height, width = image.shape[:2]
            if width > max_size:
                scale = max_size / width
                new_size = (max_size, int(height * scale))
                image = cv2.resize(image, new_size)
            
            # Convert to JPEG
            _, buffer = cv2.imencode('.jpg', image, [
                cv2.IMWRITE_JPEG_QUALITY, 80
            ])
            
            # Convert to base64
            import base64
            return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
            
        except Exception:
            return None

    def _update_stats(self, action: str) -> None:
        """Update dashboard statistics"""
        self._stats['dashboard_views'] += 1
        self._stats['last_access'] = datetime.utcnow()
        
        if action == 'view':
            self._stats['active_sessions'] += 1

    async def get_stats(self) -> Dict:
        """Get dashboard statistics"""
        return self._stats.copy() 