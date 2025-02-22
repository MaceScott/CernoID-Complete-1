from typing import Dict, Optional
import cv2
import numpy as np
from core.camera.manager import CameraManager
from core.events.manager import EventManager
from core.recognition.processor import FaceProcessor
from core.error_handling import handle_exceptions

class CameraRecognition:
    def __init__(self):
        self.camera_manager = CameraManager()
        self.event_manager = EventManager()
        self.face_processor = FaceProcessor()
        self.active_recognitions: Dict[int, bool] = {}

    @handle_exceptions(logger=camera_logger.error)
    async def start_recognition(self, camera_id: int):
        if camera_id not in self.active_recognitions:
            self.active_recognitions[camera_id] = True
            stream = self.camera_manager.active_streams.get(camera_id)
            if stream:
                await self._process_stream(stream)

    async def _process_stream(self, stream):
        while self.active_recognitions.get(stream.camera_id, False):
            frame = await stream.get_frame()
            if frame is not None:
                results = await self.face_processor.process_frame(frame)
                await self._handle_recognition_results(results, stream.camera_id)

    async def _handle_recognition_results(self, results: list, camera_id: int):
        for result in results:
            await self.event_manager.publish(Event(
                type='face_detected',
                data={
                    'camera_id': camera_id,
                    'result': result
                }
            ))

    async def stop_recognition(self, camera_id: int):
        self.active_recognitions[camera_id] = False 
