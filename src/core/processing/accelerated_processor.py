from typing import List, Dict, Optional
import numpy as np
import cv2
import cupy as cp
from concurrent.futures import ThreadPoolExecutor
from core.error_handling import handle_exceptions

class AcceleratedProcessor:
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=8)
        self.gpu_enabled = cv2.cuda.getCudaEnabledDeviceCount() > 0
        self.face_cascade_gpu = None
        if self.gpu_enabled:
            self.face_cascade_gpu = cv2.cuda.CascadeClassifier_create(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )

    @handle_exceptions(logger=processor_logger.error)
    async def process_frames(self, frames: List[np.ndarray]) -> List[Dict]:
        if self.gpu_enabled:
            return await self._process_frames_gpu(frames)
        else:
            return await self._process_frames_cpu(frames)

    async def _process_frames_gpu(self, frames: List[np.ndarray]) -> List[Dict]:
        # Convert frames to GPU arrays
        gpu_frames = [cv2.cuda_GpuMat(frame) for frame in frames]
        
        # Process in parallel on GPU
        futures = []
        for gpu_frame in gpu_frames:
            future = self.thread_pool.submit(
                self._detect_faces_gpu,
                gpu_frame
            )
            futures.append(future)
            
        results = []
        for future in futures:
            result = future.result()
            if result:
                results.extend(result)
                
        return results

    def _detect_faces_gpu(self, gpu_frame: cv2.cuda_GpuMat) -> List[Dict]:
        # Convert to grayscale on GPU
        gray_gpu = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using GPU
        faces = self.face_cascade_gpu.detectMultiScale(gray_gpu)
        
        # Process detected faces
        results = []
        for face in faces.download():
            face_data = self._process_face_gpu(gpu_frame, face)
            if face_data:
                results.append(face_data)
                
        return results

    @staticmethod
    def _process_face_gpu(gpu_frame: cv2.cuda_GpuMat, face: tuple) -> Optional[Dict]:
        x, y, w, h = face
        face_roi = gpu_frame[y:y+h, x:x+w]
        
        # Additional GPU-accelerated processing here
        return {
            'bbox': face,
            'confidence': 0.95,
            'features': face_roi.download()
        } 
