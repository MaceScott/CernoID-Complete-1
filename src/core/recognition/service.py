from typing import List, Optional, Dict, Any
import numpy as np
import cv2
from pathlib import Path
import torch
from core.utils.decorators import measure_performance

class RecognitionService:
    """Face recognition service with performance optimization"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logger()
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() and 
                                 config['gpu_enabled'] else 'cpu')
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize face recognition model"""
        try:
            model_path = Path(self.config['model_path'])
            if not model_path.exists():
                raise FileNotFoundError(f"Model not found at {model_path}")
                
            self.model = torch.load(model_path, map_location=self.device)
            self.model.eval()
            self.logger.info("Face recognition model initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Model initialization failed: {str(e)}")
            raise

    @measure_performance()
    async def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces in image with optimization"""
        try:
            # Convert to grayscale for faster detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            results = []
            for (x, y, w, h) in faces:
                face_img = image[y:y+h, x:x+w]
                confidence = self._get_detection_confidence(face_img)
                
                if confidence >= self.config['confidence_threshold']:
                    results.append({
                        'bbox': (x, y, w, h),
                        'confidence': float(confidence),
                        'encoding': self._get_face_encoding(face_img)
                    })
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Face detection failed: {str(e)}")
            raise

    @torch.no_grad()
    def _get_face_encoding(self, face_img: np.ndarray) -> np.ndarray:
        """Get face encoding with optimization"""
        # Preprocess image
        face_tensor = self._preprocess_image(face_img)
        
        # Get encoding
        encoding = self.model(face_tensor.to(self.device))
        return encoding.cpu().numpy()

    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for model input"""
        # Resize image
        image = cv2.resize(image, (224, 224))
        
        # Convert to tensor
        tensor = torch.from_numpy(image.transpose(2, 0, 1))
        tensor = tensor.float() / 255.0
        tensor = tensor.unsqueeze(0)
        
        return tensor

    def _get_detection_confidence(self, face_img: np.ndarray) -> float:
        """Calculate detection confidence"""
        # Implement confidence calculation
        # This is a placeholder implementation
        return 0.95

    def _setup_logger(self):
        """Setup recognition service logger"""
        from core.logging import LogManager
        return LogManager().get_logger("RecognitionService") 