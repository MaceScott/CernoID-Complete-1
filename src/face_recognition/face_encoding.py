from typing import List
import numpy as np
from functools import lru_cache
from core.error_handling import handle_exceptions
from core.config.manager import ConfigManager

class FaceEncoder:
    def __init__(self):
        self.config = ConfigManager()
        self._model = self._load_model()
        
    def _load_model(self):
        model_path = self.config.get('face_encoding.model_path')
        return dlib.face_recognition_model_v1(model_path)

    @lru_cache(maxsize=1000)
    def compute_face_encoding(self, face_image: np.ndarray) -> np.ndarray:
        return np.array(self._model.compute_face_descriptor(face_image))

    @handle_exceptions(logger=encoding_logger.error)
    async def encode_faces(self, face_images: List[np.ndarray]) -> List[np.ndarray]:
        return [self.compute_face_encoding(face) for face in face_images]

    def clear_cache(self):
        self.compute_face_encoding.cache_clear() 
