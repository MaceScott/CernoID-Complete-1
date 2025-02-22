from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
import cv2
from datetime import datetime
from dataclasses import dataclass
import asyncio

from ..base import BaseComponent
from ..utils.errors import EmotionError

@dataclass
class EmotionResult:
    """Emotion recognition result"""
    primary: str
    confidence: float
    secondary: Optional[str] = None
    intensities: Dict[str, float] = None
    timestamp: datetime = None

class EmotionRecognizer(BaseComponent):
    """Advanced emotion recognition system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Emotion categories
        self._emotions = [
            'neutral', 'happy', 'sad', 'angry',
            'fear', 'surprise', 'disgust'
        ]
        
        # Load models
        self._emotion_model = self._load_emotion_model()
        self._feature_extractor = self._load_feature_extractor()
        
        # Processing settings
        self._face_size = config.get('emotion.face_size', 224)
        self._batch_size = config.get('emotion.batch_size', 16)
        self._confidence_threshold = config.get('emotion.confidence', 0.6)
        
        # Temporal smoothing
        self._smooth_window = config.get('emotion.smooth_window', 5)
        self._emotion_history: Dict[str, List[str]] = {}
        self._confidence_history: Dict[str, List[float]] = {}
        
        # Image preprocessing
        self._normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        # Statistics
        self._stats = {
            'emotions_analyzed': 0,
            'average_confidence': 0.0,
            'emotion_distribution': {e: 0 for e in self._emotions}
        }

    def _load_emotion_model(self) -> nn.Module:
        """Load emotion recognition model"""
        try:
            model_path = self.config.get('emotion.model_path')
            if not model_path:
                raise EmotionError("Emotion model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise EmotionError(f"Failed to load emotion model: {str(e)}")

    def _load_feature_extractor(self) -> nn.Module:
        """Load feature extraction model"""
        try:
            model_path = self.config.get('emotion.feature_model')
            if not model_path:
                raise EmotionError("Feature model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise EmotionError(f"Failed to load feature model: {str(e)}")

    async def analyze_emotion(self,
                            face_img: np.ndarray,
                            face_id: Optional[str] = None) -> EmotionResult:
        """Analyze facial emotion"""
        try:
            # Preprocess image
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                raise EmotionError("Face preprocessing failed")
            
            # Extract features
            with torch.no_grad():
                features = self._feature_extractor(face_tensor)
                emotion_pred = self._emotion_model(features)
                
                # Get probabilities
                probs = torch.softmax(emotion_pred, dim=1)
                probs = probs.cpu().numpy()[0]
            
            # Get primary emotion
            primary_idx = np.argmax(probs)
            primary_emotion = self._emotions[primary_idx]
            primary_conf = float(probs[primary_idx])
            
            # Get secondary emotion
            probs[primary_idx] = 0
            secondary_idx = np.argmax(probs)
            secondary_emotion = self._emotions[secondary_idx]
            
            # Create emotion intensities
            intensities = {
                emotion: float(prob)
                for emotion, prob in zip(self._emotions, probs)
            }
            
            # Apply temporal smoothing if face_id provided
            if face_id:
                primary_emotion, primary_conf = self._smooth_prediction(
                    face_id,
                    primary_emotion,
                    primary_conf
                )
            
            # Create result
            result = EmotionResult(
                primary=primary_emotion,
                confidence=primary_conf,
                secondary=secondary_emotion,
                intensities=intensities,
                timestamp=datetime.utcnow()
            )
            
            # Update statistics
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            raise EmotionError(f"Emotion analysis failed: {str(e)}")

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

    def _smooth_prediction(self,
                         face_id: str,
                         emotion: str,
                         confidence: float) -> Tuple[str, float]:
        """Apply temporal smoothing to emotion predictions"""
        try:
            # Initialize history for new faces
            if face_id not in self._emotion_history:
                self._emotion_history[face_id] = []
                self._confidence_history[face_id] = []
            
            # Add current prediction
            self._emotion_history[face_id].append(emotion)
            self._confidence_history[face_id].append(confidence)
            
            # Maintain window size
            if len(self._emotion_history[face_id]) > self._smooth_window:
                self._emotion_history[face_id].pop(0)
                self._confidence_history[face_id].pop(0)
            
            # Get most frequent emotion
            from collections import Counter
            emotions = self._emotion_history[face_id]
            emotion_counts = Counter(emotions)
            smoothed_emotion = emotion_counts.most_common(1)[0][0]
            
            # Calculate average confidence
            smoothed_confidence = np.mean(self._confidence_history[face_id])
            
            return smoothed_emotion, float(smoothed_confidence)
            
        except Exception as e:
            self.logger.error(f"Prediction smoothing failed: {str(e)}")
            return emotion, confidence

    async def analyze_batch(self,
                          faces: List[np.ndarray],
                          face_ids: Optional[List[str]] = None) -> List[EmotionResult]:
        """Analyze emotions in batch"""
        try:
            results = []
            
            # Process in batches
            for i in range(0, len(faces), self._batch_size):
                batch_faces = faces[i:i + self._batch_size]
                batch_ids = face_ids[i:i + self._batch_size] if face_ids else None
                
                # Preprocess batch
                batch_tensors = []
                for face in batch_faces:
                    tensor = self._preprocess_face(face)
                    if tensor is not None:
                        batch_tensors.append(tensor)
                
                if not batch_tensors:
                    continue
                
                # Stack tensors
                batch_input = torch.cat(batch_tensors, dim=0)
                
                # Process batch
                with torch.no_grad():
                    batch_features = self._feature_extractor(batch_input)
                    batch_emotions = self._emotion_model(batch_features)
                    batch_probs = torch.softmax(batch_emotions, dim=1)
                    batch_probs = batch_probs.cpu().numpy()
                
                # Process results
                for j, probs in enumerate(batch_probs):
                    face_id = batch_ids[j] if batch_ids else None
                    
                    # Get primary emotion
                    primary_idx = np.argmax(probs)
                    primary_emotion = self._emotions[primary_idx]
                    primary_conf = float(probs[primary_idx])
                    
                    # Apply smoothing if face_id provided
                    if face_id:
                        primary_emotion, primary_conf = self._smooth_prediction(
                            face_id,
                            primary_emotion,
                            primary_conf
                        )
                    
                    # Create result
                    result = EmotionResult(
                        primary=primary_emotion,
                        confidence=primary_conf,
                        timestamp=datetime.utcnow()
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            raise EmotionError(f"Batch analysis failed: {str(e)}")

    def _update_stats(self, result: EmotionResult) -> None:
        """Update emotion statistics"""
        self._stats['emotions_analyzed'] += 1
        
        # Update average confidence
        n = self._stats['emotions_analyzed']
        current_avg = self._stats['average_confidence']
        self._stats['average_confidence'] = (
            (current_avg * (n - 1) + result.confidence) / n
        )
        
        # Update emotion distribution
        self._stats['emotion_distribution'][result.primary] += 1

    async def get_stats(self) -> Dict:
        """Get emotion recognition statistics"""
        return self._stats.copy() 