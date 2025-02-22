from typing import List, Optional
import numpy as np
from .detection import BatchDetector
from ..database import DatabasePool
from ..error_handling import handle_exceptions

class FaceProcessor:
    def __init__(self, confidence_threshold: float = 0.95):
        self.detector = BatchDetector()
        self.db_pool = DatabasePool()
        self.threshold = confidence_threshold
        self._encoding_cache = {}

    @handle_exceptions(logger=recognition_logger.error)
    async def process_frame(self, frame: np.ndarray) -> List[dict]:
        faces = await self.detector.detect_faces(frame)
        results = []
        
        for face in faces:
            encoding = self._compute_encoding(face)
            match = await self._find_match(encoding)
            results.append({
                'face': face,
                'match': match,
                'confidence': match.get('confidence') if match else 0
            })
        
        return results

    async def _find_match(self, encoding: np.ndarray) -> Optional[dict]:
        async with self.db_pool.get_connection() as conn:
            stored_encodings = await conn.execute(
                "SELECT user_id, encoding_data FROM face_encodings"
            )
            # Compare with stored encodings
            for stored in stored_encodings:
                if self._compare_encodings(encoding, stored.encoding_data) > self.threshold:
                    return {
                        'user_id': stored.user_id,
                        'confidence': self._compare_encodings(encoding, stored.encoding_data)
                    }
        return None 
