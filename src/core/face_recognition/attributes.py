"""
Advanced facial attribute analysis system with GPU acceleration.

This module provides:
- Age estimation
- Gender classification
- Ethnicity detection
- Facial feature analysis
- Quality-aware processing
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

from ..base import BaseComponent
from ..utils.errors import AttributeError

@dataclass
class PersonAttributes:
    """Person attribute analysis results"""
    age: float
    age_range: Tuple[int, int]
    gender: str
    gender_confidence: float
    ethnicity: Optional[str] = None
    ethnicity_confidence: Optional[float] = None
    glasses: Optional[bool] = None
    beard: Optional[bool] = None
    expression: Optional[str] = None
    expression_confidence: Optional[float] = None
    quality_score: Optional[float] = None
    timestamp: datetime = None

class AttributeAnalyzer(BaseComponent):
    """Advanced facial attribute analysis system"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Model settings
        self._age_model_path = config.get('attributes.age_model_path')
        self._gender_model_path = config.get('attributes.gender_model_path')
        self._attribute_model_path = config.get('attributes.attribute_model_path')
        
        # Processing settings
        self._batch_size = config.get('attributes.batch_size', 16)
        self._face_size = config.get('attributes.face_size', 224)
        self._min_confidence = config.get('attributes.min_confidence', 0.8)
        
        # GPU support
        self.device = torch.device('cuda' if torch.cuda.is_available() and 
                                 config.get('gpu_enabled', True) else 'cpu')
        
        # Initialize models
        self._age_model = self._load_age_model()
        self._gender_model = self._load_gender_model()
        self._attribute_model = self._load_attribute_model()
        
        # Preprocessing
        self._normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        # Statistics
        self._stats = {
            'total_processed': 0,
            'average_age': 0.0,
            'gender_distribution': {'male': 0, 'female': 0},
            'ethnicity_distribution': {},
            'average_confidence': 0.0,
            'processing_time': 0.0
        }

    def _load_age_model(self) -> nn.Module:
        """Load age estimation model"""
        try:
            if not self._age_model_path:
                raise ValueError("Age model path not configured")
                
            model = torch.load(self._age_model_path, map_location=self.device)
            model.eval()
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load age model: {str(e)}")
            raise AttributeError(f"Failed to load age model: {str(e)}")

    def _load_gender_model(self) -> nn.Module:
        """Load gender classification model"""
        try:
            if not self._gender_model_path:
                raise ValueError("Gender model path not configured")
                
            model = torch.load(self._gender_model_path, map_location=self.device)
            model.eval()
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load gender model: {str(e)}")
            raise AttributeError(f"Failed to load gender model: {str(e)}")

    def _load_attribute_model(self) -> nn.Module:
        """Load facial attribute analysis model"""
        try:
            if not self._attribute_model_path:
                raise ValueError("Attribute model path not configured")
                
            model = torch.load(self._attribute_model_path, map_location=self.device)
            model.eval()
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load attribute model: {str(e)}")
            raise AttributeError(f"Failed to load attribute model: {str(e)}")

    async def analyze_attributes(self, face_img: np.ndarray) -> PersonAttributes:
        """
        Analyze facial attributes
        
        Args:
            face_img: Face image array
            
        Returns:
            PersonAttributes object with analysis results
        """
        try:
            start_time = datetime.utcnow()
            
            # Preprocess image
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                raise AttributeError("Face preprocessing failed")
            
            # Get age estimation
            age, age_range = await self._estimate_age(face_tensor)
            
            # Get gender classification
            gender, gender_confidence = await self._classify_gender(face_tensor)
            
            # Get additional attributes
            attributes = await self._analyze_additional(face_tensor)
            
            # Create result
            result = PersonAttributes(
                age=age,
                age_range=age_range,
                gender=gender,
                gender_confidence=gender_confidence,
                ethnicity=attributes.get('ethnicity'),
                ethnicity_confidence=attributes.get('ethnicity_confidence'),
                glasses=attributes.get('glasses'),
                beard=attributes.get('beard'),
                expression=attributes.get('expression'),
                expression_confidence=attributes.get('expression_confidence'),
                quality_score=attributes.get('quality_score'),
                timestamp=datetime.utcnow()
            )
            
            # Update statistics
            self._update_stats(result)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._stats['processing_time'] = (
                (self._stats['processing_time'] * self._stats['total_processed'] +
                 processing_time) / (self._stats['total_processed'] + 1)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Attribute analysis failed: {str(e)}")
            raise AttributeError(f"Attribute analysis failed: {str(e)}")

    def _preprocess_face(self, face_img: np.ndarray) -> Optional[torch.Tensor]:
        """Preprocess face image for analysis"""
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

    async def _estimate_age(self,
                          face_tensor: torch.Tensor) -> Tuple[float, Tuple[int, int]]:
        """
        Estimate age from face image
        
        Returns:
            Tuple of (estimated age, age range)
        """
        try:
            with torch.no_grad():
                # Get age prediction
                output = self._age_model(face_tensor)
                age_pred = output['age'].item()
                
                # Get age range
                confidence = 0.9  # 90% confidence interval
                std_dev = output.get('std_dev', 3.0)
                margin = std_dev * 1.96  # 95% confidence interval
                
                age_min = max(0, int(age_pred - margin))
                age_max = min(100, int(age_pred + margin))
                
                return float(age_pred), (age_min, age_max)
                
        except Exception as e:
            self.logger.error(f"Age estimation failed: {str(e)}")
            return 0.0, (0, 0)

    async def _classify_gender(self,
                             face_tensor: torch.Tensor) -> Tuple[str, float]:
        """
        Classify gender from face image
        
        Returns:
            Tuple of (gender, confidence)
        """
        try:
            with torch.no_grad():
                # Get gender prediction
                output = self._gender_model(face_tensor)
                prob = torch.sigmoid(output).item()
                
                gender = 'male' if prob > 0.5 else 'female'
                confidence = max(prob, 1 - prob)
                
                return gender, float(confidence)
                
        except Exception as e:
            self.logger.error(f"Gender classification failed: {str(e)}")
            return 'unknown', 0.0

    async def _analyze_additional(self, face_tensor: torch.Tensor) -> Dict:
        """Analyze additional facial attributes"""
        try:
            with torch.no_grad():
                # Get attribute predictions
                output = self._attribute_model(face_tensor)
                
                # Process ethnicity
                ethnicity_probs = output['ethnicity']
                ethnicity_idx = torch.argmax(ethnicity_probs).item()
                ethnicity_map = ['asian', 'black', 'caucasian', 'indian', 'other']
                ethnicity = ethnicity_map[ethnicity_idx]
                ethnicity_conf = float(ethnicity_probs[ethnicity_idx])
                
                # Process expression
                expr_probs = output['expression']
                expr_idx = torch.argmax(expr_probs).item()
                expr_map = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'fearful']
                expression = expr_map[expr_idx]
                expr_conf = float(expr_probs[expr_idx])
                
                # Process binary attributes
                glasses_prob = torch.sigmoid(output['glasses']).item()
                beard_prob = torch.sigmoid(output['beard']).item()
                
                # Calculate quality score
                quality_score = float(output.get('quality_score', 1.0))
                
                return {
                    'ethnicity': ethnicity,
                    'ethnicity_confidence': ethnicity_conf,
                    'expression': expression,
                    'expression_confidence': expr_conf,
                    'glasses': glasses_prob > 0.5,
                    'beard': beard_prob > 0.5,
                    'quality_score': quality_score
                }
                
        except Exception as e:
            self.logger.error(f"Additional attribute analysis failed: {str(e)}")
            return {}

    async def analyze_batch(self,
                          faces: List[np.ndarray]) -> List[PersonAttributes]:
        """
        Analyze attributes for batch of faces
        
        Args:
            faces: List of face images
            
        Returns:
            List of PersonAttributes objects
        """
        try:
            results = []
            
            # Process in batches
            for i in range(0, len(faces), self._batch_size):
                batch_faces = faces[i:i + self._batch_size]
                batch_tensors = []
                
                # Preprocess batch
                for face in batch_faces:
                    face_tensor = self._preprocess_face(face)
                    if face_tensor is not None:
                        batch_tensors.append(face_tensor)
                
                if not batch_tensors:
                    continue
                    
                # Stack tensors
                batch_tensor = torch.cat(batch_tensors, dim=0)
                
                # Process batch
                with torch.no_grad():
                    # Get age predictions
                    age_output = self._age_model(batch_tensor)
                    age_preds = age_output['age'].cpu().numpy()
                    age_stds = age_output.get('std_dev', np.full_like(age_preds, 3.0))
                    
                    # Get gender predictions
                    gender_output = self._gender_model(batch_tensor)
                    gender_probs = torch.sigmoid(gender_output).cpu().numpy()
                    
                    # Get attribute predictions
                    attr_output = self._attribute_model(batch_tensor)
                    
                # Process results
                for j in range(len(batch_tensors)):
                    # Get age info
                    age = float(age_preds[j])
                    margin = float(age_stds[j] * 1.96)
                    age_range = (max(0, int(age - margin)),
                               min(100, int(age + margin)))
                    
                    # Get gender info
                    prob = float(gender_probs[j])
                    gender = 'male' if prob > 0.5 else 'female'
                    gender_conf = max(prob, 1 - prob)
                    
                    # Get additional attributes
                    attributes = {
                        'ethnicity': attr_output['ethnicity'][j],
                        'ethnicity_confidence': float(attr_output['ethnicity_conf'][j]),
                        'expression': attr_output['expression'][j],
                        'expression_confidence': float(attr_output['expression_conf'][j]),
                        'glasses': bool(attr_output['glasses'][j] > 0.5),
                        'beard': bool(attr_output['beard'][j] > 0.5),
                        'quality_score': float(attr_output['quality'][j])
                    }
                    
                    # Create result
                    result = PersonAttributes(
                        age=age,
                        age_range=age_range,
                        gender=gender,
                        gender_confidence=gender_conf,
                        ethnicity=attributes['ethnicity'],
                        ethnicity_confidence=attributes['ethnicity_confidence'],
                        glasses=attributes['glasses'],
                        beard=attributes['beard'],
                        expression=attributes['expression'],
                        expression_confidence=attributes['expression_confidence'],
                        quality_score=attributes['quality_score'],
                        timestamp=datetime.utcnow()
                    )
                    
                    results.append(result)
                    
                    # Update statistics
                    self._update_stats(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch attribute analysis failed: {str(e)}")
            raise AttributeError(f"Batch attribute analysis failed: {str(e)}")

    def _update_stats(self, result: PersonAttributes) -> None:
        """Update analysis statistics"""
        try:
            self._stats['total_processed'] += 1
            
            # Update average age
            n = self._stats['total_processed']
            current_avg = self._stats['average_age']
            self._stats['average_age'] = (current_avg * (n - 1) + result.age) / n
            
            # Update gender distribution
            if result.gender in self._stats['gender_distribution']:
                self._stats['gender_distribution'][result.gender] += 1
            
            # Update ethnicity distribution
            if result.ethnicity:
                if result.ethnicity not in self._stats['ethnicity_distribution']:
                    self._stats['ethnicity_distribution'][result.ethnicity] = 0
                self._stats['ethnicity_distribution'][result.ethnicity] += 1
            
            # Update average confidence
            self._stats['average_confidence'] = (
                (self._stats['average_confidence'] * (n - 1) +
                 result.gender_confidence) / n
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update stats: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get analysis statistics"""
        return self._stats.copy()

# Global analyzer instance
attribute_analyzer = AttributeAnalyzer({}) 