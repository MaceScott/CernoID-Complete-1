"""WebSocket handlers for real-time camera feeds."""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import asyncio
import json
from ...core.recognition import FaceRecognitionSystem
from ...core.security import ThreatDetector
from ...utils.logging import get_logger

class CameraManager:
    """Manage WebSocket connections for camera feeds."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.recognition_system = FaceRecognitionSystem()
        self.threat_detector = ThreatDetector()
        self.logger = get_logger(__name__)
        
    async def connect(self,
                     websocket: WebSocket,
                     camera_id: str):
        """Handle new WebSocket connection."""
        await websocket.accept()
        
        if camera_id not in self.active_connections:
            self.active_connections[camera_id] = set()
        self.active_connections[camera_id].add(websocket)
        
    async def disconnect(self,
                        websocket: WebSocket,
                        camera_id: str):
        """Handle WebSocket disconnection."""
        self.active_connections[camera_id].remove(websocket)
        if not self.active_connections[camera_id]:
            del self.active_connections[camera_id]
            
    async def broadcast(self,
                       camera_id: str,
                       message: Dict):
        """Broadcast message to all connected clients."""
        if camera_id not in self.active_connections:
            return
            
        for connection in self.active_connections[camera_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.error(f"Broadcast error: {str(e)}")
                await self.disconnect(connection, camera_id)
                
    async def process_frame(self,
                          camera_id: str,
                          frame_data: bytes):
        """Process camera frame and broadcast results."""
        try:
            # Process frame
            results = await self.recognition_system.process_frame(frame_data)
            
            # Check for threats
            threats = await self.threat_detector.detect_threats(
                frame_data,
                results
            )
            
            # Prepare message
            message = {
                "camera_id": camera_id,
                "timestamp": time.time(),
                "faces": results,
                "threats": threats
            }
            
            # Broadcast results
            await self.broadcast(camera_id, message)
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")

camera_manager = CameraManager()

async def get_camera_manager():
    """Dependency to get camera manager instance."""
    return camera_manager 