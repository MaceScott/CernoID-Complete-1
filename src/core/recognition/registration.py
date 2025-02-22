from typing import Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from datetime import datetime
import uuid
from pathlib import Path
from ..base import BaseComponent
from ..utils.errors import RegistrationError
from .quality import FaceQualityAssessor
import asyncio

class FaceRegistration(BaseComponent):
    """Face registration and enrollment system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Initialize components
        self._quality_assessor = FaceQualityAssessor(config)
        self._min_quality = config.get('registration.quality_threshold', 0.8)
        self._min_face_size = config.get('registration.min_face_size', 160)
        self._required_views = config.get('registration.required_views', 3)
        
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
            'average_quality': 0.0
        }

    async def register_face(self, 
                          frames: List[np.ndarray],
                          metadata: Dict) -> str:
        """Register face with multiple views"""
        try:
            async with self._processing_lock:
                # Validate inputs
                if not frames or len(frames) < self._required_views:
                    raise RegistrationError(
                        f"Insufficient views. Required: {self._required_views}"
                    )
                
                # Process each frame
                face_data = []
                for frame in frames:
                    # Detect and assess face
                    face = await self._process_frame(frame)
                    if face:
                        face_data.append(face)
                
                # Check if we have enough quality faces
                if len(face_data) < self._required_views:
                    raise RegistrationError("Insufficient quality face views")
                
                # Check for duplicates
                if await self._check_duplicate(face_data):
                    self._stats['duplicate_detections'] += 1
                    raise RegistrationError("Duplicate face detected")
                
                # Generate face ID
                face_id = str(uuid.uuid4())
                
                # Store face data
                await self._store_face_data(face_id, face_data, metadata)
                
                # Update statistics
                self._stats['total_registrations'] += 1
                self._update_quality_stats(face_data)
                
                return face_id
                
        except Exception as e:
            self._stats['failed_registrations'] += 1
            raise RegistrationError(f"Registration failed: {str(e)}")

    async def _process_frame(self, frame: np.ndarray) -> Optional[Dict]:
        """Process single frame for registration"""
        try:
            # Detect face
            faces = await self.app.recognition.detect_faces(frame)
            if not faces or len(faces) > 1:
                return None
            
            face = faces[0]
            
            # Check face size
            if not self._check_face_size(face.bbox):
                return None
            
            # Assess quality
            quality = await self._quality_assessor.assess_face(
                frame, face.bbox
            )
            if quality < self._min_quality:
                return None
            
            # Extract features
            encoding = await self.app.recognition.encode_face(face, frame)
            
            return {
                'bbox': face.bbox,
                'quality': quality,
                'encoding': encoding,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Frame processing failed: {str(e)}")
            return None

    def _check_face_size(self, bbox: Tuple[int, int, int, int]) -> bool:
        """Check if face meets minimum size requirements"""
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width >= self._min_face_size and height >= self._min_face_size

    async def _check_duplicate(self, face_data: List[Dict]) -> bool:
        """Check for duplicate faces in database"""
        try:
            # Get average encoding
            encodings = [face['encoding'] for face in face_data]
            avg_encoding = np.mean(encodings, axis=0)
            
            # Search for matches
            matches = await self.app.recognition.matcher.find_matches(
                avg_encoding,
                max_matches=1
            )
            
            # Check confidence threshold
            if matches and matches[0].confidence > 0.8:  # High confidence threshold
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
                'faces': face_data,
                'metadata': metadata,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            # Store in database
            await self.app.storage.store_face(face_id, storage_data)
            
            # Add to matcher
            avg_encoding = np.mean(
                [face['encoding'] for face in face_data],
                axis=0
            )
            await self.app.recognition.matcher.add_face(
                face_id,
                avg_encoding,
                metadata
            )
            
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

    async def get_stats(self) -> Dict:
        """Get registration statistics"""
        return self._stats.copy() 