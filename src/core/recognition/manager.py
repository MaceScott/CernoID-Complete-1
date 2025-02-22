from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import cv2
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from ..base import BaseComponent
from ..utils.errors import RecognitionError
from ..utils.metrics import PerformanceMetrics

@dataclass
class DetectedFace:
    """Represents a detected face with its data"""
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    landmarks: Optional[np.ndarray] = None
    encoding: Optional[np.ndarray] = None
    frame_id: Optional[str] = None

class RecognitionManager(BaseComponent):
    """Enhanced facial recognition manager"""
    
    def __init__(self, config: dict):
        self._validate_config(config)
        super().__init__(config)
        
        # Initialize face detection model
        self._detector = self._initialize_detector()
        self._encoder = self._initialize_encoder()
        
        # Recognition settings
        self._min_face_size = config.get('recognition.min_face_size', 64)
        self._detection_threshold = config.get('recognition.detection_threshold', 0.8)
        self._matching_threshold = config.get('recognition.matching_threshold', 0.6)
        
        # Processing queues and cache
        self._detection_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._encoding_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._face_cache: Dict[str, np.ndarray] = {}
        
        # Thread pool for CPU-intensive operations
        self._thread_pool = ThreadPoolExecutor(
            max_workers=config.get('recognition.workers', 2),
            thread_name_prefix='recognition'
        )
        
        # Performance monitoring
        self._metrics = PerformanceMetrics()
        
        # Processing state
        self._processing = False
        self._last_cleanup = datetime.utcnow()
        
        # Statistics
        self._stats = {
            'faces_detected': 0,
            'faces_recognized': 0,
            'average_detection_time': 0.0,
            'average_matching_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    def _validate_config(self, config: dict) -> None:
        """Validate recognition configuration"""
        required_keys = [
            'recognition.model_path',
            'recognition.device',
            'recognition.batch_size'
        ]
        
        for key in required_keys:
            if not self._get_nested_config(config, key):
                raise RecognitionError(f"Missing required config: {key}")

    def _get_nested_config(self, config: dict, key: str) -> Optional[any]:
        """Safely get nested configuration value"""
        keys = key.split('.')
        value = config
        
        for k in keys:
            if not isinstance(value, dict):
                return None
            value = value.get(k)
            
        return value

    async def initialize(self) -> None:
        """Initialize recognition system"""
        try:
            # Verify model files
            model_path = Path(self.config['recognition.model_path'])
            if not model_path.exists():
                raise RecognitionError(f"Model not found: {model_path}")
            
            # Start processing workers
            self._processing = True
            asyncio.create_task(self._detection_worker())
            asyncio.create_task(self._encoding_worker())
            asyncio.create_task(self._cache_cleanup_worker())
            
            self.logger.info("Recognition manager initialized successfully")
            
        except Exception as e:
            raise RecognitionError(f"Initialization failed: {str(e)}")

    async def detect_faces(self, frame: np.ndarray) -> List[DetectedFace]:
        """Detect faces in frame with improved error handling"""
        try:
            async with self._metrics.measure('detection_time'):
                # Validate frame
                if frame is None or frame.size == 0:
                    raise ValueError("Invalid frame")
                
                # Prepare frame
                prepared_frame = self._prepare_frame(frame)
                
                # Detect faces
                detections = await self._run_detection(prepared_frame)
                
                # Process detections
                faces = []
                for det in detections:
                    if det.confidence >= self._detection_threshold:
                        face = DetectedFace(
                            bbox=det.bbox,
                            confidence=det.confidence,
                            frame_id=self._generate_frame_id(frame)
                        )
                        faces.append(face)
                
                # Update statistics
                self._stats['faces_detected'] += len(faces)
                
                return faces
                
        except Exception as e:
            self.logger.error(f"Face detection failed: {str(e)}")
            raise RecognitionError(f"Detection failed: {str(e)}")

    async def encode_face(self, face: DetectedFace, frame: np.ndarray) -> np.ndarray:
        """Extract face encoding with validation"""
        try:
            async with self._metrics.measure('encoding_time'):
                # Validate inputs
                if face is None or frame is None:
                    raise ValueError("Invalid face or frame")
                
                # Extract face region
                face_img = self._extract_face_region(frame, face.bbox)
                
                # Generate encoding
                encoding = await self._run_encoding(face_img)
                
                # Validate encoding
                if not self._validate_encoding(encoding):
                    raise RecognitionError("Invalid face encoding generated")
                
                return encoding
                
        except Exception as e:
            self.logger.error(f"Face encoding failed: {str(e)}")
            raise RecognitionError(f"Encoding failed: {str(e)}")

    def _prepare_frame(self, frame: np.ndarray) -> np.ndarray:
        """Prepare frame for processing"""
        # Resize if needed
        if frame.shape[0] > 1080 or frame.shape[1] > 1920:
            scale = min(1080 / frame.shape[0], 1920 / frame.shape[1])
            new_size = (
                int(frame.shape[1] * scale),
                int(frame.shape[0] * scale)
            )
            frame = cv2.resize(frame, new_size)
        
        # Convert to RGB if needed
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        elif frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
            
        return frame

    async def _detection_worker(self) -> None:
        """Worker for processing detection queue"""
        while self._processing:
            try:
                # Get frame from queue
                frame_data = await self._detection_queue.get()
                
                # Process frame
                faces = await self.detect_faces(frame_data['frame'])
                
                # Handle results
                await self._handle_detections(faces, frame_data)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Detection worker error: {str(e)}")
                await asyncio.sleep(1)

    async def cleanup(self) -> None:
        """Cleanup recognition resources"""
        try:
            self._processing = False
            
            # Clear queues
            while not self._detection_queue.empty():
                self._detection_queue.get_nowait()
            while not self._encoding_queue.empty():
                self._encoding_queue.get_nowait()
            
            # Shutdown thread pool
            self._thread_pool.shutdown(wait=True)
            
            # Clear cache
            self._face_cache.clear()
            
            self.logger.info("Recognition manager cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get recognition statistics"""
        stats = self._stats.copy()
        
        # Add metrics
        stats.update({
            'detection_time': self._metrics.get_average('detection_time'),
            'encoding_time': self._metrics.get_average('encoding_time'),
            'cache_size': len(self._face_cache)
        })
        
        return stats 