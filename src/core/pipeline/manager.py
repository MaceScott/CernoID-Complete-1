from typing import Dict, List, Optional, Union
import asyncio
import numpy as np
from datetime import datetime
import cv2
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import torch

from ..base import BaseComponent
from ..utils.errors import PipelineError

class ProcessingPipeline(BaseComponent):
    """Real-time facial recognition processing pipeline"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Processing settings
        self._batch_size = config.get('pipeline.batch_size', 4)
        self._max_queue_size = config.get('pipeline.queue_size', 100)
        self._use_gpu = config.get('pipeline.use_gpu', True) and torch.cuda.is_available()
        
        # Initialize queues
        self._frame_queue = Queue(maxsize=self._max_queue_size)
        self._result_queue = Queue(maxsize=self._max_queue_size)
        
        # Processing pools
        self._thread_pool = ThreadPoolExecutor(
            max_workers=config.get('pipeline.workers', 4),
            thread_name_prefix='pipeline'
        )
        
        # Pipeline state
        self._running = False
        self._current_batch: List = []
        self._processing_times: Dict[str, List[float]] = {
            'preprocess': [],
            'detection': [],
            'recognition': [],
            'total': []
        }
        
        # Performance monitoring
        self._stats = {
            'frames_processed': 0,
            'faces_detected': 0,
            'matches_found': 0,
            'average_latency': 0.0,
            'dropped_frames': 0
        }

    async def start(self) -> None:
        """Start processing pipeline"""
        try:
            if self._running:
                return
                
            self._running = True
            
            # Start processing workers
            asyncio.create_task(self._frame_processor())
            asyncio.create_task(self._result_processor())
            
            self.logger.info("Processing pipeline started")
            
        except Exception as e:
            raise PipelineError(f"Failed to start pipeline: {str(e)}")

    async def stop(self) -> None:
        """Stop processing pipeline"""
        try:
            self._running = False
            
            # Clear queues
            while not self._frame_queue.empty():
                self._frame_queue.get_nowait()
            while not self._result_queue.empty():
                self._result_queue.get_nowait()
                
            # Shutdown thread pool
            self._thread_pool.shutdown(wait=True)
            
            self.logger.info("Processing pipeline stopped")
            
        except Exception as e:
            self.logger.error(f"Pipeline shutdown error: {str(e)}")

    async def process_frame(self, frame: np.ndarray, camera_id: str) -> None:
        """Add frame to processing queue"""
        try:
            if self._frame_queue.qsize() >= self._max_queue_size:
                self._stats['dropped_frames'] += 1
                return
                
            frame_data = {
                'frame': frame,
                'camera_id': camera_id,
                'timestamp': datetime.utcnow().timestamp()
            }
            
            self._frame_queue.put(frame_data)
            
        except Exception as e:
            self.logger.error(f"Frame queueing error: {str(e)}")

    async def _frame_processor(self) -> None:
        """Process frames from queue"""
        while self._running:
            try:
                # Collect batch of frames
                batch = []
                while len(batch) < self._batch_size:
                    try:
                        frame_data = self._frame_queue.get_nowait()
                        batch.append(frame_data)
                    except:
                        break
                        
                if not batch:
                    await asyncio.sleep(0.01)
                    continue
                
                # Process batch
                start_time = datetime.utcnow().timestamp()
                
                # Preprocess frames
                preprocessed = await self._preprocess_batch(batch)
                
                # Detect faces
                detections = await self._detect_faces(preprocessed)
                
                # Recognize faces
                results = await self._recognize_faces(detections)
                
                # Calculate processing time
                process_time = datetime.utcnow().timestamp() - start_time
                self._update_timing_stats('total', process_time)
                
                # Queue results
                for result in results:
                    self._result_queue.put(result)
                
                # Update statistics
                self._stats['frames_processed'] += len(batch)
                
            except Exception as e:
                self.logger.error(f"Frame processing error: {str(e)}")
                await asyncio.sleep(0.1)

    async def _preprocess_batch(self, batch: List[Dict]) -> List[np.ndarray]:
        """Preprocess batch of frames"""
        try:
            start_time = datetime.utcnow().timestamp()
            
            processed = []
            for frame_data in batch:
                frame = frame_data['frame']
                
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
                
                processed.append(frame)
            
            process_time = datetime.utcnow().timestamp() - start_time
            self._update_timing_stats('preprocess', process_time)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Preprocessing error: {str(e)}")
            return []

    async def _detect_faces(self, frames: List[np.ndarray]) -> List[Dict]:
        """Detect faces in preprocessed frames"""
        try:
            start_time = datetime.utcnow().timestamp()
            
            detections = []
            for frame in frames:
                faces = await self.app.recognition.detect_faces(frame)
                detections.append({
                    'frame': frame,
                    'faces': faces
                })
                self._stats['faces_detected'] += len(faces)
            
            process_time = datetime.utcnow().timestamp() - start_time
            self._update_timing_stats('detection', process_time)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Face detection error: {str(e)}")
            return []

    async def _recognize_faces(self, detections: List[Dict]) -> List[Dict]:
        """Recognize detected faces"""
        try:
            start_time = datetime.utcnow().timestamp()
            
            results = []
            for detection in detections:
                frame = detection['frame']
                faces = detection['faces']
                
                for face in faces:
                    # Extract features
                    encoding = await self.app.recognition.encode_face(face, frame)
                    
                    # Find matches
                    matches = await self.app.recognition.matcher.find_matches(
                        encoding,
                        max_matches=1
                    )
                    
                    if matches:
                        self._stats['matches_found'] += 1
                        
                    results.append({
                        'frame': frame,
                        'face': face,
                        'matches': matches,
                        'timestamp': datetime.utcnow().timestamp()
                    })
            
            process_time = datetime.utcnow().timestamp() - start_time
            self._update_timing_stats('recognition', process_time)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Face recognition error: {str(e)}")
            return []

    def _update_timing_stats(self, stage: str, time: float) -> None:
        """Update processing timing statistics"""
        self._processing_times[stage].append(time)
        if len(self._processing_times[stage]) > 100:
            self._processing_times[stage].pop(0)
            
        if stage == 'total':
            self._stats['average_latency'] = np.mean(
                self._processing_times['total']
            )

    async def get_stats(self) -> Dict:
        """Get pipeline statistics"""
        stats = self._stats.copy()
        
        # Add timing stats
        for stage, times in self._processing_times.items():
            if times:
                stats[f'avg_{stage}_time'] = np.mean(times)
            else:
                stats[f'avg_{stage}_time'] = 0.0
                
        return stats 