from typing import List, Optional
import numpy as np
import cv2
from core.recognition.processor import BatchDetector
from core.error_handling import handle_exceptions
from core.config.manager import ConfigManager

class FaceDetector:
    def __init__(self):
        self.config = ConfigManager()
        self.batch_detector = BatchDetector(
            batch_size=self.config.get('face_detection.batch_size', 4)
        )
        self.cascade = cv2.CascadeClassifier(
            self.config.get('face_detection.cascade_path')
        )

    @handle_exceptions(logger=detection_logger.error)
    async def detect_faces(self, frames: List[np.ndarray]) -> List[dict]:
        results = await self.batch_detector.process_images(frames)
        return [
            {
                'bbox': result['bbox'],
                'confidence': result['confidence'],
                'frame_index': result['frame_index']
            }
            for result in results
            if result['confidence'] > self.config.get('face_detection.min_confidence', 0.8)
        ]

    async def detect_single_face(self, frame: np.ndarray) -> Optional[dict]:
        results = await self.detect_faces([frame])
        return results[0] if results else None
