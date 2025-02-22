from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
import cv2
from datetime import datetime
import asyncio
from dataclasses import dataclass

from ..base import BaseComponent
from ..utils.errors import SpoofingError

@dataclass
class SpoofingResult:
    """Anti-spoofing analysis result"""
    is_real: bool
    confidence: float
    attack_type: Optional[str]
    texture_score: float
    depth_score: float
    reflection_score: float
    motion_score: float
    timestamp: datetime

class AntiSpoofing(BaseComponent):
    """Advanced anti-spoofing detection system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Load models
        self._texture_model = self._load_texture_model()
        self._depth_model = self._load_depth_model()
        self._reflection_model = self._load_reflection_model()
        
        # Processing settings
        self._face_size = config.get('security.face_size', 224)
        self._batch_size = config.get('security.batch_size', 16)
        self._threshold = config.get('security.spoof_threshold', 0.8)
        
        # Attack types
        self._attack_types = [
            'print', 'replay', 'mask', 'deepfake'
        ]
        
        # Motion analysis
        self._motion_window = config.get('security.motion_window', 10)
        self._frame_history: Dict[str, List[np.ndarray]] = {}
        
        # Image preprocessing
        self._normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        # Statistics
        self._stats = {
            'total_checks': 0,
            'spoof_detected': 0,
            'average_confidence': 0.0,
            'attack_distribution': {t: 0 for t in self._attack_types}
        }

    def _load_texture_model(self) -> nn.Module:
        """Load texture analysis model"""
        try:
            model_path = self.config.get('security.texture_model')
            if not model_path:
                raise SpoofingError("Texture model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise SpoofingError(f"Failed to load texture model: {str(e)}")

    def _load_depth_model(self) -> nn.Module:
        """Load depth estimation model"""
        try:
            model_path = self.config.get('security.depth_model')
            if not model_path:
                raise SpoofingError("Depth model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise SpoofingError(f"Failed to load depth model: {str(e)}")

    def _load_reflection_model(self) -> nn.Module:
        """Load reflection analysis model"""
        try:
            model_path = self.config.get('security.reflection_model')
            if not model_path:
                raise SpoofingError("Reflection model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise SpoofingError(f"Failed to load reflection model: {str(e)}")

    async def check_spoofing(self,
                           face_img: np.ndarray,
                           face_id: Optional[str] = None) -> SpoofingResult:
        """Check for spoofing attempts"""
        try:
            # Preprocess image
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                raise SpoofingError("Face preprocessing failed")
            
            # Analyze texture
            texture_score = await self._analyze_texture(face_tensor)
            
            # Analyze depth
            depth_score = await self._analyze_depth(face_tensor)
            
            # Analyze reflections
            reflection_score = await self._analyze_reflections(face_tensor)
            
            # Analyze motion if face_id provided
            motion_score = 0.0
            if face_id:
                motion_score = await self._analyze_motion(face_img, face_id)
            
            # Calculate final score
            weights = {
                'texture': 0.4,
                'depth': 0.3,
                'reflection': 0.2,
                'motion': 0.1
            }
            
            final_score = (
                texture_score * weights['texture'] +
                depth_score * weights['depth'] +
                reflection_score * weights['reflection'] +
                motion_score * weights['motion']
            )
            
            # Determine if real
            is_real = final_score >= self._threshold
            
            # Detect attack type if spoof
            attack_type = None
            if not is_real:
                attack_type = await self._detect_attack_type(
                    texture_score,
                    depth_score,
                    reflection_score
                )
            
            # Create result
            result = SpoofingResult(
                is_real=is_real,
                confidence=final_score,
                attack_type=attack_type,
                texture_score=texture_score,
                depth_score=depth_score,
                reflection_score=reflection_score,
                motion_score=motion_score,
                timestamp=datetime.utcnow()
            )
            
            # Update statistics
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            raise SpoofingError(f"Spoofing check failed: {str(e)}")

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

    async def _analyze_texture(self, face_tensor: torch.Tensor) -> float:
        """Analyze facial texture"""
        try:
            with torch.no_grad():
                texture_features = self._texture_model(face_tensor)
                texture_score = torch.sigmoid(texture_features).item()
            return float(texture_score)
            
        except Exception as e:
            self.logger.error(f"Texture analysis failed: {str(e)}")
            return 0.0

    async def _analyze_depth(self, face_tensor: torch.Tensor) -> float:
        """Analyze facial depth"""
        try:
            with torch.no_grad():
                depth_map = self._depth_model(face_tensor)
                depth_score = self._evaluate_depth_map(depth_map)
            return float(depth_score)
            
        except Exception as e:
            self.logger.error(f"Depth analysis failed: {str(e)}")
            return 0.0

    async def _analyze_reflections(self, face_tensor: torch.Tensor) -> float:
        """Analyze facial reflections"""
        try:
            with torch.no_grad():
                reflection_features = self._reflection_model(face_tensor)
                reflection_score = torch.sigmoid(reflection_features).item()
            return float(reflection_score)
            
        except Exception as e:
            self.logger.error(f"Reflection analysis failed: {str(e)}")
            return 0.0

    async def _analyze_motion(self,
                            face_img: np.ndarray,
                            face_id: str) -> float:
        """Analyze facial motion"""
        try:
            # Initialize history for new faces
            if face_id not in self._frame_history:
                self._frame_history[face_id] = []
            
            # Add current frame
            self._frame_history[face_id].append(face_img)
            
            # Maintain window size
            if len(self._frame_history[face_id]) > self._motion_window:
                self._frame_history[face_id].pop(0)
            
            # Need at least 2 frames for motion analysis
            if len(self._frame_history[face_id]) < 2:
                return 0.0
            
            # Calculate optical flow
            prev_frame = cv2.cvtColor(
                self._frame_history[face_id][-2],
                cv2.COLOR_BGR2GRAY
            )
            curr_frame = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            flow = cv2.calcOpticalFlowFarneback(
                prev_frame,
                curr_frame,
                None,
                0.5, 3, 15, 3, 5, 1.2, 0
            )
            
            # Analyze flow patterns
            magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            motion_score = self._evaluate_motion_patterns(magnitude)
            
            return float(motion_score)
            
        except Exception as e:
            self.logger.error(f"Motion analysis failed: {str(e)}")
            return 0.0

    def _evaluate_depth_map(self, depth_map: torch.Tensor) -> float:
        """Evaluate depth map consistency"""
        try:
            depth_map = depth_map.cpu().numpy()
            
            # Calculate depth statistics
            depth_mean = np.mean(depth_map)
            depth_std = np.std(depth_map)
            depth_gradient = np.gradient(depth_map)
            
            # Evaluate consistency
            consistency_score = 1.0 - (depth_std / depth_mean)
            gradient_score = np.mean(np.abs(depth_gradient))
            
            # Combine scores
            depth_score = (consistency_score + gradient_score) / 2
            
            return float(np.clip(depth_score, 0.0, 1.0))
            
        except Exception:
            return 0.0

    def _evaluate_motion_patterns(self, magnitude: np.ndarray) -> float:
        """Evaluate motion patterns"""
        try:
            # Calculate motion statistics
            motion_mean = np.mean(magnitude)
            motion_std = np.std(magnitude)
            
            # Evaluate naturalness
            naturalness_score = 1.0 - (motion_std / (motion_mean + 1e-6))
            
            # Scale score
            motion_score = np.clip(naturalness_score, 0.0, 1.0)
            
            return float(motion_score)
            
        except Exception:
            return 0.0

    async def _detect_attack_type(self,
                                texture_score: float,
                                depth_score: float,
                                reflection_score: float) -> str:
        """Detect type of spoofing attack"""
        try:
            # Feature vector
            features = np.array([
                texture_score,
                depth_score,
                reflection_score
            ])
            
            # Simple rule-based detection
            if texture_score < 0.3:
                return 'print'
            elif reflection_score < 0.3:
                return 'replay'
            elif depth_score < 0.3:
                return 'mask'
            else:
                return 'deepfake'
            
        except Exception:
            return 'unknown'

    def _update_stats(self, result: SpoofingResult) -> None:
        """Update spoofing statistics"""
        self._stats['total_checks'] += 1
        
        if not result.is_real:
            self._stats['spoof_detected'] += 1
            if result.attack_type:
                self._stats['attack_distribution'][result.attack_type] += 1
        
        # Update average confidence
        n = self._stats['total_checks']
        current_avg = self._stats['average_confidence']
        self._stats['average_confidence'] = (
            (current_avg * (n - 1) + result.confidence) / n
        )

    async def get_stats(self) -> Dict:
        """Get anti-spoofing statistics"""
        return self._stats.copy() 