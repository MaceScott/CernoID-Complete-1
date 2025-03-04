"""
Advanced face registration system with quality assessment and duplicate detection.
"""

from typing import Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from datetime import datetime
import uuid
from pathlib import Path
import asyncio
from dataclasses import dataclass

from ..base import BaseComponent
from ..utils.errors import RegistrationError
from ..utils.decorators import measure_performance
from .quality import QualityAssessor
from .core import FaceDetection, FaceRecognitionSystem

@dataclass
class RegistrationResult:
    """Face registration result"""
    face_id: str
    quality_scores: List[float]
    view_count: int
    metadata: Dict
    timestamp: datetime

class FaceRegistration(BaseComponent):
    """Advanced face registration system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Initialize components
        self._quality_assessor = QualityAssessor(config)
        self._recognition = FaceRecognitionSystem()
        
        # Registration settings
        self._min_quality = config.get('registration.quality_threshold', 0.8)
        self._min_face_size = config.get('registration.min_face_size', 160)
        self._required_views = config.get('registration.required_views', 3)
        self._max_views = config.get('registration.max_views', 5)
        self._duplicate_threshold = config.get('registration.duplicate_threshold', 0.8)
        
        # Storage paths
        self._storage_path = Path(config.get('registration.storage_path', 'data/faces'))
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Processing state
        self._processing_lock = asyncio.Lock()
        
        # Statistics
        self._stats = {
            'total_registrations': 0,
            'failed_registrations': 0,
            'duplicate_detections': 0,
            'average_quality': 0.0,
            'registration_times': []
        }

    @measure_performance()
    async def register_face(self, 
                          frames: List[np.ndarray],
                          metadata: Dict) -> RegistrationResult:
        """
        Register face with multiple views and quality assessment
        
        Args:
            frames: List of face images from different angles
            metadata: Additional information about the face
            
        Returns:
            RegistrationResult with face ID and quality metrics
        """
        try:
            async with self._processing_lock:
                start_time = datetime.utcnow()
                
                # Validate inputs
                if not frames or len(frames) < self._required_views:
                    raise RegistrationError(
                        f"Insufficient views. Required: {self._required_views}"
                    )
                
                # Process each frame
                face_data = []
                quality_scores = []
                
                for frame in frames[:self._max_views]:
                    # Detect and assess face
                    face = await self._process_frame(frame)
                    if face:
                        face_data.append(face)
                        quality_scores.append(face['quality'])
                
                # Check if we have enough quality faces
                if len(face_data) < self._required_views:
                    raise RegistrationError(
                        f"Insufficient quality face views. Got {len(face_data)}, need {self._required_views}"
                    )
                
                # Check for duplicates
                if await self._check_duplicate(face_data):
                    self._stats['duplicate_detections'] += 1
                    raise RegistrationError("Duplicate face detected in database")
                
                # Generate face ID
                face_id = str(uuid.uuid4())
                
                # Store face data
                await self._store_face_data(face_id, face_data, metadata)
                
                # Create result
                result = RegistrationResult(
                    face_id=face_id,
                    quality_scores=quality_scores,
                    view_count=len(face_data),
                    metadata=metadata,
                    timestamp=datetime.utcnow()
                )
                
                # Update statistics
                self._stats['total_registrations'] += 1
                self._update_quality_stats(face_data)
                
                # Record registration time
                duration = (datetime.utcnow() - start_time).total_seconds()
                self._stats['registration_times'].append(duration)
                
                return result
                
        except Exception as e:
            self._stats['failed_registrations'] += 1
            raise RegistrationError(f"Registration failed: {str(e)}")

    async def _process_frame(self, frame: np.ndarray) -> Optional[Dict]:
        """Process single frame for registration"""
        try:
            # Detect faces
            detections = await self._recognition.detect_faces(frame)
            if not detections or len(detections) > 1:
                self.logger.warning(f"Invalid face count: {len(detections)}")
                return None
            
            detection = detections[0]
            
            # Check face size
            if not self._check_face_size(detection.bbox):
                self.logger.warning("Face too small for registration")
                return None
            
            # Assess quality
            quality_metrics = await self._quality_assessor.assess_quality(
                detection.face_image
            )
            
            if quality_metrics.overall_score < self._min_quality:
                self.logger.info(f"Face quality too low: {quality_metrics.overall_score:.2f}")
                return None
            
            # Generate encoding
            encodings = await self._recognition.encode_faces([detection])
            if not encodings:
                self.logger.error("Failed to generate face encoding")
                return None
            
            return {
                'bbox': detection.bbox,
                'quality': quality_metrics.overall_score,
                'quality_metrics': quality_metrics,
                'encoding': encodings[0],
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Frame processing failed: {str(e)}")
            return None

    def _check_face_size(self, bbox: Tuple[int, int, int, int]) -> bool:
        """Check if face meets minimum size requirements"""
        width = bbox[2]
        height = bbox[3]
        return width >= self._min_face_size and height >= self._min_face_size

    async def _check_duplicate(self, face_data: List[Dict]) -> bool:
        """Check for duplicate faces in database"""
        try:
            # Get average encoding
            encodings = [face['encoding'] for face in face_data]
            avg_encoding = np.mean(encodings, axis=0)
            
            # Search for matches
            matches = await self._recognition.find_matches(avg_encoding)
            
            # Check confidence threshold
            if matches and matches[0].confidence > self._duplicate_threshold:
                self.logger.warning(
                    f"Duplicate face found with confidence: {matches[0].confidence:.2f}"
                )
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Duplicate check failed: {str(e)}")
            return False

    async def _store_face_data(self,
                             face_id: str,
                             face_data: List[Dict],
                             metadata: Dict) -> None:
        """Store face data securely"""
        try:
            # Prepare storage data
            storage_data = {
                'id': face_id,
                'faces': [
                    {
                        'bbox': face['bbox'],
                        'quality': face['quality'],
                        'quality_metrics': face['quality_metrics'].__dict__,
                        'timestamp': face['timestamp'].isoformat()
                    }
                    for face in face_data
                ],
                'metadata': metadata,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            # Save face images
            face_dir = self._storage_path / face_id
            face_dir.mkdir(parents=True, exist_ok=True)
            
            for idx, face in enumerate(face_data):
                image_path = face_dir / f"view_{idx}.jpg"
                x, y, w, h = face['bbox']
                face_img = frame[y:y+h, x:x+w]
                cv2.imwrite(str(image_path), face_img)
                
            # Store metadata
            metadata_path = face_dir / "metadata.json"
            import json
            with open(metadata_path, 'w') as f:
                json.dump(storage_data, f, indent=2)
            
            # Add to recognition system
            avg_encoding = np.mean(
                [face['encoding'] for face in face_data],
                axis=0
            )
            
            await self._recognition.add_face(
                face_id,
                avg_encoding,
                metadata
            )
            
            self.logger.info(f"Face data stored successfully: {face_id}")
            
        except Exception as e:
            raise RegistrationError(f"Storage failed: {str(e)}")

    def _update_quality_stats(self, face_data: List[Dict]) -> None:
        """Update quality statistics"""
        qualities = [face['quality'] for face in face_data]
        avg_quality = np.mean(qualities)
        
        # Update running average
        total = self._stats['total_registrations']
        current_avg = self._stats['average_quality']
        self._stats['average_quality'] = (
            (current_avg * (total - 1) + avg_quality) / total
        )
        
        # Trim registration times list
        if len(self._stats['registration_times']) > 1000:
            self._stats['registration_times'] = self._stats['registration_times'][-1000:]

    async def get_stats(self) -> Dict:
        """Get registration statistics"""
        stats = self._stats.copy()
        
        # Add average registration time
        if stats['registration_times']:
            stats['average_registration_time'] = np.mean(stats['registration_times'])
        
        return stats 