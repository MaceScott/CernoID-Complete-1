"""Advanced performance optimization system for face recognition.

This module provides optimization features including:
- TensorRT acceleration
- Model quantization
- Dynamic batching
- Feature caching
- Multi-threaded processing
- Performance monitoring
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import torch
import torch.nn as nn
from torch.cuda.amp import autocast
import numpy as np
from dataclasses import dataclass
import onnx
import tensorrt as trt
import cv2
import asyncio
from datetime import datetime
import threading
from queue import Queue
import psutil
import GPUtil
import logging

from .base import BaseComponent
from .errors import OptimizationError

@dataclass
class OptimizationConfig:
    """Configuration for optimization settings"""
    batch_size: int
    use_amp: bool  # Automatic mixed precision
    num_workers: int
    pin_memory: bool
    
@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    inference_time: float  # milliseconds
    preprocessing_time: float
    postprocessing_time: float
    total_time: float
    batch_size: int
    gpu_utilization: float
    memory_usage: float
    throughput: float  # faces per second
    timestamp: datetime

class FaceRecognitionOptimizer(BaseComponent):
    """Advanced performance optimization system for face recognition"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Optimization settings
        self._enable_tensorrt = config.get('optimization.tensorrt', True)
        self._enable_quantization = config.get('optimization.quantize', True)
        self._enable_batching = config.get('optimization.batching', True)
        self._enable_caching = config.get('optimization.caching', True)
        
        # TensorRT settings
        self._trt_precision = config.get('optimization.precision', 'fp16')
        self._trt_workspace = config.get('optimization.workspace_size', 1 << 30)
        self._trt_cache_path = config.get('optimization.engine_cache', 'models/trt')
        
        # Batch processing
        self._min_batch_size = config.get('optimization.min_batch', 1)
        self._max_batch_size = config.get('optimization.max_batch', 32)
        self._batch_timeout = config.get('optimization.batch_timeout', 0.1)
        
        # Feature caching
        self._cache_size = config.get('optimization.cache_size', 1000)
        self._feature_cache: Dict[str, np.ndarray] = {}
        self._cache_lock = threading.Lock()
        
        # Processing queues
        self._preprocessing_queue = Queue(maxsize=100)
        self._inference_queue = Queue(maxsize=100)
        self._postprocessing_queue = Queue(maxsize=100)
        
        # Worker threads
        self._preprocessing_workers = []
        self._inference_workers = []
        self._postprocessing_workers = []
        
        # Performance monitoring
        self._metrics_history: List[PerformanceMetrics] = []
        self._max_history = config.get('optimization.metrics_history', 1000)
        
        # Initialize optimizations
        self._initialize_optimizations()
        
        # Statistics
        self._stats = {
            'total_processed': 0,
            'average_inference_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'gpu_utilization': 0.0,
            'memory_usage': 0.0
        }

        self.logger = logging.getLogger(__name__)

    def _initialize_optimizations(self) -> None:
        """Initialize optimization components"""
        try:
            # Initialize TensorRT if enabled
            if self._enable_tensorrt:
                self._initialize_tensorrt()
            
            # Initialize quantization if enabled
            if self._enable_quantization:
                self._initialize_quantization()
            
            # Start worker threads
            self._start_workers()
            
        except Exception as e:
            raise OptimizationError(f"Optimization initialization failed: {str(e)}")

    def _initialize_tensorrt(self) -> None:
        """Initialize TensorRT optimization"""
        try:
            # Create TensorRT logger
            trt_logger = trt.Logger(trt.Logger.WARNING)
            
            # Create builder and network
            builder = trt.Builder(trt_logger)
            network = builder.create_network(
                1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
            )
            
            # Set builder config
            config = builder.create_builder_config()
            config.max_workspace_size = self._trt_workspace
            
            # Set precision
            if self._trt_precision == 'fp16':
                config.set_flag(trt.BuilderFlag.FP16)
            elif self._trt_precision == 'int8':
                config.set_flag(trt.BuilderFlag.INT8)
            
            # Parse ONNX model
            parser = trt.OnnxParser(network, trt_logger)
            model_path = self.config.get('model.path')
            success = parser.parse_from_file(model_path)
            
            if not success:
                raise OptimizationError("Failed to parse ONNX model")
            
            # Build engine
            self._trt_engine = builder.build_engine(network, config)
            if not self._trt_engine:
                raise OptimizationError("Failed to build TensorRT engine")
            
            # Save engine
            with open(self._trt_cache_path, 'wb') as f:
                f.write(self._trt_engine.serialize())
            
        except Exception as e:
            raise OptimizationError(f"TensorRT initialization failed: {str(e)}")

    def _initialize_quantization(self) -> None:
        """Initialize model quantization"""
        try:
            # Load model
            model = torch.load(self.config.get('model.path'))
            
            # Quantize model
            quantized_model = torch.quantization.quantize_dynamic(
                model,
                {torch.nn.Linear, torch.nn.Conv2d},
                dtype=torch.qint8
            )
            
            # Save quantized model
            torch.save(
                quantized_model,
                self.config.get('model.path') + '.quantized'
            )
            
        except Exception as e:
            raise OptimizationError(f"Quantization failed: {str(e)}")

    def _start_workers(self) -> None:
        """Start worker threads for parallel processing"""
        try:
            # Start preprocessing workers
            num_cpu_workers = psutil.cpu_count() // 2
            for _ in range(num_cpu_workers):
                worker = threading.Thread(
                    target=self._preprocessing_worker,
                    daemon=True
                )
                worker.start()
                self._preprocessing_workers.append(worker)
            
            # Start inference workers
            num_gpu_workers = len(GPUtil.getGPUs())
            for _ in range(num_gpu_workers):
                worker = threading.Thread(
                    target=self._inference_worker,
                    daemon=True
                )
                worker.start()
                self._inference_workers.append(worker)
            
            # Start postprocessing workers
            for _ in range(num_cpu_workers):
                worker = threading.Thread(
                    target=self._postprocessing_worker,
                    daemon=True
                )
                worker.start()
                self._postprocessing_workers.append(worker)
            
        except Exception as e:
            raise OptimizationError(f"Failed to start workers: {str(e)}")

    def _preprocessing_worker(self) -> None:
        """Worker thread for preprocessing face images"""
        while True:
            try:
                # Get batch from queue
                batch = []
                start_time = datetime.utcnow()
                
                while (len(batch) < self._max_batch_size and
                       (datetime.utcnow() - start_time).total_seconds() < self._batch_timeout):
                    try:
                        item = self._preprocessing_queue.get_nowait()
                        batch.append(item)
                    except Queue.Empty:
                        if batch:
                            break
                        else:
                            continue
                
                if not batch:
                    continue
                
                # Process batch
                processed_batch = []
                for face_img in batch:
                    # Check cache first
                    cache_key = self._get_cache_key(face_img)
                    with self._cache_lock:
                        if cache_key in self._feature_cache:
                            self._stats['cache_hits'] += 1
                            processed_batch.append(self._feature_cache[cache_key])
                            continue
                    
                    # Resize and normalize
                    face_tensor = self._preprocess_face(face_img)
                    if face_tensor is not None:
                        processed_batch.append(face_tensor)
                        self._stats['cache_misses'] += 1
                
                # Put processed batch in inference queue
                if processed_batch:
                    self._inference_queue.put(processed_batch)
                
            except Exception as e:
                self.logger.error(f"Preprocessing worker error: {str(e)}")

    def _inference_worker(self) -> None:
        """Worker thread for model inference"""
        while True:
            try:
                # Get batch from queue
                batch = self._inference_queue.get()
                
                # Run inference
                with autocast(enabled=self._enable_amp):
                    if self._enable_tensorrt:
                        features = self._trt_inference(batch)
                    else:
                        features = self.model(batch)
                
                # Update cache
                if self._enable_caching:
                    with self._cache_lock:
                        for face_img, feature in zip(batch, features):
                            cache_key = self._get_cache_key(face_img)
                            self._feature_cache[cache_key] = feature
                            
                            # Limit cache size
                            if len(self._feature_cache) > self._cache_size:
                                self._feature_cache.pop(next(iter(self._feature_cache)))
                
                # Put results in postprocessing queue
                self._postprocessing_queue.put(features)
                
            except Exception as e:
                self.logger.error(f"Inference worker error: {str(e)}")

    def _postprocessing_worker(self) -> None:
        """Worker thread for postprocessing results"""
        while True:
            try:
                # Get batch from queue
                features = self._postprocessing_queue.get()
                
                # Update statistics
                self._stats['total_processed'] += len(features)
                
                # Update GPU metrics
                gpus = GPUtil.getGPUs()
                if gpus:
                    self._stats['gpu_utilization'] = gpus[0].load * 100
                    self._stats['memory_usage'] = gpus[0].memoryUtil * 100
                
            except Exception as e:
                self.logger.error(f"Postprocessing worker error: {str(e)}")

    def _preprocess_face(self, face_img: np.ndarray) -> Optional[torch.Tensor]:
        """Preprocess face image for model input"""
        try:
            # Resize to model input size
            input_size = self.config.get('model.input_size', (112, 112))
            face_img = cv2.resize(face_img, input_size)
            
            # Normalize
            face_img = face_img.astype(np.float32) / 255.0
            face_img = (face_img - 0.5) / 0.5
            
            # Convert to tensor
            face_tensor = torch.from_numpy(face_img).permute(2, 0, 1)
            face_tensor = face_tensor.unsqueeze(0)
            
            return face_tensor
            
        except Exception as e:
            self.logger.error(f"Face preprocessing error: {str(e)}")
            return None

    def _get_cache_key(self, face_img: np.ndarray) -> str:
        """Generate cache key for face image"""
        return str(hash(face_img.tobytes()))

    def _trt_inference(self, batch_input: torch.Tensor) -> torch.Tensor:
        """Run inference using TensorRT engine"""
        try:
            # Create execution context
            context = self._trt_engine.create_execution_context()
            
            # Allocate memory
            input_shape = (len(batch_input),) + tuple(batch_input.shape[1:])
            output_shape = (len(batch_input), self.config.get('model.feature_dim'))
            
            d_input = cuda.mem_alloc(batch_input.numel() * batch_input.element_size())
            d_output = cuda.mem_alloc(np.prod(output_shape) * 4)  # float32
            
            # Copy input to GPU
            cuda.memcpy_htod(d_input, batch_input.numpy())
            
            # Run inference
            context.execute_v2(bindings=[int(d_input), int(d_output)])
            
            # Copy output back to CPU
            output = np.empty(output_shape, dtype=np.float32)
            cuda.memcpy_dtoh(output, d_output)
            
            return torch.from_numpy(output)
            
        except Exception as e:
            raise OptimizationError(f"TensorRT inference failed: {str(e)}")

    def _update_metrics(self,
                       inference_time: float,
                       preprocessing_time: float,
                       postprocessing_time: float,
                       batch_size: int) -> None:
        """Update performance metrics"""
        try:
            # Calculate metrics
            total_time = inference_time + preprocessing_time + postprocessing_time
            throughput = batch_size / (total_time / 1000)  # faces per second
            
            # Get GPU metrics
            gpus = GPUtil.getGPUs()
            gpu_util = gpus[0].load * 100 if gpus else 0
            mem_usage = gpus[0].memoryUtil * 100 if gpus else 0
            
            # Create metrics object
            metrics = PerformanceMetrics(
                inference_time=inference_time,
                preprocessing_time=preprocessing_time,
                postprocessing_time=postprocessing_time,
                total_time=total_time,
                batch_size=batch_size,
                gpu_utilization=gpu_util,
                memory_usage=mem_usage,
                throughput=throughput,
                timestamp=datetime.utcnow()
            )
            
            # Update history
            self._metrics_history.append(metrics)
            if len(self._metrics_history) > self._max_history:
                self._metrics_history.pop(0)
                
        except Exception as e:
            self.logger.error(f"Metrics update error: {str(e)}")

    async def get_metrics(self,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[PerformanceMetrics]:
        """Get performance metrics for specified time range"""
        try:
            if not start_time:
                start_time = datetime.min
            if not end_time:
                end_time = datetime.max
                
            return [
                m for m in self._metrics_history
                if start_time <= m.timestamp <= end_time
            ]
            
        except Exception as e:
            self.logger.error(f"Error retrieving metrics: {str(e)}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get current optimization statistics"""
        return self._stats.copy()

    def optimize_model(self, model: nn.Module) -> nn.Module:
        """Apply optimization techniques to model"""
        try:
            # Enable AMP if configured
            if self.config.get('optimization.amp', True):
                model = model.half()
            
            # Enable TensorRT if configured
            if self._enable_tensorrt:
                # Export to ONNX
                dummy_input = torch.randn(1, 3, 112, 112).cuda()
                torch.onnx.export(
                    model, 
                    dummy_input,
                    'model.onnx',
                    input_names=['input'],
                    output_names=['output'],
                    dynamic_axes={
                        'input': {0: 'batch_size'},
                        'output': {0: 'batch_size'}
                    }
                )
                
                # Initialize TensorRT
                self._initialize_tensorrt()
            
            # Enable quantization if configured
            if self._enable_quantization:
                model = self._initialize_quantization()
            
            return model
            
        except Exception as e:
            raise OptimizationError(f"Model optimization failed: {str(e)}") 