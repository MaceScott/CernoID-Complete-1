from typing import List, Dict, Optional
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import cv2
from core.error_handling import handle_exceptions

class OptimizedFaceProcessor:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.recognition_model = self._load_recognition_model()
        self.encoding_cache = LRUCache(maxsize=1000)
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
    @handle_exceptions(logger=recognition_logger.error)
    async def process_frame(self, frame: np.ndarray) -> List[Dict]:
        # Convert to grayscale for faster processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using GPU acceleration if available
        faces = await self._detect_faces_gpu(gray)
        
        # Process detected faces in parallel
        face_data = []
        futures = []
        
        for face in faces:
            future = self.thread_pool.submit(
                self._process_single_face,
                frame[face[1]:face[1]+face[3], face[0]:face[0]+face[2]]
            )
            futures.append(future)
            
        # Collect results
        for future in futures:
            result = future.result()
            if result:
                face_data.append(result)
                
        return face_data

    async def _detect_faces_gpu(self, gray_frame: np.ndarray) -> List[tuple]:
        try:
            # Try using GPU acceleration
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                gpu_frame = cv2.cuda_GpuMat()
                gpu_frame.upload(gray_frame)
                
                gpu_cascade = cv2.cuda.CascadeClassifier_create(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                
                faces = gpu_cascade.detectMultiScale(gpu_frame)
                return faces.download()
        except:
            # Fall back to CPU if GPU fails
            faces = self.face_cascade.detectMultiScale(
                gray_frame,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            return faces

    def _process_single_face(self, face_img: np.ndarray) -> Optional[Dict]:
        # Generate face encoding
        encoding = self._generate_encoding(face_img)
        
        # Check cache first
        cache_key = self._generate_cache_key(encoding)
        if cache_key in self.encoding_cache:
            return self.encoding_cache[cache_key]
            
        # Compare with database
        match = self._find_match(encoding)
        
        if match:
            result = {
                'match': match,
                'confidence': match['confidence'],
                'encoding': encoding
            }
            self.encoding_cache[cache_key] = result
            return result
            
        return None 
