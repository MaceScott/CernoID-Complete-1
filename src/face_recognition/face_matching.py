from typing import List, Optional, Dict
import numpy as np
from core.database import DatabasePool
from core.error_handling import handle_exceptions
from weakref import WeakValueDictionary

class FaceMatcher:
    def __init__(self):
        self.db_pool = DatabasePool()
        self._encodings_cache = {}
        self._large_objects = WeakValueDictionary()
        self.threshold = 0.6

    @handle_exceptions(logger=matching_logger.error)
    async def find_matches(self, encoding: np.ndarray) -> List[Dict]:
        async with self.db_pool.get_connection() as conn:
            stored_encodings = await conn.execute(
                "SELECT user_id, encoding_data FROM face_encodings"
            )
            matches = []
            for stored in stored_encodings:
                similarity = self._compare_encodings(encoding, stored.encoding_data)
                if similarity > self.threshold:
                    matches.append({
                        'user_id': stored.user_id,
                        'confidence': float(similarity)
                    })
            return sorted(matches, key=lambda x: x['confidence'], reverse=True)

    def _compare_encodings(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        return 1 - np.linalg.norm(encoding1 - encoding2)

    def clear_cache(self):
        self._encodings_cache.clear() 
