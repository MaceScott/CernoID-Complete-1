from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
import cv2
from datetime import datetime
import asyncio
from dataclasses import dataclass
import dlib
import tensorflow as tf
import time
from collections import deque
from ..utils.config import get_settings
from ..utils.logging import get_logger
from pydantic import BaseModel, ValidationError

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

@dataclass
class LivenessScore:
    """Liveness detection result with detailed scores"""
    overall_score: float
    blink_score: float
    texture_score: float
    depth_score: float
    ir_score: Optional[float]
    motion_score: float
    timestamp: float
    metadata: Dict[str, Any]

class AntiSpoofingConfig(BaseModel):
    face_size: int = 224
    batch_size: int = 16
    spoof_threshold: float = 0.8
    motion_window: int = 10
    texture_model: str
    depth_model: str
    reflection_model: str

class AntiSpoofing(BaseComponent):
    """Advanced anti-spoofing detection system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = get_logger(__name__)
        try:
            validated_config = AntiSpoofingConfig(**config.get('security', {}))
        except ValidationError as e:
            self.logger.error(f"Invalid anti-spoofing configuration: {e}")
            raise SpoofingError(f"Invalid anti-spoofing configuration: {e}")
        self._face_size = validated_config.face_size
        self._batch_size = validated_config.batch_size
        self._threshold = validated_config.spoof_threshold
        self._motion_window = validated_config.motion_window
        self._texture_model = self._load_texture_model(validated_config.texture_model)
        self._depth_model = self._load_depth_model(validated_config.depth_model)
        self._reflection_model = self._load_reflection_model(validated_config.reflection_model)
        
        # Attack types
        self._attack_types = [
            'print', 'replay', 'mask', 'deepfake'
        ]
        
        # Motion analysis
        self._frame_history: Dict[str, deque] = {}
        
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

    def _load_texture_model(self, model_path: str) -> nn.Module:
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            model = torch.load(model_path, map_location=device)
            model.eval()
            self.logger.info(f"Texture model loaded successfully on {device}")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load texture model: {str(e)}")
            raise SpoofingError(f"Failed to load texture model: {str(e)}")

    def _load_depth_model(self, model_path: str) -> nn.Module:
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            model = torch.load(model_path, map_location=device)
            model.eval()
            self.logger.info(f"Depth model loaded successfully on {device}")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load depth model: {str(e)}")
            raise SpoofingError(f"Failed to load depth model: {str(e)}")

    def _load_reflection_model(self, model_path: str) -> nn.Module:
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            model = torch.load(model_path, map_location=device)
            model.eval()
            self.logger.info(f"Reflection model loaded successfully on {device}")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load reflection model: {str(e)}")
            raise SpoofingError(f"Failed to load reflection model: {str(e)}")

    async def check_spoofing(self, face_img: np.ndarray, face_id: Optional[str] = None) -> SpoofingResult:
        try:
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                raise SpoofingError("Face preprocessing failed")

            tasks = [
                self._analyze_texture(face_tensor),
                self._analyze_depth(face_tensor),
                self._analyze_reflections(face_tensor)
            ]

            if face_id:
                tasks.append(self._analyze_motion(face_img, face_id))

            results = await asyncio.gather(*tasks)

            texture_score, depth_score, reflection_score = results[:3]
            motion_score = results[3] if face_id else 0.0

            final_score = (texture_score * 0.4 + depth_score * 0.3 + reflection_score * 0.2 + motion_score * 0.1)
            is_real = final_score >= self._threshold

            attack_type = None if is_real else await self._detect_attack_type(texture_score, depth_score, reflection_score)

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

            self._update_stats(result)
            self.logger.info(f"Spoofing check completed successfully: {result}")

            return result
        except Exception as e:
            self.logger.error(f"Spoofing check failed: {str(e)}")
            raise SpoofingError(f"Spoofing check failed: {str(e)}")

    def _preprocess_face(self, face_img: np.ndarray) -> Optional[torch.Tensor]:
        """Preprocess face image"""
        try:
            face_img = cv2.resize(face_img, (self._face_size, self._face_size), interpolation=cv2.INTER_AREA)
            if face_img.ndim == 2 or face_img.shape[2] == 1:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2RGB)
            elif face_img.shape[2] == 4:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGRA2RGB)
            else:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            face_tensor = torch.from_numpy(face_img).float().permute(2, 0, 1).unsqueeze(0)
            face_tensor = self._normalize(face_tensor / 255.0)
            return face_tensor.cuda() if torch.cuda.is_available() else face_tensor
        except Exception as e:
            self.logger.error(f"Face preprocessing failed: {str(e)}")
            return None

    async def _analyze_texture(self, face_tensor: torch.Tensor) -> float:
        try:
            with torch.no_grad():
                texture_features = self._texture_model(face_tensor)
                texture_score = torch.sigmoid(texture_features).item()
            self.logger.info(f"Texture analysis completed successfully with score: {texture_score}")
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
                self._frame_history[face_id] = deque(maxlen=self._motion_window)
            
            # Add current frame
            self._frame_history[face_id].append(face_img)
            
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

    async def _detect_attack_type(self, texture_score: float, depth_score: float, reflection_score: float) -> str:
        scores = {'texture': texture_score, 'depth': depth_score, 'reflection': reflection_score}
        attack_type = max(scores, key=scores.get)
        self.logger.debug(f"Detected attack type: {attack_type} with scores: {scores}")
        return attack_type

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

class AntiSpoofingSystem:
    """
    Multi-method anti-spoofing system with deep learning
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize models
        self.depth_model = self._load_depth_model()
        self.texture_model = self._load_texture_model()
        self.blink_detector = self._load_blink_detector()
        
        # Initialize IR camera if available
        self.ir_camera = self._init_ir_camera()
        
        # Motion tracking
        self.motion_history = deque(maxlen=self.settings.motion_history_size)
        self.face_landmarks = dlib.shape_predictor(
            self.settings.landmark_model_path
        )
        
        # Previous frame storage for motion analysis
        self.prev_frame = None
        self.prev_landmarks = None
        
    def _load_depth_model(self) -> tf.keras.Model:
        """Load depth estimation model"""
        try:
            model = tf.keras.models.load_model(
                self.settings.depth_model_path
            )
            self.logger.info("Depth model loaded successfully")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load depth model: {str(e)}")
            return None
            
    def _load_texture_model(self) -> tf.keras.Model:
        """Load texture analysis model"""
        try:
            model = tf.keras.models.load_model(
                self.settings.texture_model_path
            )
            self.logger.info("Texture model loaded successfully")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load texture model: {str(e)}")
            return None
            
    def _load_blink_detector(self) -> cv2.dnn.Net:
        """Load blink detection model"""
        try:
            net = cv2.dnn.readNet(
                self.settings.blink_model_weights,
                self.settings.blink_model_config
            )
            
            if self.settings.use_gpu:
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                
            self.logger.info("Blink detector loaded successfully")
            return net
        except Exception as e:
            self.logger.error(f"Failed to load blink detector: {str(e)}")
            return None
            
    def _init_ir_camera(self) -> Optional[cv2.VideoCapture]:
        """Initialize IR camera if available"""
        try:
            if self.settings.use_ir_camera:
                camera = cv2.VideoCapture(self.settings.ir_camera_index)
                if camera.isOpened():
                    self.logger.info("IR camera initialized successfully")
                    return camera
        except Exception as e:
            self.logger.error(f"Failed to initialize IR camera: {str(e)}")
        return None
        
    async def check_liveness(self,
                           frame: np.ndarray,
                           face_location: Tuple[int, int, int, int],
                           landmarks: np.ndarray) -> LivenessScore:
        """
        Perform comprehensive liveness check
        
        Args:
            frame: Input image frame
            face_location: Face bounding box
            landmarks: Facial landmarks
            
        Returns:
            Detailed liveness score
        """
        try:
            timestamp = time.time()
            
            # Extract face region
            x1, y1, x2, y2 = face_location
            face = frame[y1:y2, x1:x2]
            
            # Perform various checks
            blink_score = await self._check_blink(face, landmarks)
            texture_score = await self._analyze_texture(face)
            depth_score = await self._estimate_depth(face)
            motion_score = await self._analyze_motion(frame, landmarks)
            
            # Get IR score if available
            ir_score = None
            if self.ir_camera is not None:
                ir_score = await self._check_ir()
            
            # Calculate overall score
            weights = self.settings.liveness_weights
            overall_score = (
                weights["blink"] * blink_score +
                weights["texture"] * texture_score +
                weights["depth"] * depth_score +
                weights["motion"] * motion_score
            )
            
            if ir_score is not None:
                overall_score += weights["ir"] * ir_score
                overall_score /= sum(weights.values())
            else:
                overall_score /= sum(
                    v for k, v in weights.items() if k != "ir"
                )
            
            return LivenessScore(
                overall_score=overall_score,
                blink_score=blink_score,
                texture_score=texture_score,
                depth_score=depth_score,
                ir_score=ir_score,
                motion_score=motion_score,
                timestamp=timestamp,
                metadata=self._get_metadata(face_location)
            )
            
        except Exception as e:
            self.logger.error(f"Liveness check failed: {str(e)}")
            return self._get_default_score()
            
    async def _check_blink(self,
                          face: np.ndarray,
                          landmarks: np.ndarray) -> float:
        """Check for natural eye blinking"""
        try:
            # Extract eye regions
            left_eye = landmarks[36:42]
            right_eye = landmarks[42:48]
            
            # Calculate eye aspect ratios
            left_ear = self._eye_aspect_ratio(left_eye)
            right_ear = self._eye_aspect_ratio(right_eye)
            
            # Average eye aspect ratio
            ear = (left_ear + right_ear) / 2.0
            
            # Check if eyes are naturally open/closed
            if self.blink_detector is not None:
                # Use ML model for more accurate detection
                blob = cv2.dnn.blobFromImage(
                    face,
                    1.0,
                    (96, 96),
                    (0, 0, 0),
                    swapRB=True,
                    crop=False
                )
                self.blink_detector.setInput(blob)
                score = self.blink_detector.forward()[0][0]
            else:
                # Fallback to threshold-based detection
                score = 1.0 if ear > self.settings.blink_threshold else 0.0
                
            return float(score)
            
        except Exception as e:
            self.logger.error(f"Blink check failed: {str(e)}")
            return 0.0
            
    async def _analyze_texture(self, face: np.ndarray) -> float:
        """Analyze face texture for spoof detection"""
        try:
            if self.texture_model is None:
                return 1.0
                
            # Preprocess image
            face_resized = cv2.resize(face, (128, 128))
            face_normalized = face_resized / 255.0
            
            # Get prediction
            prediction = self.texture_model.predict(
                face_normalized.reshape(1, 128, 128, 3)
            )
            
            return float(prediction[0][0])
            
        except Exception as e:
            self.logger.error(f"Texture analysis failed: {str(e)}")
            return 0.0
            
    async def _estimate_depth(self, face: np.ndarray) -> float:
        """Estimate 3D depth for spoof detection"""
        try:
            if self.depth_model is None:
                return 1.0
                
            # Preprocess image
            face_resized = cv2.resize(face, (256, 256))
            face_normalized = face_resized / 255.0
            
            # Get depth map
            depth_map = self.depth_model.predict(
                face_normalized.reshape(1, 256, 256, 3)
            )
            
            # Analyze depth variation
            depth_std = np.std(depth_map)
            depth_score = min(depth_std / self.settings.depth_threshold, 1.0)
            
            return float(depth_score)
            
        except Exception as e:
            self.logger.error(f"Depth estimation failed: {str(e)}")
            return 0.0
            
    async def _analyze_motion(self,
                            frame: np.ndarray,
                            landmarks: np.ndarray) -> float:
        """Analyze natural head motion"""
        try:
            if self.prev_frame is None:
                self.prev_frame = frame
                self.prev_landmarks = landmarks
                return 1.0
                
            # Calculate landmark movement
            motion = np.mean(np.linalg.norm(
                landmarks - self.prev_landmarks,
                axis=1
            ))
            
            # Update motion history
            self.motion_history.append(motion)
            
            # Calculate motion consistency
            if len(self.motion_history) >= 2:
                motion_std = np.std(self.motion_history)
                motion_score = min(
                    motion_std / self.settings.motion_threshold,
                    1.0
                )
            else:
                motion_score = 1.0
                
            # Update previous frame
            self.prev_frame = frame
            self.prev_landmarks = landmarks
            
            return float(motion_score)
            
        except Exception as e:
            self.logger.error(f"Motion analysis failed: {str(e)}")
            return 0.0
            
    async def _check_ir(self) -> float:
        """Check IR image for liveness"""
        try:
            if self.ir_camera is None:
                return None
                
            ret, ir_frame = self.ir_camera.read()
            if not ret:
                return None
                
            # Analyze IR intensity distribution
            ir_gray = cv2.cvtColor(ir_frame, cv2.COLOR_BGR2GRAY)
            ir_std = np.std(ir_gray)
            
            # Calculate score based on IR variation
            ir_score = min(ir_std / self.settings.ir_threshold, 1.0)
            
            return float(ir_score)
            
        except Exception as e:
            self.logger.error(f"IR check failed: {str(e)}")
            return None
            
    def _eye_aspect_ratio(self, eye: np.ndarray) -> float:
        """Calculate eye aspect ratio"""
        # Compute euclidean distances
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        C = np.linalg.norm(eye[0] - eye[3])
        
        # Calculate eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return float(ear)
        
    def _get_metadata(self,
                     face_location: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """Get additional metadata for liveness check"""
        return {
            "face_size": (face_location[2] - face_location[0]) *
                        (face_location[3] - face_location[1]),
            "models_used": {
                "depth": self.depth_model is not None,
                "texture": self.texture_model is not None,
                "blink": self.blink_detector is not None,
                "ir": self.ir_camera is not None
            },
            "timestamp": time.time()
        }
        
    def _get_default_score(self) -> LivenessScore:
        """Get default liveness score for error cases"""
        return LivenessScore(
            overall_score=0.0,
            blink_score=0.0,
            texture_score=0.0,
            depth_score=0.0,
            ir_score=None,
            motion_score=0.0,
            timestamp=time.time(),
            metadata={"error": True}
        )
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.ir_camera is not None:
            self.ir_camera.release() 