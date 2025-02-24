"""
Face recognition pipeline with GPU acceleration.
"""
from typing import Dict, Any, List, Optional, Tuple
import torch
import numpy as np
from pathlib import Path
import cv2
from PIL import Image
import io
import base64
from datetime import datetime

from ...utils.config import get_settings
from ...utils.logging import get_logger
from ..monitoring.service import monitoring_service

class RecognitionPipeline:
    """Advanced face recognition pipeline"""
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize models
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.detector = self._load_detector()
        self.recognizer = self._load_recognizer()
        
        # Initialize monitoring
        self.monitoring = monitoring_service
        
    def _load_detector(self) -> torch.nn.Module:
        """Load face detection model."""
        try:
            model = torch.jit.load(
                self.settings.detector_path,
                map_location=self.device
            )
            model.eval()
            return model
        except Exception as e:
            self.logger.error(f"Failed to load detector: {str(e)}")
            raise
            
    def _load_recognizer(self) -> torch.nn.Module:
        """Load face recognition model."""
        try:
            model = torch.jit.load(
                self.settings.recognizer_path,
                map_location=self.device
            )
            model.eval()
            return model
        except Exception as e:
            self.logger.error(f"Failed to load recognizer: {str(e)}")
            raise
            
    async def process_image(self,
                          image_data: str,
                          options: Optional[Dict[str, Any]] = None
                          ) -> Dict[str, Any]:
        """Process image for face detection and recognition."""
        try:
            start_time = datetime.utcnow()
            
            # Decode image
            image = self._decode_image(image_data)
            
            # Detect faces
            faces = await self._detect_faces(image, options)
            
            # Extract features
            features = await self._extract_features(image, faces)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update metrics
            await self.monitoring.collect_metrics()
            
            return {
                "faces": faces,
                "features": features,
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Image processing failed: {str(e)}")
            raise
            
    def _decode_image(self, image_data: str) -> np.ndarray:
        """Decode base64 image to numpy array."""
        try:
            # Remove data URL prefix if present
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]
                
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            # Convert to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Failed to decode image")
                
            return image
            
        except Exception as e:
            self.logger.error(f"Image decoding failed: {str(e)}")
            raise
            
    async def _detect_faces(self,
                          image: np.ndarray,
                          options: Optional[Dict[str, Any]] = None
                          ) -> List[Dict[str, Any]]:
        """Detect faces in image."""
        try:
            # Prepare image tensor
            tensor = self._preprocess_image(image)
            
            # Run detection
            with torch.no_grad():
                detections = self.detector(tensor)
                
            # Post-process detections
            faces = self._process_detections(detections, image.shape)
            
            # Filter by confidence if specified
            if options and "min_confidence" in options:
                faces = [
                    face for face in faces
                    if face["confidence"] >= options["min_confidence"]
                ]
                
            return faces
            
        except Exception as e:
            self.logger.error(f"Face detection failed: {str(e)}")
            raise
            
    async def _extract_features(self,
                              image: np.ndarray,
                              faces: List[Dict[str, Any]]
                              ) -> List[np.ndarray]:
        """Extract face recognition features."""
        try:
            features = []
            
            for face in faces:
                # Extract face region
                bbox = face["bbox"]
                face_img = image[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                
                # Prepare tensor
                tensor = self._preprocess_face(face_img)
                
                # Extract features
                with torch.no_grad():
                    feature = self.recognizer(tensor)
                    
                features.append(feature.cpu().numpy())
                
            return features
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {str(e)}")
            raise
            
    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for neural network."""
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Normalize
        image = image.astype(np.float32) / 255.0
        
        # Convert to tensor
        tensor = torch.from_numpy(image).permute(2, 0, 1)
        
        # Add batch dimension
        tensor = tensor.unsqueeze(0)
        
        return tensor.to(self.device)
        
    def _preprocess_face(self, face_img: np.ndarray) -> torch.Tensor:
        """Preprocess face image for feature extraction."""
        # Resize
        face_img = cv2.resize(face_img, (112, 112))
        
        # Convert BGR to RGB
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        
        # Normalize
        face_img = face_img.astype(np.float32) / 255.0
        
        # Convert to tensor
        tensor = torch.from_numpy(face_img).permute(2, 0, 1)
        
        # Add batch dimension
        tensor = tensor.unsqueeze(0)
        
        return tensor.to(self.device)
        
    def _process_detections(self,
                          detections: torch.Tensor,
                          image_shape: Tuple[int, int, int]
                          ) -> List[Dict[str, Any]]:
        """Process raw detections into face information."""
        faces = []
        height, width = image_shape[:2]
        
        # Convert detections to face information
        for detection in detections[0]:
            confidence = float(detection[4])
            if confidence < self.settings.min_detection_confidence:
                continue
                
            # Convert normalized coordinates to pixel coordinates
            bbox = [
                int(detection[0] * width),   # x1
                int(detection[1] * height),  # y1
                int(detection[2] * width),   # x2
                int(detection[3] * height)   # y2
            ]
            
            # Add landmarks if available
            landmarks = None
            if len(detection) > 5:
                landmarks = []
                for i in range(5, 15, 2):
                    x = int(detection[i] * width)
                    y = int(detection[i + 1] * height)
                    landmarks.append([x, y])
                    
            faces.append({
                "bbox": bbox,
                "confidence": confidence,
                "landmarks": landmarks
            })
            
        return faces

# Global recognition pipeline instance
recognition_pipeline = RecognitionPipeline() 