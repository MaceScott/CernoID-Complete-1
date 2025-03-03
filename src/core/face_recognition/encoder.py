"""
Advanced face encoding system with GPU acceleration and quality assessment.

This module provides:
- Face encoding generation
- Quality assessment
- Pose estimation
- Parallel processing
- GPU acceleration
- Caching
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
import cv2
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from ..base import BaseComponent
from ..utils.errors import EncoderError

@dataclass
class EncodingResult:
    """Face encoding result with metadata"""
    encoding: np.ndarray
    quality_score: float
    pose_score: Optional[float] = None
    blur_score: Optional[float] = None
    size_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class FaceEncoder(BaseComponent):
    """Advanced face encoding system with GPU support"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Model settings
        self._encoder_model_path = config.get('encoder.model_path')
        self._quality_model_path = config.get('encoder.quality_model_path')
        
        # Processing settings
        self._batch_size = config.get('encoder.batch_size', 32)
        self._face_size = config.get('encoder.face_size', 224)
        self._min_quality = config.get('encoder.min_quality', 0.5)
        self._enhance_faces = config.get('encoder.enhance_faces', True)
        
        # GPU support
        self.device = torch.device('cuda' if torch.cuda.is_available() and 
                                 config.get('gpu_enabled', True) else 'cpu')
        
        # Initialize models
        self._encoder_model = self._load_encoder_model()
        self._quality_model = self._load_quality_model()
        
        # Thread pool for parallel processing
        self._max_workers = config.get('encoder.max_workers', 4)
        self._thread_pool = ThreadPoolExecutor(max_workers=self._max_workers)
        
        # Cache settings
        self._cache_size = config.get('encoder.cache_size', 1000)
        self._encoding_cache: Dict[str, EncodingResult] = {}
        
        # Preprocessing
        self._normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        # Statistics
        self._stats = {
            'total_encoded': 0,
            'average_quality': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'processing_time': 0.0
        }

    def _load_encoder_model(self) -> nn.Module:
        """Load face encoding model"""
        try:
            if not self._encoder_model_path:
                raise ValueError("Encoder model path not configured")
                
            model = torch.load(self._encoder_model_path, map_location=self.device)
            model.eval()
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load encoder model: {str(e)}")
            raise EncoderError(f"Failed to load encoder model: {str(e)}")

    def _load_quality_model(self) -> Optional[nn.Module]:
        """Load quality assessment model"""
        try:
            if not self._quality_model_path:
                return None
                
            model = torch.load(self._quality_model_path, map_location=self.device)
            model.eval()
            return model
            
        except Exception as e:
            self.logger.warning(f"Failed to load quality model: {str(e)}")
            return None

    async def encode_face(self,
                         face_img: np.ndarray,
                         landmarks: Optional[np.ndarray] = None) -> EncodingResult:
        """
        Generate encoding for single face
        
        Args:
            face_img: Face image array
            landmarks: Optional facial landmarks
            
        Returns:
            EncodingResult with face encoding and quality metrics
        """
        try:
            start_time = datetime.utcnow()
            
            # Check cache
            cache_key = self._get_cache_key(face_img)
            if cache_key in self._encoding_cache:
                self._stats['cache_hits'] += 1
                return self._encoding_cache[cache_key]
                
            self._stats['cache_misses'] += 1
            
            # Enhance face if enabled
            if self._enhance_faces:
                face_img = await self._enhance_face(face_img)
            
            # Preprocess image
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                raise EncoderError("Face preprocessing failed")
            
            # Generate encoding
            with torch.no_grad():
                encoding = self._encoder_model(face_tensor)
                encoding = encoding.cpu().numpy()[0]
            
            # Assess quality
            quality_scores = await self._assess_quality(face_img, face_tensor, landmarks)
            
            # Create result
            result = EncodingResult(
                encoding=encoding,
                quality_score=quality_scores['overall'],
                pose_score=quality_scores.get('pose'),
                blur_score=quality_scores.get('blur'),
                size_score=quality_scores.get('size'),
                metadata={
                    'face_size': face_img.shape[:2],
                    'enhanced': self._enhance_faces,
                    'device': str(self.device),
                    **quality_scores
                },
                timestamp=datetime.utcnow()
            )
            
            # Update cache
            self._update_cache(cache_key, result)
            
            # Update stats
            self._update_stats(result, start_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Face encoding failed: {str(e)}")
            raise EncoderError(f"Face encoding failed: {str(e)}")

    async def encode_batch(self,
                         faces: List[np.ndarray],
                         landmarks: Optional[List[np.ndarray]] = None) -> List[EncodingResult]:
        """
        Generate encodings for batch of faces
        
        Args:
            faces: List of face images
            landmarks: Optional list of facial landmarks
            
        Returns:
            List of EncodingResults
        """
        try:
            results = []
            
            # Process in batches
            for i in range(0, len(faces), self._batch_size):
                batch_faces = faces[i:i + self._batch_size]
                batch_landmarks = None
                if landmarks:
                    batch_landmarks = landmarks[i:i + self._batch_size]
                
                # Process batch in parallel
                futures = []
                for j, face in enumerate(batch_faces):
                    lm = batch_landmarks[j] if batch_landmarks else None
                    future = self._thread_pool.submit(
                        self.encode_face, face, lm
                    )
                    futures.append(future)
                
                # Collect results
                for future in futures:
                    try:
                        result = await future
                        if result is not None:
                            results.append(result)
                    except Exception as e:
                        self.logger.error(f"Batch encoding failed: {str(e)}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch encoding failed: {str(e)}")
            raise EncoderError(f"Batch encoding failed: {str(e)}")

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
            
            return face_tensor.to(self.device)
            
        except Exception as e:
            self.logger.error(f"Face preprocessing failed: {str(e)}")
            return None

    async def _enhance_face(self, face_img: np.ndarray) -> np.ndarray:
        """Enhance face image quality"""
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(face_img, cv2.COLOR_BGR2LAB)
            
            # CLAHE on L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab[..., 0] = clahe.apply(lab[..., 0])
            
            # Convert back to BGR
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # Denoise
            enhanced = cv2.fastNlMeansDenoisingColored(
                enhanced,
                None,
                10,
                10,
                7,
                21
            )
            
            return enhanced
            
        except Exception as e:
            self.logger.warning(f"Face enhancement failed: {str(e)}")
            return face_img

    async def _assess_quality(self,
                            face_img: np.ndarray,
                            face_tensor: torch.Tensor,
                            landmarks: Optional[np.ndarray]) -> Dict[str, float]:
        """Assess face quality metrics"""
        try:
            scores = {}
            
            # Size score
            face_size = face_img.shape[0] * face_img.shape[1]
            min_size = self._face_size * self._face_size
            scores['size'] = min(face_size / min_size, 1.0)
            
            # Blur score
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            scores['blur'] = min(blur / 500.0, 1.0)  # Normalized blur score
            
            # Pose score from landmarks
            if landmarks is not None:
                scores['pose'] = self._assess_pose(landmarks)
            
            # Model-based quality score
            if self._quality_model is not None:
                with torch.no_grad():
                    quality_pred = self._quality_model(face_tensor)
                    scores['model_quality'] = float(quality_pred.item())
            
            # Overall quality score
            scores['overall'] = np.mean([
                score for score in scores.values()
                if isinstance(score, (int, float))
            ])
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {str(e)}")
            return {'overall': 0.5}

    def _assess_pose(self, landmarks: np.ndarray) -> float:
        """Assess face pose using landmarks"""
        try:
            if len(landmarks) < 68:
                return 1.0
                
            # Calculate face symmetry
            left_eye = landmarks[36:42].mean(axis=0)
            right_eye = landmarks[42:48].mean(axis=0)
            
            # Eye line angle
            angle = np.abs(np.arctan2(
                right_eye[1] - left_eye[1],
                right_eye[0] - left_eye[0]
            ))
            
            # Convert to score (0-1)
            return 1.0 - (angle / (np.pi / 4))
            
        except Exception as e:
            self.logger.warning(f"Pose assessment failed: {str(e)}")
            return 1.0

    def _get_cache_key(self, face_img: np.ndarray) -> str:
        """Generate cache key for face image"""
        try:
            # Use image hash as cache key
            return str(hash(face_img.tobytes()))
        except Exception:
            return str(datetime.utcnow().timestamp())

    def _update_cache(self, key: str, result: EncodingResult) -> None:
        """Update encoding cache"""
        try:
            # Remove oldest entry if cache is full
            if len(self._encoding_cache) >= self._cache_size:
                oldest_key = min(
                    self._encoding_cache.keys(),
                    key=lambda k: self._encoding_cache[k].timestamp
                )
                del self._encoding_cache[oldest_key]
            
            # Add new entry
            self._encoding_cache[key] = result
            
        except Exception as e:
            self.logger.warning(f"Cache update failed: {str(e)}")

    def _update_stats(self, result: EncodingResult, start_time: datetime) -> None:
        """Update encoding statistics"""
        try:
            self._stats['total_encoded'] += 1
            
            # Update average quality
            n = self._stats['total_encoded']
            current_avg = self._stats['average_quality']
            self._stats['average_quality'] = (
                (current_avg * (n - 1) + result.quality_score) / n
            )
            
            # Update processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._stats['processing_time'] = (
                (self._stats['processing_time'] * (n - 1) + processing_time) / n
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update stats: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get encoding statistics"""
        return self._stats.copy()

# Global encoder instance
face_encoder = FaceEncoder({}) 