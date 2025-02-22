from typing import Dict, Optional, Any, List, Union, Tuple
import asyncio
import cv2
import numpy as np
from datetime import datetime
import face_recognition
from ..base import BaseComponent
from ..utils.errors import handle_errors, VisionError

class VisionManager(BaseComponent):
    """Advanced computer vision management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._cameras: Dict[str, 'Camera'] = {}
        self._face_encodings: Dict[str, np.ndarray] = {}
        self._recognition_model = self.config.get('vision.model', 'hog')  # or 'cnn'
        self._confidence_threshold = self.config.get('vision.confidence', 0.6)
        self._frame_interval = self.config.get('vision.frame_interval', 3)
        self._face_db = None
        self._processing = False
        self._stats = {
            'frames_processed': 0,
            'faces_detected': 0,
            'faces_recognized': 0,
            'alerts_triggered': 0
        }

    async def initialize(self) -> None:
        """Initialize vision manager"""
        try:
            # Initialize face database
            self._face_db = await self.app.db.get_collection('faces')
            
            # Load known face encodings
            await self._load_face_encodings()
            
            # Initialize cameras
            camera_configs = self.config.get('vision.cameras', {})
            for camera_id, config in camera_configs.items():
                await self.add_camera(camera_id, config)
            
            # Start background tasks
            self._start_background_tasks()
            
        except Exception as e:
            raise VisionError(f"Vision initialization failed: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup vision resources"""
        try:
            # Stop all cameras
            for camera in self._cameras.values():
                await camera.stop()
            
            self._cameras.clear()
            self._face_encodings.clear()
            self._processing = False
            
        except Exception as e:
            self.logger.error(f"Vision cleanup error: {str(e)}")

    @handle_errors(logger=None)
    async def add_camera(self,
                        camera_id: str,
                        config: Dict) -> 'Camera':
        """Add camera to system"""
        try:
            from .camera import Camera
            
            camera = Camera(
                camera_id,
                config,
                self._frame_interval,
                self
            )
            await camera.initialize()
            
            self._cameras[camera_id] = camera
            return camera
            
        except Exception as e:
            raise VisionError(f"Camera addition failed: {str(e)}")

    @handle_errors(logger=None)
    async def register_face(self,
                          person_id: str,
                          image: Union[str, np.ndarray],
                          metadata: Dict) -> bool:
        """Register new face"""
        try:
            # Load and process image
            if isinstance(image, str):
                image = cv2.imread(image)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect face locations
            face_locations = face_recognition.face_locations(
                image,
                model=self._recognition_model
            )
            
            if not face_locations:
                raise VisionError("No face detected in image")
            
            # Generate face encoding
            face_encoding = face_recognition.face_encodings(
                image,
                face_locations
            )[0]
            
            # Store in database
            await self._face_db.insert_one({
                'person_id': person_id,
                'encoding': face_encoding.tolist(),
                'metadata': metadata,
                'created_at': datetime.utcnow()
            })
            
            # Update local cache
            self._face_encodings[person_id] = face_encoding
            
            return True
            
        except Exception as e:
            raise VisionError(f"Face registration failed: {str(e)}")

    async def process_frame(self,
                          frame: np.ndarray,
                          camera_id: str) -> List[Dict]:
        """Process video frame"""
        try:
            # Skip if no face encodings
            if not self._face_encodings:
                return []
            
            # Convert frame to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(
                rgb_frame,
                model=self._recognition_model
            )
            
            if not face_locations:
                return []
            
            # Generate encodings
            face_encodings = face_recognition.face_encodings(
                rgb_frame,
                face_locations
            )
            
            results = []
            for location, encoding in zip(face_locations, face_encodings):
                # Compare with known faces
                matches = face_recognition.compare_faces(
                    list(self._face_encodings.values()),
                    encoding,
                    tolerance=self._confidence_threshold
                )
                
                if True in matches:
                    # Get matching person
                    person_id = list(self._face_encodings.keys())[
                        matches.index(True)
                    ]
                    
                    # Get person metadata
                    person = await self._face_db.find_one({
                        'person_id': person_id
                    })
                    
                    results.append({
                        'person_id': person_id,
                        'location': location,
                        'confidence': 1 - face_recognition.face_distance(
                            [self._face_encodings[person_id]],
                            encoding
                        )[0],
                        'metadata': person['metadata']
                    })
                else:
                    results.append({
                        'person_id': None,
                        'location': location,
                        'confidence': 0,
                        'metadata': None
                    })
            
            # Update stats
            self._stats['frames_processed'] += 1
            self._stats['faces_detected'] += len(face_locations)
            self._stats['faces_recognized'] += len(
                [r for r in results if r['person_id']]
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")
            return []

    async def get_camera_feed(self,
                            camera_id: str) -> Optional['Camera']:
        """Get camera feed"""
        return self._cameras.get(camera_id)

    async def get_stats(self) -> Dict[str, Any]:
        """Get vision statistics"""
        stats = self._stats.copy()
        
        # Add camera stats
        stats['cameras'] = {
            camera_id: await camera.get_stats()
            for camera_id, camera in self._cameras.items()
        }
        
        return stats

    async def _load_face_encodings(self) -> None:
        """Load face encodings from database"""
        try:
            async for face in self._face_db.find():
                self._face_encodings[face['person_id']] = np.array(
                    face['encoding']
                )
        except Exception as e:
            raise VisionError(f"Face encoding loading failed: {str(e)}")

    def _start_background_tasks(self) -> None:
        """Start background tasks"""
        asyncio.create_task(self._cleanup_task())

    async def _cleanup_task(self) -> None:
        """Cleanup task"""
        while True:
            try:
                # Perform any necessary cleanup
                await asyncio.sleep(3600)  # Run hourly
                
            except Exception as e:
                self.logger.error(f"Cleanup task error: {str(e)}")
                await asyncio.sleep(3600) 