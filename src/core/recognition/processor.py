from typing import Dict, List, Optional, Tuple
import numpy as np
import cv2
import torch
from torchvision import transforms
from datetime import datetime
from dataclasses import dataclass
import asyncio

from ..base import BaseComponent
from ..utils.errors import ProcessingError

@dataclass
class FaceFeatures:
    """Extracted face features"""
    embedding: np.ndarray
    landmarks: np.ndarray
    quality: float
    pose: Tuple[float, float, float]  # yaw, pitch, roll
    expression: str
    age: Optional[float]
    gender: Optional[str]

class FaceProcessor(BaseComponent):
    """Advanced face processing system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Load models
        self._feature_extractor = self._load_feature_model()
        self._landmark_detector = self._load_landmark_model()
        self._pose_estimator = self._load_pose_model()
        self._attribute_analyzer = self._load_attribute_model()
        
        # Processing settings
        self._face_size = config.get('recognition.face_size', 224)
        self._batch_size = config.get('recognition.batch_size', 16)
        self._min_quality = config.get('recognition.min_quality', 0.6)
        
        # Feature extraction settings
        self._normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        # Processing state
        self._processing_queue = asyncio.Queue(maxsize=100)
        self._batch_lock = asyncio.Lock()
        
        # Statistics
        self._stats = {
            'faces_processed': 0,
            'features_extracted': 0,
            'average_quality': 0.0,
            'processing_time': 0.0
        }

    def _load_feature_model(self) -> torch.nn.Module:
        """Load face feature extraction model"""
        try:
            model_path = self.config.get('recognition.feature_model')
            if not model_path:
                raise ProcessingError("Feature model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise ProcessingError(f"Failed to load feature model: {str(e)}")

    def _load_landmark_model(self) -> torch.nn.Module:
        """Load facial landmark detection model"""
        try:
            model_path = self.config.get('recognition.landmark_model')
            if not model_path:
                raise ProcessingError("Landmark model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise ProcessingError(f"Failed to load landmark model: {str(e)}")

    async def process_face(self, face_img: np.ndarray) -> Optional[FaceFeatures]:
        """Process face and extract features"""
        try:
            # Preprocess image
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                return None
            
            # Extract features
            with torch.no_grad():
                embedding = self._feature_extractor(face_tensor)
                landmarks = self._landmark_detector(face_tensor)
                
                # Convert to numpy
                embedding = embedding.cpu().numpy()
                landmarks = landmarks.cpu().numpy()
            
            # Estimate pose
            pose = await self._estimate_pose(landmarks)
            
            # Analyze face quality
            quality = await self._analyze_quality(face_img, landmarks)
            
            # Get attributes
            attributes = await self._analyze_attributes(face_tensor)
            
            # Create feature object
            features = FaceFeatures(
                embedding=embedding,
                landmarks=landmarks,
                quality=quality,
                pose=pose,
                expression=attributes.get('expression', 'unknown'),
                age=attributes.get('age'),
                gender=attributes.get('gender')
            )
            
            # Update statistics
            self._update_stats(quality)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Face processing failed: {str(e)}")
            return None

    def _preprocess_face(self, face_img: np.ndarray) -> Optional[torch.Tensor]:
        """Preprocess face image"""
        try:
            # Resize image
            face_img = cv2.resize(face_img, (self._face_size, self._face_size))
            
            # Convert to RGB
            if len(face_img.shape) == 2:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2RGB)
            elif face_img.shape[2] == 4:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGRA2RGB)
            elif face_img.shape[2] == 3:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            
            # Convert to tensor
            face_tensor = torch.from_numpy(face_img).float()
            face_tensor = face_tensor.permute(2, 0, 1)
            face_tensor = face_tensor.unsqueeze(0)
            
            # Normalize
            face_tensor = self._normalize(face_tensor)
            
            if torch.cuda.is_available():
                face_tensor = face_tensor.cuda()
            
            return face_tensor
            
        except Exception as e:
            self.logger.error(f"Face preprocessing failed: {str(e)}")
            return None

    async def _estimate_pose(self, landmarks: np.ndarray) -> Tuple[float, float, float]:
        """Estimate face pose from landmarks"""
        try:
            # Convert landmarks to 3D points
            model_points = self._get_3d_model_points()
            camera_matrix = self._get_camera_matrix()
            
            # Solve PnP
            success, rotation_vec, translation_vec = cv2.solvePnP(
                model_points,
                landmarks,
                camera_matrix,
                None
            )
            
            if not success:
                return (0.0, 0.0, 0.0)
            
            # Convert rotation vector to Euler angles
            rotation_mat, _ = cv2.Rodrigues(rotation_vec)
            pose_mat = cv2.hconcat([rotation_mat, translation_vec])
            _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
            
            return tuple(euler_angles.flatten())
            
        except Exception as e:
            self.logger.error(f"Pose estimation failed: {str(e)}")
            return (0.0, 0.0, 0.0)

    async def _analyze_quality(self,
                             face_img: np.ndarray,
                             landmarks: np.ndarray) -> float:
        """Analyze face quality"""
        try:
            # Check face size
            height, width = face_img.shape[:2]
            if height < 64 or width < 64:
                return 0.0
            
            # Calculate sharpness
            laplacian = cv2.Laplacian(face_img, cv2.CV_64F)
            sharpness = np.var(laplacian)
            
            # Calculate brightness and contrast
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Check landmark confidence
            landmark_confidence = np.mean(landmarks[:, 2])
            
            # Calculate overall quality score
            quality_score = np.mean([
                sharpness / 1000,  # Normalize sharpness
                brightness / 255,   # Normalize brightness
                contrast / 128,     # Normalize contrast
                landmark_confidence
            ])
            
            return float(np.clip(quality_score, 0.0, 1.0))
            
        except Exception as e:
            self.logger.error(f"Quality analysis failed: {str(e)}")
            return 0.0

    async def _analyze_attributes(self, face_tensor: torch.Tensor) -> Dict:
        """Analyze facial attributes"""
        try:
            with torch.no_grad():
                attributes = self._attribute_analyzer(face_tensor)
            
            # Process attributes
            results = {
                'expression': self._get_expression(attributes),
                'age': self._estimate_age(attributes),
                'gender': self._detect_gender(attributes)
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Attribute analysis failed: {str(e)}")
            return {}

    def _update_stats(self, quality: float) -> None:
        """Update processing statistics"""
        self._stats['faces_processed'] += 1
        self._stats['features_extracted'] += 1
        
        # Update average quality
        n = self._stats['faces_processed']
        current_avg = self._stats['average_quality']
        self._stats['average_quality'] = (
            (current_avg * (n - 1) + quality) / n
        )

    async def get_stats(self) -> Dict:
        """Get processor statistics"""
        return self._stats.copy() 