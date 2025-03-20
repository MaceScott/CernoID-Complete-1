"""
File: core.py
Purpose: Provides a unified face recognition system with GPU support and optimized performance.

Key Features:
- Face detection and recognition
- Face feature extraction
- Face matching and verification
- Quality assessment
- Pose estimation
- Attribute analysis (age, gender, expression)
- Distance estimation
- GPU acceleration
- Caching and performance optimization

Dependencies:
- OpenCV: Image processing
- dlib: Face detection and recognition
- PyTorch: Deep learning operations
- NumPy: Array operations
- Core services:
  - Event management
  - Error handling
  - Configuration
  - Database
  - Monitoring
  - Performance measurement

Configuration:
- Model paths and URLs
- Performance thresholds
- Cache settings
- GPU settings
- Quality thresholds
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
import dlib
import os
import json
import urllib.request

from src.core.events.manager import event_manager
from src.core.error_handling import handle_exceptions
from src.core.config import settings
from src.core.database import db_pool
from src.core.utils.decorators import measure_performance
from src.core.monitoring.service import monitoring_service
from gtts import gTTS
from ..base import BaseComponent
from ..utils.errors import handle_errors

# Configure logging
logger = logging.getLogger(__name__)

# Model paths and URLs
CASCADE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'haarcascade_frontalface_default.xml')
DLIB_FACE_RECOGNITION_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'data', 'dlib_face_recognition_resnet_model_v1.dat')
DLIB_SHAPE_PREDICTOR_PATH = os.path.join(os.path.dirname(__file__), 'data', 'shape_predictor_68_face_landmarks.dat')

# Model download URLs
DLIB_FACE_RECOGNITION_MODEL_URL = "https://github.com/davisking/dlib-models/raw/master/dlib_face_recognition_resnet_model_v1.dat.bz2"
DLIB_SHAPE_PREDICTOR_URL = "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2"

@dataclass
class FaceFeatures:
    """
    Extracted face features and attributes.
    
    Attributes:
        embedding: Face embedding vector
        landmarks: Facial landmark points
        quality: Face quality score
        pose: Face pose angles (yaw, pitch, roll)
        expression: Detected facial expression
        age: Estimated age
        gender: Detected gender
    """
    embedding: np.ndarray
    landmarks: np.ndarray
    quality: float
    pose: Tuple[float, float, float]  # yaw, pitch, roll
    expression: str
    age: Optional[float]
    gender: Optional[str]

@dataclass
class FaceDetection:
    """
    Face detection result with metadata.
    
    Attributes:
        bbox: Bounding box coordinates
        confidence: Detection confidence score
        frame_index: Frame index in video
        face_image: Cropped face image
        landmarks: Optional facial landmarks
        features: Optional extracted features
        distance: Optional estimated distance
    """
    bbox: tuple[int, int, int, int]
    confidence: float
    frame_index: int
    face_image: np.ndarray
    landmarks: Optional[List[List[int]]] = None
    features: Optional[FaceFeatures] = None
    distance: Optional[float] = None  # Distance in meters

@dataclass
class FaceMatch:
    """
    Face matching result with confidence score.
    
    Attributes:
        user_id: Matched user ID
        confidence: Match confidence score
        metadata: Optional additional metadata
    """
    user_id: str
    confidence: float
    metadata: Optional[Dict] = None

class FaceRecognitionSystem(BaseComponent):
    """
    Unified face recognition system with GPU support.
    
    Features:
    - Face detection and recognition
    - Feature extraction and matching
    - Quality assessment
    - Performance optimization
    - GPU acceleration
    - Caching
    """
    
    def __init__(self, config: Dict[str, Any], database_url: str):
        """
        Initialize face recognition system.
        Sets up configuration, services, and GPU settings.
        """
        super().__init__(config)
        self.database = FaceDatabase(database_url)
        self._encoding_cache = TTLCache(
            maxsize=self.config.FACE_RECOGNITION_CACHE_SIZE,
            ttl=self.config.FACE_RECOGNITION_CACHE_TTL
        )
        self.is_initialized = False
        self._initializing = False
        
        # GPU configuration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

    @handle_errors
    async def initialize(self) -> None:
        """
        Initialize the face recognition system.
        
        Steps:
        1. Create data directory
        2. Download and prepare models
        3. Initialize components (detector, encoder, landmark detector)
        4. Set up caching and performance settings
        5. Initialize monitoring and statistics
        
        Raises:
            Exception: If initialization fails
        """
        if self.is_initialized:
            logger.info("Face recognition system already initialized")
            return
            
        if self._initializing:
            logger.info("Face recognition system initialization already in progress")
            return
            
        self._initializing = True
        
        try:
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Download and prepare models
            await self._download_and_prepare_models()
            
            # Initialize components
            self._detector = await self._init_detector()
            self._encoder = await self._init_encoder()
            self._landmark_detector = await self._init_landmark_detector()
            
            # Batch size for CPU
            self._batch_size = 4
                
            # Optimize processing settings
            self._face_size = self.config.RECOGNITION_FACE_SIZE
            self._min_quality = self.config.RECOGNITION_MIN_QUALITY
            
            # Cache settings
            self.matching_threshold = self.config.FACE_RECOGNITION_MATCHING_THRESHOLD
            
            # Performance settings
            self._min_face_size = self.config.FACE_RECOGNITION_MIN_FACE_SIZE
            self._scale_factor = self.config.FACE_RECOGNITION_SCALE_FACTOR
            
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
            self._focal_length = self.config.RECOGNITION_FOCAL_LENGTH
            self._avg_face_width = self.config.RECOGNITION_AVG_FACE_WIDTH
            self._activation_range = self.config.RECOGNITION_ACTIVATION_RANGE
            self._long_range_threshold = self.config.RECOGNITION_LONG_RANGE_THRESHOLD
            
            # Initialize face recognition model
            self.model = await self._load_model()
            
            self.is_initialized = True
            logger.info("Face recognition system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize face recognition system: {e}")
            raise
        finally:
            self._initializing = False

    @handle_errors
    async def cleanup(self) -> None:
        """
        Cleanup face recognition system resources.
        
        Steps:
        1. Clear caches
        2. Clear processing queue
        3. Release GPU memory
        4. Reset initialization state
        
        Raises:
            Exception: If cleanup fails
        """
        if not self.is_initialized:
            logger.info("Face recognition system not initialized, nothing to clean up")
            return
            
        try:
            # Clear caches
            if hasattr(self, '_encoding_cache'):
                self._encoding_cache.clear()
            
            # Clear processing queue
            if hasattr(self, '_processing_queue'):
                while not self._processing_queue.empty():
                    try:
                        self._processing_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
            
            # Release GPU memory if using CUDA
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            self.is_initialized = False
            logger.info("Face recognition system cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up face recognition system: {e}")
            raise

    async def _download_and_prepare_models(self):
        """
        Download and prepare required models if they don't exist.
        
        Downloads:
        - Cascade classifier
        - dlib face recognition model
        - Shape predictor model
        
        Raises:
            Exception: If model download or preparation fails
        """
        try:
            # Download cascade classifier if it doesn't exist
            if not os.path.exists(CASCADE_PATH):
                url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
                urllib.request.urlretrieve(url, CASCADE_PATH)
                logger.info(f"Downloaded cascade classifier to {CASCADE_PATH}")
            
            # Download and extract dlib face recognition model if it doesn't exist
            if not os.path.exists(DLIB_FACE_RECOGNITION_MODEL_PATH):
                import bz2
                import shutil
                
                # Download compressed file
                compressed_path = DLIB_FACE_RECOGNITION_MODEL_PATH + '.bz2'
                urllib.request.urlretrieve(DLIB_FACE_RECOGNITION_MODEL_URL, compressed_path)
                
                # Extract the file
                with bz2.BZ2File(compressed_path, 'rb') as source, open(DLIB_FACE_RECOGNITION_MODEL_PATH, 'wb') as dest:
                    shutil.copyfileobj(source, dest)
                
                # Remove compressed file
                os.remove(compressed_path)
                logger.info(f"Downloaded and extracted face recognition model to {DLIB_FACE_RECOGNITION_MODEL_PATH}")
            
            # Download and extract shape predictor model if it doesn't exist
            if not os.path.exists(DLIB_SHAPE_PREDICTOR_PATH):
                import bz2
                import shutil
                
                # Download compressed file
                compressed_path = DLIB_SHAPE_PREDICTOR_PATH + '.bz2'
                urllib.request.urlretrieve(DLIB_SHAPE_PREDICTOR_URL, compressed_path)
                
                # Extract the file
                with bz2.BZ2File(compressed_path, 'rb') as source, open(DLIB_SHAPE_PREDICTOR_PATH, 'wb') as dest:
                    shutil.copyfileobj(source, dest)
                
                # Remove compressed file
                os.remove(compressed_path)
                logger.info(f"Downloaded and extracted shape predictor model to {DLIB_SHAPE_PREDICTOR_PATH}")
                
        except Exception as e:
            logger.error(f"Error downloading models: {e}")
            raise

    async def _init_detector(self) -> cv2.CascadeClassifier:
        """
        Initialize face detector.
        
        Returns:
            cv2.CascadeClassifier: Initialized face detector
        """
        try:
            detector = cv2.CascadeClassifier(CASCADE_PATH)
            if detector.empty():
                raise ValueError(f"Failed to load cascade classifier from {CASCADE_PATH}")
            return detector
        except Exception as e:
            logger.error(f"Error initializing face detector: {e}")
            raise

    async def _init_encoder(self) -> 'dlib.face_recognition_model_v1':
        """
        Initialize face encoder.
        
        Returns:
            dlib.face_recognition_model_v1: Initialized face encoder
        """
        try:
            return dlib.face_recognition_model_v1(DLIB_FACE_RECOGNITION_MODEL_PATH)
        except Exception as e:
            logger.error(f"Error initializing face encoder: {e}")
            raise

    async def _init_landmark_detector(self) -> 'dlib.shape_predictor':
        """
        Initialize facial landmark detector.
        
        Returns:
            dlib.shape_predictor: Initialized landmark detector
        """
        try:
            return dlib.shape_predictor(DLIB_SHAPE_PREDICTOR_PATH)
        except Exception as e:
            logger.error(f"Failed to load landmark model: {str(e)}")
            raise

    async def _load_model(self):
        """
        Load face recognition model.
        
        Returns:
            Loaded model instance
        """
        # TODO: Implement model loading
        pass

    @handle_errors
    @measure_performance()
    async def process_image(self,
                          image_data: Union[str, np.ndarray],
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process an image for face detection and recognition.
        
        Args:
            image_data: Image data (base64 string or numpy array)
            options: Optional processing options
            
        Returns:
            Dict containing processing results
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
        """
        Process a single face image to extract features.
        
        Args:
            face_img: Face image array
            
        Returns:
            Optional[FaceFeatures]: Extracted face features
        """
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
        """
        Decode base64 image data to numpy array.
        
        Args:
            image_data: Base64 encoded image string
            
        Returns:
            np.ndarray: Decoded image array
        """
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

    @handle_errors
    @measure_performance()
    async def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect faces in an image.
        
        Args:
            image: Input image array
            
        Returns:
            List of face detection results
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self._detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Convert to list of face objects
        face_list = []
        for (x, y, w, h) in faces:
            face_list.append({
                'bbox': (x, y, w, h),
                'confidence': None  # Haar cascade doesn't provide confidence
            })
            
        return face_list

    @handle_errors
    @measure_performance()
    async def get_face_encoding(self, image: np.ndarray, face_bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Get face encoding for a detected face.
        
        Args:
            image: Input image array
            face_bbox: Face bounding box coordinates
            
        Returns:
            np.ndarray: Face encoding vector
        """
        try:
            # Extract face region
            x, y, w, h = face_bbox
            face_img = image[y:y+h, x:x+w]
            
            # Preprocess face image
            face_tensor = self._preprocess_face(face_img)
            if face_tensor is None:
                raise ValueError("Failed to preprocess face image")
            
            # Generate embedding
            with torch.no_grad():
                embedding = self._encoder(face_tensor)
                embedding = embedding.cpu().numpy()
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Face encoding failed: {str(e)}")
            raise

    @handle_errors
    @measure_performance()
    async def verify_face(self, image: np.ndarray, username: str) -> Optional[Dict[str, Any]]:
        """
        Verify a face against a stored template.
        
        Args:
            image: Input face image
            username: Username to verify against
            
        Returns:
            Optional[Dict]: Verification result with confidence
        """
        try:
            # Detect faces
            faces = await self.detect_faces(image)
            if not faces:
                return None
            
            # Get encoding for largest face
            largest_face = max(faces, key=lambda f: f['bbox'][2] * f['bbox'][3])
            encoding = await self.get_face_encoding(image, largest_face['bbox'])
            
            # Get stored encodings
            stored_encodings = self.database.get_user_encodings(username)
            if not stored_encodings:
                return None
            
            # Compare with all stored encodings
            similarities = [
                self._compare_encodings(encoding, stored_encoding)
                for stored_encoding in stored_encodings
            ]
            
            # Get best match
            best_similarity = max(similarities)
            
            return {
                'match': best_similarity > 0.9,
                'confidence': float(best_similarity),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Face verification failed: {e}")
            return None

    @handle_errors
    @measure_performance()
    async def register_face(self, image: np.ndarray, user_id: int) -> bool:
        """
        Register a new face template.
        
        Args:
            image: Face image to register
            user_id: User ID to associate with face
            
        Returns:
            bool: Success status
        """
        try:
            # Detect faces
            faces = await self.detect_faces(image)
            if not faces:
                return False
            
            # Get encoding for largest face
            largest_face = max(faces, key=lambda f: f['bbox'][2] * f['bbox'][3])
            encoding = await self.get_face_encoding(image, largest_face['bbox'])
            
            # Assess quality
            quality_score = await self._analyze_quality(
                image[largest_face['bbox'][1]:largest_face['bbox'][1]+largest_face['bbox'][3],
                      largest_face['bbox'][0]:largest_face['bbox'][0]+largest_face['bbox'][2]],
                None  # No landmarks needed for quality check
            )
            
            # Store encoding in database
            success = self.database.store_encoding(user_id, encoding, quality_score)
            if success:
                # Update cache
                self._encoding_cache[user_id] = encoding
            
            return success
            
        except Exception as e:
            logger.error(f"Face registration failed: {e}")
            return False

    def _compare_encodings(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """
        Compare two face encodings.
        
        Args:
            encoding1: First face encoding
            encoding2: Second face encoding
            
        Returns:
            float: Similarity score
        """
        try:
            # Ensure encodings are normalized
            encoding1 = encoding1 / np.linalg.norm(encoding1)
            encoding2 = encoding2 / np.linalg.norm(encoding2)
            
            # Calculate cosine similarity
            similarity = np.dot(encoding1, encoding2)
            
            # Convert to distance metric (0 = same person, 1 = different person)
            distance = 1 - similarity
            
            # Apply sigmoid function to get probability
            probability = 1 / (1 + np.exp(-10 * (0.5 - distance)))
            
            return float(probability)
            
        except Exception as e:
            logger.error(f"Encoding comparison failed: {str(e)}")
            return 0.0

    def _preprocess_face(self, face_img: np.ndarray) -> Optional[torch.Tensor]:
        """
        Preprocess face image for feature extraction.
        
        Args:
            face_img: Input face image
            
        Returns:
            Optional[torch.Tensor]: Preprocessed face tensor
        """
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
        """
        Estimate face pose from landmarks.
        
        Args:
            landmarks: Facial landmark points
            
        Returns:
            Tuple[float, float, float]: Pose angles (yaw, pitch, roll)
        """
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
        """
        Get 3D model points for pose estimation.
        
        Returns:
            np.ndarray: 3D model points
        """
        return np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ])

    def _get_camera_matrix(self) -> np.ndarray:
        """
        Get camera matrix for pose estimation.
        
        Returns:
            np.ndarray: Camera matrix
        """
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
        """
        Analyze face image quality.
        
        Args:
            face_img: Face image
            landmarks: Facial landmarks
            
        Returns:
            float: Quality score
        """
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
        """
        Analyze face attributes (age, gender, expression).
        
        Args:
            face_tensor: Preprocessed face tensor
            
        Returns:
            Dict: Analyzed attributes
        """
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
        """
        Get facial expression from attributes.
        
        Args:
            attributes: Face attributes tensor
            
        Returns:
            str: Detected expression
        """
        expressions = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'fearful', 'disgusted']
        idx = torch.argmax(attributes[:7]).item()
        return expressions[idx]

    def _estimate_age(self, attributes: torch.Tensor) -> Optional[float]:
        """
        Estimate age from face attributes.
        
        Args:
            attributes: Face attributes tensor
            
        Returns:
            Optional[float]: Estimated age
        """
        try:
            age = attributes[7].item() * 100  # Scale to years
            return float(np.clip(age, 0, 100))
        except:
            return None

    def _detect_gender(self, attributes: torch.Tensor) -> Optional[str]:
        """
        Detect gender from face attributes.
        
        Args:
            attributes: Face attributes tensor
            
        Returns:
            Optional[str]: Detected gender
        """
        try:
            return 'male' if attributes[8].item() > 0.5 else 'female'
        except:
            return None

    def _update_stats(self, quality: float) -> None:
        """
        Update system statistics.
        
        Args:
            quality: Face quality score
        """
        self._stats['faces_processed'] += 1
        self._stats['features_extracted'] += 1
        
        # Update average quality
        n = self._stats['faces_processed']
        current_avg = self._stats['average_quality']
        self._stats['average_quality'] = (current_avg * (n - 1) + quality) / n

    @handle_errors
    @measure_performance()
    async def encode_faces(self, detections: List[FaceDetection]) -> List[np.ndarray]:
        """
        Encode multiple detected faces.
        
        Args:
            detections: List of face detections
            
        Returns:
            List[np.ndarray]: Face encodings
        """
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

    @handle_errors
    @measure_performance()
    async def find_matches(self, encoding: np.ndarray) -> List[FaceMatch]:
        """
        Find matching faces for an encoding.
        
        Args:
            encoding: Face encoding to match
            
        Returns:
            List[FaceMatch]: Matching results
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

    def clear_caches(self) -> None:
        """Clear all system caches."""
        self._encoding_cache.clear()
        self._compute_detection_confidence.cache_clear()

    def _estimate_distance(self, face_width_pixels: float) -> float:
        """
        Estimate face distance from camera.
        
        Args:
            face_width_pixels: Face width in pixels
            
        Returns:
            float: Estimated distance in meters
        """
        try:
            distance = (self._avg_face_width * self._focal_length) / face_width_pixels
            return float(distance)
        except (ZeroDivisionError, ValueError):
            return float('inf')

    def _load_tts_responses(self):
        """Load text-to-speech responses."""
        try:
            tts_config_path = self.config.tts_responses_path
            with open(tts_config_path, 'r') as file:
                self.tts_responses = json.load(file)
        except Exception as e:
            logger.error(f"Error loading TTS responses: {e}")

def play_response(event):
    """Play audio response for an event."""
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