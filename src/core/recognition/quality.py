from typing import Dict, List, Optional, Tuple
import numpy as np
import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from dataclasses import dataclass
from datetime import datetime
import asyncio

from ..base import BaseComponent
from ..utils.errors import QualityError

@dataclass
class QualityMetrics:
    """Face quality metrics"""
    overall_score: float
    sharpness: float
    brightness: float
    contrast: float
    pose: Tuple[float, float, float]  # yaw, pitch, roll
    occlusion: float
    expression: float
    symmetry: float
    resolution: Tuple[int, int]
    noise_level: float
    timestamp: datetime

class QualityAssessor(BaseComponent):
    """Advanced face quality assessment system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Load models
        self._quality_model = self._load_quality_model()
        self._pose_estimator = self._load_pose_model()
        
        # Quality thresholds
        self._min_resolution = config.get('quality.min_resolution', 64)
        self._min_sharpness = config.get('quality.min_sharpness', 0.4)
        self._min_brightness = config.get('quality.min_brightness', 0.2)
        self._max_brightness = config.get('quality.max_brightness', 0.8)
        self._min_contrast = config.get('quality.min_contrast', 0.3)
        self._max_pose = config.get('quality.max_pose_angle', 30)
        self._max_occlusion = config.get('quality.max_occlusion', 0.2)
        
        # Processing settings
        self._face_size = config.get('quality.face_size', 224)
        self._batch_size = config.get('quality.batch_size', 16)
        
        # Image preprocessing
        self._normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        # Statistics
        self._stats = {
            'faces_assessed': 0,
            'average_quality': 0.0,
            'rejected_faces': 0,
            'rejection_reasons': {
                'resolution': 0,
                'sharpness': 0,
                'brightness': 0,
                'contrast': 0,
                'pose': 0,
                'occlusion': 0
            }
        }

    def _load_quality_model(self) -> nn.Module:
        """Load quality assessment model"""
        try:
            model_path = self.config.get('quality.model_path')
            if not model_path:
                raise QualityError("Quality model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise QualityError(f"Failed to load quality model: {str(e)}")

    def _load_pose_model(self) -> nn.Module:
        """Load pose estimation model"""
        try:
            model_path = self.config.get('quality.pose_model')
            if not model_path:
                raise QualityError("Pose model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise QualityError(f"Failed to load pose model: {str(e)}")

    async def assess_quality(self, face_img: np.ndarray) -> QualityMetrics:
        """Assess face image quality"""
        try:
            # Check resolution
            height, width = face_img.shape[:2]
            if height < self._min_resolution or width < self._min_resolution:
                self._stats['rejection_reasons']['resolution'] += 1
                raise QualityError("Face resolution too low")
            
            # Preprocess image
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                raise QualityError("Face preprocessing failed")
            
            # Get quality metrics
            sharpness = await self._analyze_sharpness(face_img)
            brightness = await self._analyze_brightness(face_img)
            contrast = await self._analyze_contrast(face_img)
            pose = await self._estimate_pose(face_tensor)
            occlusion = await self._detect_occlusion(face_tensor)
            expression = await self._analyze_expression(face_tensor)
            symmetry = await self._analyze_symmetry(face_img)
            noise_level = await self._estimate_noise(face_img)
            
            # Check quality thresholds
            if sharpness < self._min_sharpness:
                self._stats['rejection_reasons']['sharpness'] += 1
                raise QualityError("Face image too blurry")
                
            if brightness < self._min_brightness or brightness > self._max_brightness:
                self._stats['rejection_reasons']['brightness'] += 1
                raise QualityError("Face brightness out of range")
                
            if contrast < self._min_contrast:
                self._stats['rejection_reasons']['contrast'] += 1
                raise QualityError("Face contrast too low")
                
            if max(abs(pose[0]), abs(pose[1])) > self._max_pose:
                self._stats['rejection_reasons']['pose'] += 1
                raise QualityError("Face pose angle too large")
                
            if occlusion > self._max_occlusion:
                self._stats['rejection_reasons']['occlusion'] += 1
                raise QualityError("Face occlusion too high")
            
            # Calculate overall quality score
            weights = {
                'sharpness': 0.25,
                'brightness': 0.15,
                'contrast': 0.15,
                'pose': 0.2,
                'occlusion': 0.15,
                'expression': 0.05,
                'symmetry': 0.05
            }
            
            pose_score = 1.0 - (max(abs(pose[0]), abs(pose[1])) / 90.0)
            
            overall_score = (
                sharpness * weights['sharpness'] +
                (1.0 - abs(brightness - 0.5) * 2) * weights['brightness'] +
                contrast * weights['contrast'] +
                pose_score * weights['pose'] +
                (1.0 - occlusion) * weights['occlusion'] +
                expression * weights['expression'] +
                symmetry * weights['symmetry']
            )
            
            # Create metrics
            metrics = QualityMetrics(
                overall_score=overall_score,
                sharpness=sharpness,
                brightness=brightness,
                contrast=contrast,
                pose=pose,
                occlusion=occlusion,
                expression=expression,
                symmetry=symmetry,
                resolution=(width, height),
                noise_level=noise_level,
                timestamp=datetime.utcnow()
            )
            
            # Update statistics
            self._update_stats(metrics)
            
            return metrics
            
        except QualityError as e:
            self._stats['rejected_faces'] += 1
            raise e
        except Exception as e:
            raise QualityError(f"Quality assessment failed: {str(e)}")

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

    async def _analyze_sharpness(self, face_img: np.ndarray) -> float:
        """Analyze image sharpness"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = np.var(laplacian)
            
            # Normalize sharpness score
            sharpness = np.clip(sharpness / 1000, 0.0, 1.0)
            
            return float(sharpness)
            
        except Exception as e:
            self.logger.error(f"Sharpness analysis failed: {str(e)}")
            return 0.0

    async def _analyze_brightness(self, face_img: np.ndarray) -> float:
        """Analyze image brightness"""
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(face_img, cv2.COLOR_BGR2HSV)
            
            # Get value channel
            v = hsv[:, :, 2]
            
            # Calculate average brightness
            brightness = np.mean(v) / 255.0
            
            return float(brightness)
            
        except Exception as e:
            self.logger.error(f"Brightness analysis failed: {str(e)}")
            return 0.0

    async def _analyze_contrast(self, face_img: np.ndarray) -> float:
        """Analyze image contrast"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Calculate standard deviation
            contrast = np.std(gray) / 128.0
            
            return float(np.clip(contrast, 0.0, 1.0))
            
        except Exception as e:
            self.logger.error(f"Contrast analysis failed: {str(e)}")
            return 0.0

    async def _estimate_pose(self, face_tensor: torch.Tensor) -> Tuple[float, float, float]:
        """Estimate face pose angles"""
        try:
            with torch.no_grad():
                pose = self._pose_estimator(face_tensor)
                pose = pose.cpu().numpy()[0]
            
            return tuple(pose)
            
        except Exception as e:
            self.logger.error(f"Pose estimation failed: {str(e)}")
            return (0.0, 0.0, 0.0)

    async def _detect_occlusion(self, face_tensor: torch.Tensor) -> float:
        """Detect face occlusion"""
        try:
            with torch.no_grad():
                occlusion = self._quality_model(face_tensor)
                occlusion = torch.sigmoid(occlusion).item()
            
            return float(occlusion)
            
        except Exception as e:
            self.logger.error(f"Occlusion detection failed: {str(e)}")
            return 0.0

    async def _analyze_expression(self, face_tensor: torch.Tensor) -> float:
        """Analyze facial expression neutrality"""
        try:
            with torch.no_grad():
                expr = self._quality_model(face_tensor)
                expr = torch.sigmoid(expr).item()
            
            return float(expr)
            
        except Exception as e:
            self.logger.error(f"Expression analysis failed: {str(e)}")
            return 0.0

    async def _analyze_symmetry(self, face_img: np.ndarray) -> float:
        """Analyze face symmetry"""
        try:
            # Flip image
            flipped = cv2.flip(face_img, 1)
            
            # Calculate difference
            diff = cv2.absdiff(face_img, flipped)
            symmetry = 1.0 - (np.mean(diff) / 255.0)
            
            return float(symmetry)
            
        except Exception as e:
            self.logger.error(f"Symmetry analysis failed: {str(e)}")
            return 0.0

    async def _estimate_noise(self, face_img: np.ndarray) -> float:
        """Estimate image noise level"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Calculate noise using median filter difference
            denoised = cv2.medianBlur(gray, 3)
            noise = cv2.absdiff(gray, denoised)
            noise_level = np.mean(noise) / 255.0
            
            return float(noise_level)
            
        except Exception as e:
            self.logger.error(f"Noise estimation failed: {str(e)}")
            return 0.0

    def _update_stats(self, metrics: QualityMetrics) -> None:
        """Update quality statistics"""
        self._stats['faces_assessed'] += 1
        
        # Update average quality
        n = self._stats['faces_assessed']
        current_avg = self._stats['average_quality']
        self._stats['average_quality'] = (
            (current_avg * (n - 1) + metrics.overall_score) / n
        )

    async def get_stats(self) -> Dict:
        """Get quality assessment statistics"""
        return self._stats.copy() 