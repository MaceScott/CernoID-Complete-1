from typing import Dict, Optional
import cv2
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from core.error_handling import handle_exceptions

@dataclass
class StreamConfig:
    quality: int = 80  # JPEG quality
    max_fps: int = 15
    resolution: tuple = (640, 480)
    format: str = "JPEG"

class MobileStreamManager:
    def __init__(self):
        self.active_streams: Dict[int, Dict] = {}
        self.stream_config = StreamConfig()

    @handle_exceptions(logger=stream_logger.error)
    async def start_stream(self, camera_id: int, websocket) -> None:
        if camera_id not in self.active_streams:
            self.active_streams[camera_id] = {
                'websocket': websocket,
                'last_frame_time': datetime.now(),
                'frame_count': 0
            }
            
        try:
            camera = await self.camera_manager.get_camera(camera_id)
            while True:
                frame = await camera.get_frame()
                if frame is not None:
                    # Process frame for mobile streaming
                    processed_frame = await self._process_frame(frame)
                    
                    # Send frame through WebSocket
                    await websocket.send_bytes(processed_frame)
                    
                    # Update stream statistics
                    self.active_streams[camera_id]['frame_count'] += 1
                    self.active_streams[camera_id]['last_frame_time'] = datetime.now()
                    
        except Exception as e:
            stream_logger.error(f"Stream error for camera {camera_id}: {e}")
            await self.stop_stream(camera_id)

    async def _process_frame(self, frame: np.ndarray) -> bytes:
        # Resize frame for mobile
        resized = cv2.resize(
            frame,
            self.stream_config.resolution,
            interpolation=cv2.INTER_AREA
        )
        
        # Encode frame
        success, encoded = cv2.imencode(
            f'.{self.stream_config.format.lower()}',
            resized,
            [cv2.IMWRITE_JPEG_QUALITY, self.stream_config.quality]
        )
        
        if not success:
            raise Exception("Failed to encode frame")
            
        return encoded.tobytes()

    async def stop_stream(self, camera_id: int):
        if camera_id in self.active_streams:
            try:
                await self.active_streams[camera_id]['websocket'].close()
            except:
                pass
            del self.active_streams[camera_id]
