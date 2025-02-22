from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
import cv2
from dataclasses import dataclass
from datetime import datetime
import asyncio

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
    timestamp: datetime = None

class AttributeAnalyzer(BaseComponent):
    """Advanced facial attribute analysis system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Load models
        self._age_model = self._load_age_model()
        self._gender_model = self._load_gender_model()
        self._attribute_model = self._load_attribute_model()
        
        # Processing settings
        self._face_size = config.get('attributes.face_size', 224)
        self._batch_size = config.get('attributes.batch_size', 16)
        
        # Age ranges
        self._age_ranges = [
            (0, 2), (3, 6), (7, 12), (13, 17),
            (18, 24), (25, 34), (35, 44), (45, 54),
            (55, 64), (65, 74), (75, 100)
        ]
        
        # Attribute categories
        self._genders = ['male', 'female']
        self._ethnicities = [
            'caucasian', 'asian', 'african',
            'indian', 'middle_eastern', 'latino'
        ]
        
        # Image preprocessing
        self._normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        # Statistics
        self._stats = {
            'faces_analyzed': 0,
            'age_distribution': {str(r): 0 for r in self._age_ranges},
            'gender_distribution': {g: 0 for g in self._genders},
            'average_confidence': 0.0
        }

    def _load_age_model(self) -> nn.Module:
        """Load age estimation model"""
        try:
            model_path = self.config.get('attributes.age_model')
            if not model_path:
                raise AttributeError("Age model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise AttributeError(f"Failed to load age model: {str(e)}")

    def _load_gender_model(self) -> nn.Module:
        """Load gender classification model"""
        try:
            model_path = self.config.get('attributes.gender_model')
            if not model_path:
                raise AttributeError("Gender model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise AttributeError(f"Failed to load gender model: {str(e)}")

    def _load_attribute_model(self) -> nn.Module:
        """Load additional attribute model"""
        try:
            model_path = self.config.get('attributes.attribute_model')
            if not model_path:
                raise AttributeError("Attribute model path not configured")
                
            model = torch.load(model_path)
            if torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            
            return model
            
        except Exception as e:
            raise AttributeError(f"Failed to load attribute model: {str(e)}")

    async def analyze_attributes(self, face_img: np.ndarray) -> PersonAttributes:
        """Analyze facial attributes"""
        try:
            # Preprocess image
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                raise AttributeError("Face preprocessing failed")
            
            # Estimate age
            age, age_range = await self._estimate_age(face_tensor)
            
            # Classify gender
            gender, gender_conf = await self._classify_gender(face_tensor)
            
            # Get additional attributes
            attributes = await self._analyze_additional(face_tensor)
            
            # Create result
            result = PersonAttributes(
                age=age,
                age_range=age_range,
                gender=gender,
                gender_confidence=gender_conf,
                ethnicity=attributes.get('ethnicity'),
                ethnicity_confidence=attributes.get('ethnicity_confidence'),
                glasses=attributes.get('glasses'),
                beard=attributes.get('beard'),
                timestamp=datetime.utcnow()
            )
            
            # Update statistics
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            raise AttributeError(f"Attribute analysis failed: {str(e)}")

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

    async def _estimate_age(self,
                          face_tensor: torch.Tensor) -> Tuple[float, Tuple[int, int]]:
        """Estimate age and age range"""
        try:
            with torch.no_grad():
                age_pred = self._age_model(face_tensor)
                
                # Get regression output
                age = float(age_pred[0].item())
                
                # Get age range
                age_range = None
                for age_min, age_max in self._age_ranges:
                    if age_min <= age <= age_max:
                        age_range = (age_min, age_max)
                        break
                
                if age_range is None:
                    age_range = self._age_ranges[-1]
                
                return age, age_range
                
        except Exception as e:
            self.logger.error(f"Age estimation failed: {str(e)}")
            return 0.0, self._age_ranges[0]

    async def _classify_gender(self,
                             face_tensor: torch.Tensor) -> Tuple[str, float]:
        """Classify gender"""
        try:
            with torch.no_grad():
                gender_pred = self._gender_model(face_tensor)
                probs = torch.softmax(gender_pred, dim=1)
                
                # Get prediction
                gender_idx = torch.argmax(probs).item()
                gender = self._genders[gender_idx]
                confidence = float(probs[0, gender_idx])
                
                return gender, confidence
                
        except Exception as e:
            self.logger.error(f"Gender classification failed: {str(e)}")
            return self._genders[0], 0.0

    async def _analyze_additional(self, face_tensor: torch.Tensor) -> Dict:
        """Analyze additional attributes"""
        try:
            with torch.no_grad():
                attr_pred = self._attribute_model(face_tensor)
                
                # Get ethnicity
                ethnicity_probs = torch.softmax(attr_pred[:, :6], dim=1)
                ethnicity_idx = torch.argmax(ethnicity_probs).item()
                ethnicity = self._ethnicities[ethnicity_idx]
                ethnicity_conf = float(ethnicity_probs[0, ethnicity_idx])
                
                # Get binary attributes
                glasses_prob = torch.sigmoid(attr_pred[0, 6]).item()
                beard_prob = torch.sigmoid(attr_pred[0, 7]).item()
                
                return {
                    'ethnicity': ethnicity,
                    'ethnicity_confidence': ethnicity_conf,
                    'glasses': glasses_prob > 0.5,
                    'beard': beard_prob > 0.5
                }
                
        except Exception as e:
            self.logger.error(f"Additional attribute analysis failed: {str(e)}")
            return {}

    async def analyze_batch(self,
                          faces: List[np.ndarray]) -> List[PersonAttributes]:
        """Analyze attributes in batch"""
        try:
            results = []
            
            # Process in batches
            for i in range(0, len(faces), self._batch_size):
                batch_faces = faces[i:i + self._batch_size]
                
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
                    age_preds = self._age_model(batch_input)
                    gender_preds = self._gender_model(batch_input)
                    attr_preds = self._attribute_model(batch_input)
                
                # Process results
                for j in range(len(batch_tensors)):
                    # Get age
                    age = float(age_preds[j].item())
                    age_range = None
                    for r in self._age_ranges:
                        if r[0] <= age <= r[1]:
                            age_range = r
                            break
                    if age_range is None:
                        age_range = self._age_ranges[-1]
                    
                    # Get gender
                    gender_probs = torch.softmax(gender_preds[j:j+1], dim=1)
                    gender_idx = torch.argmax(gender_probs).item()
                    gender = self._genders[gender_idx]
                    gender_conf = float(gender_probs[0, gender_idx])
                    
                    # Get additional attributes
                    attr_pred = attr_preds[j:j+1]
                    ethnicity_probs = torch.softmax(attr_pred[:, :6], dim=1)
                    ethnicity_idx = torch.argmax(ethnicity_probs).item()
                    ethnicity = self._ethnicities[ethnicity_idx]
                    ethnicity_conf = float(ethnicity_probs[0, ethnicity_idx])
                    
                    glasses = torch.sigmoid(attr_pred[0, 6]).item() > 0.5
                    beard = torch.sigmoid(attr_pred[0, 7]).item() > 0.5
                    
                    # Create result
                    result = PersonAttributes(
                        age=age,
                        age_range=age_range,
                        gender=gender,
                        gender_confidence=gender_conf,
                        ethnicity=ethnicity,
                        ethnicity_confidence=ethnicity_conf,
                        glasses=glasses,
                        beard=beard,
                        timestamp=datetime.utcnow()
                    )
                    
                    results.append(result)
                    self._update_stats(result)
            
            return results
            
        except Exception as e:
            raise AttributeError(f"Batch analysis failed: {str(e)}")

    def _update_stats(self, result: PersonAttributes) -> None:
        """Update attribute statistics"""
        self._stats['faces_analyzed'] += 1
        
        # Update age distribution
        age_range = f"({result.age_range[0]}, {result.age_range[1]})"
        self._stats['age_distribution'][age_range] += 1
        
        # Update gender distribution
        self._stats['gender_distribution'][result.gender] += 1
        
        # Update average confidence
        n = self._stats['faces_analyzed']
        current_avg = self._stats['average_confidence']
        self._stats['average_confidence'] = (
            (current_avg * (n - 1) + result.gender_confidence) / n
        )

    async def get_stats(self) -> Dict:
        """Get attribute analysis statistics"""
        return self._stats.copy() 