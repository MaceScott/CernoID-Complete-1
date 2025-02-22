from typing import Optional, List, Dict
from pathlib import Path
import numpy as np

from .base import BaseService
from core.models import FaceModel
from core.processing import ImageProcessor
from core.types import FaceEncoding, DetectedFace
from core.database import DatabaseService

class RecognitionService(BaseService):
    """Handles face recognition operations"""
    
    def __init__(self, database_service: DatabaseService, config: Optional[Dict] = None):
        super().__init__(config)
        self.model: Optional[FaceModel] = None
        self.processor: Optional[ImageProcessor] = None
        self.face_database: Dict[str, FaceEncoding] = {}
        self.model_path = self.config.get('model_path', 'models/face_recognition')
        self.database_service = database_service

    async def _do_initialize(self) -> None:
        """Initialize recognition models and processors"""
        self.model = await self._load_model()
        self.processor = ImageProcessor()
        await self._load_face_database()

    async def _do_cleanup(self) -> None:
        """Cleanup recognition resources"""
        self.face_database.clear()
        if self.model:
            await self.model.unload()
        if self.processor:
            await self.processor.cleanup()

    async def detect_faces(self, image: np.ndarray) -> List[DetectedFace]:
        """Detect faces in an image"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")
            
        try:
            processed_image = await self.processor.preprocess(image)
            faces = await self.model.detect(processed_image)
            return [
                DetectedFace(
                    bbox=face.bbox,
                    confidence=face.confidence,
                    encoding=await self.model.encode(face.image)
                )
                for face in faces
            ]
        except Exception as e:
            self.logger.error(f"Face detection failed: {str(e)}")
            raise

    async def _load_model(self) -> FaceModel:
        """Load the face recognition model"""
        model_path = Path(self.model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
            
        try:
            model = FaceModel()
            await model.load(model_path)
            return model
        except Exception as e:
            self.logger.error(f"Failed to load face recognition model: {str(e)}")
            raise

    async def _load_face_database(self) -> None:
        """Load known face encodings from database"""
        try:
            faces = await self.database_service.get_all_face_encodings()
            self.face_database = {face_id: encoding for face_id, encoding in faces.items()}
            self.logger.info(f"Loaded {len(self.face_database)} faces")
        except Exception as e:
            self.logger.error(f"Face database loading failed: {str(e)}")
            raise 