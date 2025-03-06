"""
Unified face recognition system with centralized error handling, GPU support, and optimized performance.
"""

from typing import List, Optional, Dict, Union, Any, Tuple
import numpy as np
import cv2
from dataclasses import dataclass
from functools import lru_cache
import logging
from weakref import WeakValueDictionary
import torch
from torchvision import transforms
import base64
from datetime import datetime
from pathlib import Path
import io
from PIL import Image
import asyncio
import GPUtil
from functools import lru_cache
from cachetools import TTLCache

from src.core.events.manager import event_manager
from src.core.error_handling import handle_exceptions
from src.core.config import settings
from src.core.database import db_pool
from src.core.utils.decorators import measure_performance
from src.core.monitoring.service import monitoring_service
from gtts import gTTS
import os
import json

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class FaceFeatures:
    """Extracted face features"""
    embedding: np.ndarray
    landmarks: np.ndarray
    quality: float
    pose: Tuple[float, float, float]  # yaw, pitch, roll
    expression: str
    age: Optional[float]
    gender: Optional[str]

@dataclass
class FaceDetection:
    """Face detection result"""
    bbox: tuple[int, int, int, int]
    confidence: float
    frame_index: int
    face_image: np.ndarray
    landmarks: Optional[List[List[int]]] = None
    features: Optional[FaceFeatures] = None
    distance: Optional[float] = None  # Distance in meters

@dataclass
class FaceMatch:
    """Face matching result"""
    user_id: str
    confidence: float
    metadata: Optional[Dict] = None

class FaceRecognitionSystem:
    """Unified face recognition system with GPU support"""
    
    def __init__(self):
        self.config = settings
        self.event_manager = event_manager
        self.db_pool = db_pool
        
        # GPU configuration
        self.device = torch.device('cuda' if torch.cuda.is_available() and 
                                 self.config.gpu_enabled else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Initialize components
        self._detector = self._init_detector()
        self._encoder = self._init_encoder()
        self._landmark_detector = self._init_landmark_detector()
        self._attribute_analyzer = self._init_attribute_analyzer()
        
        # Optimize batch size based on available GPU memory
        if torch.cuda.is_available():
            gpu = GPUtil.getGPUs()[0]
            total_mem = gpu.memoryTotal
            self._batch_size = min(32, max(4, int(total_mem / 500)))  # Heuristic: 500MB per batch
        else:
            self._batch_size = 4
            
        # Enhanced caching with TTL
        self._encoding_cache = TTLCache(
            maxsize=self.config.face_recognition_cache_size,
            ttl=self.config.face_recognition_cache_ttl
        )
        
        # Optimize processing settings
        self._face_size = self.config.recognition_face_size
        self._min_quality = self.config.recognition_min_quality
        
        # Use mixed precision training
        self.scaler = torch.cuda.amp.GradScaler()
        self.use_amp = torch.cuda.is_available()
        
        # Cache settings
        self.matching_threshold = self.config.face_recognition_matching_threshold
        
        # Performance settings
        self._min_face_size = self.config.face_recognition_min_face_size
        self._scale_factor = self.config.face_recognition_scale_factor
        
        # Feature extraction settings
        self._normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        # Processing state
        self._processing_queue = asyncio.Queue(maxsize=100)
        self._batch_lock = asyncio.Lock()
        
        # Initialize monitoring
        self.monitoring = monitoring_service
        
        # Statistics
        self._stats = {
            'total_processed': 0,
            'average_inference_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'gpu_utilization': 0.0,
            'memory_usage': 0.0,
            'faces_processed': 0,
            'features_extracted': 0,
            'average_quality': 0.0,
            'processing_time': 0.0
        }
        
        # Distance detection settings
        self._focal_length = self.config.recognition_focal_length
        self._avg_face_width = self.config.recognition_avg_face_width
        self._activation_range = self.config.recognition_activation_range
        self._long_range_threshold = self.config.recognition_long_range_threshold

    def _init_detector(self) -> Union[cv2.CascadeClassifier, torch.nn.Module]:
        """Initialize face detector"""
        try:
            if self.device.type == 'cuda':
                # Use TorchScript model for GPU
                model_path = self.config.face_detection_torch_model_path
                model = torch.jit.load(model_path, map_location=self.device)
                model.eval()
                return model
            else:
                # Use OpenCV for CPU
                cascade_path = self.config.face_detection_cascade_path
                detector = cv2.CascadeClassifier(cascade_path)
                if detector.empty():
                    raise ValueError(f"Failed to load cascade classifier from {cascade_path}")
                return detector
        except Exception as e:
            logger.error(f"Error initializing face detector: {e}")
            raise

    def _init_encoder(self) -> Union['dlib.face_recognition_model_v1', torch.nn.Module]:
        """Initialize face encoder with GPU support if available"""
        try:
            if self.device.type == 'cuda':
                # Use PyTorch model for GPU
                model_path = self.config.face_encoding_torch_model_path
                model = torch.jit.load(model_path, map_location=self.device)
                model.eval()
                return model
            else:
                # Use dlib for CPU
                import dlib
                model_path = self.config.face_encoding_dlib_model_path
                return dlib.face_recognition_model_v1(model_path)
        except Exception as e:
            logger.error(f"Error initializing face encoder: {e}")
            raise

    def _init_landmark_detector(self) -> torch.nn.Module:
        """Initialize facial landmark detection model"""
        try:
            model_path = self.config.recognition_landmark_model
            if not model_path:
                raise ValueError("Landmark model path not configured")
                
            model = torch.load(model_path)
            model = model.to(self.device)
            model.eval()
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load landmark model: {str(e)}")
            raise

    def _init_attribute_analyzer(self) -> torch.nn.Module:
        """Initialize facial attribute analysis model"""
        try:
            model_path = self.config.recognition_attribute_model
            if not model_path:
                raise ValueError("Attribute model path not configured")
                
            model = torch.load(model_path)
            model = model.to(self.device)
            model.eval()
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load attribute model: {str(e)}")
            raise

    @handle_exceptions(logger_func=logger.error)
    @measure_performance()
    async def process_image(self,
                          image_data: Union[str, np.ndarray],
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process image for face detection and recognition
        
        Args:
            image_data: Image as base64 string or numpy array
            options: Processing options
            
        Returns:
            Dictionary with faces, features and processing time
        """
        try:
            start_time = datetime.utcnow()
            
            # Decode image if needed
            if isinstance(image_data, str):
                image = self._decode_image(image_data)
            else:
                image = image_data
                
            # Detect faces
            faces = await self.detect_faces(image)
            
            # Process each face
            for face in faces:
                features = await self.process_face(face.face_image)
                if features:
                    face.features = features
                    
            # Update statistics
            self._stats['total_processed'] += 1
            self._stats['faces_processed'] += len(faces)
            self._stats['processing_time'] = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'faces': faces,
                'processing_time': self._stats['processing_time']
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise

    async def process_face(self, face_img: np.ndarray) -> Optional[FaceFeatures]:
        """Process face and extract features"""
        try:
            # Preprocess image
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                return None
            
            # Extract features
            with torch.no_grad():
                embedding = self._encoder(face_tensor)
                landmarks = self._landmark_detector(face_tensor)
                
                # Convert to numpy
                embedding = embedding.cpu().numpy()
                landmarks = landmarks.cpu().numpy()
            
            # Estimate pose
            pose = await self._estimate_pose(landmarks)
            
            # Analyze face quality
            quality = await self._analyze_quality(face_img, landmarks)
            
            # Get attributes
            attributes = await self._analyze_attributes(face_tensor)
            
            # Create feature object
            features = FaceFeatures(
                embedding=embedding,
                landmarks=landmarks,
                quality=quality,
                pose=pose,
                expression=attributes.get('expression', 'unknown'),
                age=attributes.get('age'),
                gender=attributes.get('gender')
            )
            
            # Update statistics
            self._update_stats(quality)
            
            return features
            
        except Exception as e:
            logger.error(f"Face processing failed: {str(e)}")
            return None

    def _decode_image(self, image_data: str) -> np.ndarray:
        """Decode base64 image to numpy array"""
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
            logger.error(f"Image decoding failed: {str(e)}")
            raise

    @handle_exceptions(logger_func=logger.error)
    @measure_performance()
    async def detect_faces(self, 
                         frames: Union[np.ndarray, List[np.ndarray]],
                         options: Optional[Dict[str, Any]] = None) -> List[FaceDetection]:
        """
        Detect faces in one or more frames with optimized batch processing and distance estimation
        """
        if isinstance(frames, np.ndarray):
            frames = [frames]
            
        detections = []
        min_confidence = options.get('min_confidence', 
                                   self.config.face_detection_min_confidence)
        
        # Process frames in batches
        for batch_idx in range(0, len(frames), self._batch_size):
            batch_frames = frames[batch_idx:batch_idx + self._batch_size]
            
            if isinstance(self._detector, torch.nn.Module):
                # GPU detection
                batch_tensors = [self._preprocess_image(frame) for frame in batch_frames]
                batch_tensor = torch.cat(batch_tensors, dim=0)
                
                with torch.no_grad():
                    batch_detections = self._detector(batch_tensor)
                    
                for idx, (frame, dets) in enumerate(zip(batch_frames, batch_detections)):
                    frame_dets = self._process_detections(dets, frame.shape)
                    for det in frame_dets:
                        if det["confidence"] > min_confidence:
                            x1, y1, x2, y2 = det["bbox"]
                            face_width = x2 - x1
                            distance = self._estimate_distance(face_width)
                            
                            face_image = frame[y1:y2, x1:x2]
                            detections.append(FaceDetection(
                                bbox=(x1, y1, x2-x1, y2-y1),
                                confidence=det["confidence"],
                                frame_index=batch_idx + idx,
                                face_image=face_image,
                                landmarks=det.get("landmarks"),
                                distance=distance
                            ))
            else:
                # CPU detection
                batch_grays = [cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
                             for frame in batch_frames]
                
                for idx, (frame, gray) in enumerate(zip(batch_frames, batch_grays)):
                    faces = self._detector.detectMultiScale(
                        gray,
                        scaleFactor=self._scale_factor,
                        minNeighbors=5,
                        minSize=self._min_face_size
                    )
                    
                    for (x, y, w, h) in faces:
                        face_image = frame[y:y+h, x:x+w]
                        confidence = self._compute_detection_confidence(face_image)
                        
                        if confidence > min_confidence:
                            distance = self._estimate_distance(w)
                            detections.append(FaceDetection(
                                bbox=(x, y, w, h),
                                confidence=confidence,
                                frame_index=batch_idx + idx,
                                face_image=face_image,
                                distance=distance
                            ))
                    
        logger.info(f"Detected {len(detections)} faces in {len(frames)} frames")
        return detections

    def _process_detections(self,
                          detections: torch.Tensor,
                          image_shape: Tuple[int, int, int]) -> List[Dict[str, Any]]:
        """Process raw detections into face information"""
        faces = []
        height, width = image_shape[:2]
        
        # Convert detections to face information
        for detection in detections[0]:
            confidence = float(detection[4])
            if confidence < self.config.face_detection_min_confidence:
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

    @lru_cache(maxsize=1000)
    def _compute_detection_confidence(self, face_image: np.ndarray) -> float:
        """Compute confidence score for detected face"""
        try:
            # Convert image to tensor
            face_tensor = self._preprocess_image(face_image)
            
            # Use model confidence if available
            if hasattr(self._encoder, 'get_confidence'):
                with torch.no_grad():
                    confidence = self._encoder.get_confidence(face_tensor)
                return float(confidence)
                
            # Fallback to basic metric
            return 0.95
            
        except Exception as e:
            logger.error(f"Error computing detection confidence: {e}")
            return 0.0

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
            
            return face_tensor.to(self.device)
            
        except Exception as e:
            logger.error(f"Face preprocessing failed: {str(e)}")
            return None

    async def _estimate_pose(self, landmarks: np.ndarray) -> Tuple[float, float, float]:
        """Estimate face pose from landmarks"""
        try:
            # Convert landmarks to 3D points
            model_points = self._get_3d_model_points()
            camera_matrix = self._get_camera_matrix()
            
            # Solve PnP
            success, rotation_vec, translation_vec = cv2.solvePnP(
                model_points,
                landmarks,
                camera_matrix,
                None
            )
            
            if not success:
                return (0.0, 0.0, 0.0)
            
            # Convert rotation vector to Euler angles
            rotation_mat, _ = cv2.Rodrigues(rotation_vec)
            pose_mat = cv2.hconcat([rotation_mat, translation_vec])
            _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
            
            return tuple(euler_angles.flatten())
            
        except Exception as e:
            logger.error(f"Pose estimation failed: {str(e)}")
            return (0.0, 0.0, 0.0)

    def _get_3d_model_points(self) -> np.ndarray:
        """Get 3D facial landmark model points"""
        return np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ])

    def _get_camera_matrix(self) -> np.ndarray:
        """Get camera calibration matrix"""
        size = self._face_size
        center = size / 2
        focal_length = center / np.tan(60/2 * np.pi / 180)
        
        return np.array([
            [focal_length, 0, center],
            [0, focal_length, center],
            [0, 0, 1]
        ], dtype=np.float32)

    async def _analyze_quality(self,
                             face_img: np.ndarray,
                             landmarks: np.ndarray) -> float:
        """Analyze face quality"""
        try:
            # Check face size
            height, width = face_img.shape[:2]
            if height < 64 or width < 64:
                return 0.0
            
            # Calculate sharpness
            laplacian = cv2.Laplacian(face_img, cv2.CV_64F)
            sharpness = np.var(laplacian)
            
            # Calculate brightness and contrast
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Check landmark confidence
            landmark_confidence = np.mean(landmarks[:, 2])
            
            # Calculate overall quality score
            quality_score = np.mean([
                sharpness / 1000,  # Normalize sharpness
                brightness / 255,   # Normalize brightness
                contrast / 128,     # Normalize contrast
                landmark_confidence
            ])
            
            return float(np.clip(quality_score, 0.0, 1.0))
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {str(e)}")
            return 0.0

    async def _analyze_attributes(self, face_tensor: torch.Tensor) -> Dict:
        """Analyze facial attributes"""
        try:
            with torch.no_grad():
                attributes = self._attribute_analyzer(face_tensor)
            
            # Process attributes
            results = {
                'expression': self._get_expression(attributes),
                'age': self._estimate_age(attributes),
                'gender': self._detect_gender(attributes)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Attribute analysis failed: {str(e)}")
            return {}

    def _get_expression(self, attributes: torch.Tensor) -> str:
        """Get facial expression from attributes"""
        expressions = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'fearful', 'disgusted']
        idx = torch.argmax(attributes[:7]).item()
        return expressions[idx]

    def _estimate_age(self, attributes: torch.Tensor) -> Optional[float]:
        """Estimate age from attributes"""
        try:
            age = attributes[7].item() * 100  # Scale to years
            return float(np.clip(age, 0, 100))
        except:
            return None

    def _detect_gender(self, attributes: torch.Tensor) -> Optional[str]:
        """Detect gender from attributes"""
        try:
            return 'male' if attributes[8].item() > 0.5 else 'female'
        except:
            return None

    def _update_stats(self, quality: float) -> None:
        """Update processing statistics"""
        self._stats['faces_processed'] += 1
        self._stats['features_extracted'] += 1
        
        # Update average quality
        n = self._stats['faces_processed']
        current_avg = self._stats['average_quality']
        self._stats['average_quality'] = (current_avg * (n - 1) + quality) / n

    @handle_exceptions(logger_func=logger.error)
    @measure_performance()
    async def encode_faces(self, detections: List[FaceDetection]) -> List[np.ndarray]:
        """Generate encodings for detected faces with optimized GPU acceleration"""
        encodings = []
        batch_tensors = []
        cached_indices = []
        
        # Process cache hits first
        for idx, detection in enumerate(detections):
            cache_key = hash(detection.face_image.tobytes())
            if cache_key in self._encoding_cache:
                encodings.append(self._encoding_cache[cache_key])
                cached_indices.append(idx)
                continue
            # Preprocess for model
            face_tensor = self._preprocess_face(detection.face_image)
            if face_tensor is not None:
                batch_tensors.append(face_tensor)
        
        # Process remaining faces in optimized batches
        if batch_tensors:
            try:
                with torch.cuda.amp.autocast(enabled=self.use_amp):
                    # Stack tensors for batch processing
                    batch = torch.cat(batch_tensors).to(self.device)
                    
                    # Process in sub-batches if needed
                    for i in range(0, len(batch), self._batch_size):
                        sub_batch = batch[i:i + self._batch_size]
                        with torch.no_grad():
                            features = self._encoder(sub_batch)
                            # Move to CPU and convert to numpy
                            features = features.cpu().numpy()
                            encodings.extend(features)
                            
                            # Update cache
                            for feat, det_idx in zip(features, range(i, min(i + self._batch_size, len(batch)))):
                                if det_idx not in cached_indices:
                                    cache_key = hash(detections[det_idx].face_image.tobytes())
                                    self._encoding_cache[cache_key] = feat
            
            except RuntimeError as e:
                if "out of memory" in str(e):
                    # Clear cache and retry with smaller batch
                    torch.cuda.empty_cache()
                    self._batch_size = max(1, self._batch_size // 2)
                    logger.warning(f"Reduced batch size to {self._batch_size} due to OOM")
                    return await self.encode_faces(detections)
                raise
        
        return encodings

    @handle_exceptions(logger_func=logger.error)
    @measure_performance()
    async def find_matches(self, encoding: np.ndarray) -> List[FaceMatch]:
        """
        Find matches for a face encoding with optimized similarity search
        
        Args:
            encoding: Face encoding to match
            
        Returns:
            List of FaceMatch objects sorted by confidence
        """
        async with self.db_pool.get_connection() as conn:
            # Get stored encodings with optimized query
            stored_faces = await conn.fetch(
                """
                SELECT user_id, encoding, metadata
                FROM face_encodings
                WHERE active = true
                """
            )
            
            matches = []
            for face in stored_faces:
                # Calculate similarity
                similarity = 1 - np.linalg.norm(encoding - np.array(face['encoding']))
                
                if similarity > self.matching_threshold:
                    matches.append(FaceMatch(
                        user_id=face['user_id'],
                        confidence=float(similarity),
                        metadata=face['metadata']
                    ))
            
            # Sort by confidence
            matches.sort(key=lambda x: x.confidence, reverse=True)
            return matches

    @handle_exceptions(logger_func=logger.error)
    @measure_performance()
    async def verify_face(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Complete face verification pipeline with distance-based activation
        
        Args:
            frame: Image frame containing face
            
        Returns:
            Dict with match and activation status if verified, None otherwise
        """
        # Detect face
        detections = await self.detect_faces(frame)
        if not detections:
            await self.event_manager.publish('face_not_detected', {'frame': frame})
            return None
            
        # Use best detection
        best_detection = max(detections, key=lambda d: d.confidence)
        
        # Generate encoding
        encodings = await self.encode_faces([best_detection])
        if not encodings:
            await self.event_manager.publish('face_encoding_failed', 
                                          {'detection': best_detection})
            return None
            
        # Find matches
        matches = await self.find_matches(encodings[0])
        
        if matches:
            best_match = matches[0]
            distance = best_detection.distance

            # Determine activation status based on distance
            can_activate = (distance is not None and 
                          distance <= self._activation_range)
            
            # Add detection info to match result
            result = {
                'match': best_match,
                'distance': distance,
                'can_activate': can_activate,
                'bbox': best_detection.bbox
            }
            
            # Publish appropriate event based on distance
            if distance <= self._activation_range:
                await self.event_manager.publish('face_verified_activation_range', result)
            elif distance <= self._long_range_threshold:
                await self.event_manager.publish('face_verified_long_range', result)
            else:
                await self.event_manager.publish('face_verified_out_of_range', result)
            
            return result
            
        await self.event_manager.publish('face_unverified', 
                                       {'encoding': encodings[0]})
        return None

    def clear_caches(self) -> None:
        """Clear all internal caches"""
        self._encoding_cache.clear()
        self._compute_detection_confidence.cache_clear()

    def _estimate_distance(self, face_width_pixels: float) -> float:
        """
        Estimate distance to face using known face width and focal length
        Uses the formula: Distance = (Known Width × Focal Length) / Pixel Width
        """
        try:
            distance = (self._avg_face_width * self._focal_length) / face_width_pixels
            return float(distance)
        except (ZeroDivisionError, ValueError):
            return float('inf')

    def _load_tts_responses(self):
        """Load TTS response templates from configuration."""
        try:
            tts_config_path = self.config.tts_responses_path
            with open(tts_config_path, 'r') as file:
                self.tts_responses = json.load(file)
        except Exception as e:
            logger.error(f"Error loading TTS responses: {e}")

def play_response(event):
    tts_config_path = settings.tts_responses_path
    with open(tts_config_path, 'r') as file:
        responses = json.load(file)

    response = responses.get(event)

    if response:
        tts = gTTS(text=response, lang='en')
        tts.save('response.mp3')
        os.system('mpg123 response.mp3')

# Global face recognition system instance
face_recognition_system = FaceRecognitionSystem() 