from typing import Dict, List
import cv2
import numpy as np
from core.camera.manager import CameraManager
from core.recognition.processor import FaceProcessor
from core.alerts.alert_manager import AlertManager
from core.error_handling import handle_exceptions

class EnhancedCameraMonitor:
    def __init__(self):
        self.camera_manager = CameraManager()
        self.face_processor = FaceProcessor()
        self.alert_manager = AlertManager()
        self.active_monitors: Dict[int, bool] = {}
        self.frame_buffers: Dict[int, List[np.ndarray]] = {}
        
    @handle_exceptions(logger=camera_logger.error)
    async def start_monitoring(self, camera_id: int):
        if camera_id not in self.active_monitors:
            self.active_monitors[camera_id] = True
            self.frame_buffers[camera_id] = []
            await self._monitor_camera(camera_id)

    async def _monitor_camera(self, camera_id: int):
        stream = self.camera_manager.active_streams.get(camera_id)
        if not stream:
            return

        while self.active_monitors.get(camera_id, False):
            frame = await stream.get_frame()
            if frame is not None:
                # Store frame in buffer for motion detection
                self.frame_buffers[camera_id].append(frame)
                if len(self.frame_buffers[camera_id]) > 10:
                    self.frame_buffers[camera_id].pop(0)

                # Process frame for faces
                faces = await self.face_processor.process_frame(frame)
                
                # Check for motion and suspicious activity
                if len(self.frame_buffers[camera_id]) >= 2:
                    motion = self._detect_motion(
                        self.frame_buffers[camera_id][-2:],
                        camera_id
                    )
                    if motion:
                        await self._analyze_motion(motion, camera_id)

                # Handle face detections
                for face in faces:
                    await self._handle_face_detection(face, camera_id)

    async def _handle_face_detection(self, face_data: dict, camera_id: int):
        if not face_data.get('match'):
            await self.alert_manager.create_alert(
                SecurityAlert(
                    priority=AlertPriority.MEDIUM,
                    alert_type="unrecognized_face",
                    description="Unrecognized person detected",
                    camera_id=camera_id,
                    face_data=face_data
                )
            )

    def _detect_motion(self, frames: List[np.ndarray], camera_id: int) -> Dict:
        if len(frames) < 2:
            return None
            
        diff = cv2.absdiff(frames[0], frames[1])
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(
            dilated,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE
        )

        return {
            'contours': contours,
            'frame': frames[1]
        } if contours else None 
