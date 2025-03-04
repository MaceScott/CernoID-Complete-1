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
from pathlib import Path

from .base import BaseComponent
from .errors import OptimizationError

@dataclass
class OptimizationConfig:
    """Configuration for optimization settings"""
    batch_size: int = 32
    use_amp: bool = True  # Automatic mixed precision
    num_workers: int = 4
    pin_memory: bool = True
    cache_size: int = 10000
    feature_dim: int = 512
    min_batch_size: int = 1
    max_batch_size: int = 64
    batch_timeout: float = 0.1
    tensorrt_precision: str = 'fp16'
    tensorrt_workspace: int = 1 << 30
    tensorrt_cache_path: str = 'models/trt'
    
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
        
        # Initialize configuration
        self.config = OptimizationConfig(
            batch_size=config.get('optimization.batch_size', 32),
            use_amp=config.get('optimization.use_amp', True),
            num_workers=config.get('optimization.num_workers', 4),
            pin_memory=config.get('optimization.pin_memory', True),
            cache_size=config.get('optimization.cache_size', 10000),
            feature_dim=config.get('optimization.feature_dim', 512),
            min_batch_size=config.get('optimization.min_batch_size', 1),
            max_batch_size=config.get('optimization.max_batch_size', 64),
            batch_timeout=config.get('optimization.batch_timeout', 0.1),
            tensorrt_precision=config.get('optimization.precision', 'fp16'),
            tensorrt_workspace=config.get('optimization.workspace_size', 1 << 30),
            tensorrt_cache_path=config.get('optimization.engine_cache', 'models/trt')
        )
        
        # Initialize caches
        self._feature_cache = {}
        self._cache_lock = threading.Lock()
        
        # Initialize queues
        self._preprocessing_queue = Queue(maxsize=100)
        self._inference_queue = Queue(maxsize=100)
        self._postprocessing_queue = Queue(maxsize=100)
        
        # Initialize workers
        self._preprocessing_workers = []
        self._inference_workers = []
        self._postprocessing_workers = []
        
        # Initialize metrics
        self._metrics_history: List[PerformanceMetrics] = []
        self._max_history = config.get('optimization.metrics_history', 1000)
        
        # Initialize TensorRT
        self._initialize_tensorrt()
        
        # Initialize workers
        self._start_workers()
        
        # Initialize statistics
        self._stats = {
            'total_processed': 0,
            'average_inference_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'gpu_utilization': 0.0,
            'memory_usage': 0.0
        }

        self.logger = logging.getLogger(__name__)

    def _initialize_tensorrt(self) -> None:
        """Initialize TensorRT engine."""
        try:
            # Create TensorRT builder
            TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
            builder = trt.Builder(TRT_LOGGER)
            
            # Create network
            EXPLICIT_BATCH = 1 << (int)(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
            network = builder.create_network(EXPLICIT_BATCH)
            
            # Create optimization profile
            profile = builder.create_optimization_profile()
            profile.set_shape(
                "input",  # Input tensor name
                (self.config.min_batch_size, 3, 112, 112),  # Min shape
                (self.config.batch_size, 3, 112, 112),      # Opt shape
                (self.config.max_batch_size, 3, 112, 112)   # Max shape
            )
            
            # Create config
            config = builder.create_builder_config()
            config.add_optimization_profile(profile)
            config.max_workspace_size = self.config.tensorrt_workspace
            
            # Set precision
            if self.config.tensorrt_precision == 'fp16':
                config.set_flag(trt.BuilderFlag.FP16)
            
            # Parse ONNX model
            parser = trt.OnnxParser(network, TRT_LOGGER)
            onnx_path = Path(self.config.tensorrt_cache_path) / 'model.onnx'
            success = parser.parse_from_file(str(onnx_path))
            
            if not success:
                error_msgs = []
                for idx in range(parser.num_errors):
                    error_msgs.append(parser.get_error(idx))
                raise OptimizationError(f"Failed to parse ONNX model: {error_msgs}")
            
            # Build engine
            engine = builder.build_engine(network, config)
            if engine is None:
                raise OptimizationError("Failed to build TensorRT engine")
            
            # Save engine
            engine_path = Path(self.config.tensorrt_cache_path) / 'model.engine'
            engine_path.parent.mkdir(parents=True, exist_ok=True)
            with open(engine_path, 'wb') as f:
                f.write(engine.serialize())
            
            self.logger.info("TensorRT engine initialized successfully")
            
        except Exception as e:
            raise OptimizationError(f"TensorRT initialization failed: {str(e)}")

    def _start_workers(self) -> None:
        """Start worker threads."""
        try:
            # Start preprocessing workers
            for _ in range(self.config.num_workers):
                worker = threading.Thread(
                    target=self._preprocessing_worker,
                    daemon=True
                )
                worker.start()
                self._preprocessing_workers.append(worker)
            
            # Start inference workers
            for _ in range(torch.cuda.device_count()):
                worker = threading.Thread(
                    target=self._inference_worker,
                    daemon=True
                )
                worker.start()
                self._inference_workers.append(worker)
            
            # Start postprocessing workers
            for _ in range(self.config.num_workers):
                worker = threading.Thread(
                    target=self._postprocessing_worker,
                    daemon=True
                )
                worker.start()
                self._postprocessing_workers.append(worker)
                
            self.logger.info(
                f"Started {len(self._preprocessing_workers)} preprocessing workers, "
                f"{len(self._inference_workers)} inference workers, and "
                f"{len(self._postprocessing_workers)} postprocessing workers"
            )
            
        except Exception as e:
            raise OptimizationError(f"Failed to start workers: {str(e)}")

    def _preprocessing_worker(self) -> None:
        """Worker thread for preprocessing face images."""
        while True:
            try:
                # Get batch from queue
                batch = []
                start_time = datetime.utcnow()
                
                while (len(batch) < self.config.max_batch_size and
                       (datetime.utcnow() - start_time).total_seconds() < self.config.batch_timeout):
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
                    
                    # Preprocess image
                    try:
                        # Resize to 112x112
                        face_img = cv2.resize(face_img, (112, 112))
                        
                        # Convert to RGB
                        if len(face_img.shape) == 2:
                            face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2RGB)
                        elif face_img.shape[2] == 4:
                            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGRA2RGB)
                        elif face_img.shape[2] == 3:
                            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                            
                        # Normalize
                        face_img = face_img.astype(np.float32) / 255.0
                        face_img = (face_img - 0.5) / 0.5
                        
                        # Convert to tensor
                        face_tensor = torch.from_numpy(face_img).permute(2, 0, 1)
                        if self.config.pin_memory:
                            face_tensor = face_tensor.pin_memory()
                            
                        processed_batch.append(face_tensor)
                        self._stats['cache_misses'] += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to preprocess image: {str(e)}")
                        continue
                
                # Put processed batch in inference queue
                if processed_batch:
                    self._inference_queue.put(processed_batch)
                
            except Exception as e:
                self.logger.error(f"Preprocessing worker error: {str(e)}")

    def _inference_worker(self) -> None:
        """Worker thread for model inference."""
        try:
            # Load TensorRT engine
            TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
            engine_path = Path(self.config.tensorrt_cache_path) / 'model.engine'
            
            with open(engine_path, 'rb') as f:
                engine_bytes = f.read()
            
            runtime = trt.Runtime(TRT_LOGGER)
            engine = runtime.deserialize_cuda_engine(engine_bytes)
            
            # Create execution context
            context = engine.create_execution_context()
            
            while True:
                try:
                    # Get batch from queue
                    batch = self._inference_queue.get()
                    if not batch:
                        continue
                    
                    # Stack tensors
                    batch_tensor = torch.stack(batch).cuda()
                    
                    # Run inference
                    with autocast(enabled=self.config.use_amp):
                        # Allocate output buffer
                        output = torch.empty(
                            (len(batch), self.config.feature_dim),
                            dtype=torch.float32,
                            device='cuda'
                        )
                        
                        # Set input shape
                        context.set_binding_shape(
                            0,  # Input binding index
                            (len(batch), 3, 112, 112)
                        )
                        
                        # Run inference
                        bindings = [
                            batch_tensor.data_ptr(),
                            output.data_ptr()
                        ]
                        context.execute_v2(bindings)
                        
                        # Normalize output features
                        output = torch.nn.functional.normalize(output, p=2, dim=1)
                        
                    # Put results in postprocessing queue
                    self._postprocessing_queue.put(output.cpu())
                    
                except Exception as e:
                    self.logger.error(f"Inference worker error: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize inference worker: {str(e)}")

    def _postprocessing_worker(self) -> None:
        """Worker thread for postprocessing results."""
        while True:
            try:
                # Get batch from queue
                batch = self._postprocessing_queue.get()
                if not batch:
                    continue
                
                # Update cache
                with self._cache_lock:
                    for idx, features in enumerate(batch):
                        if len(self._feature_cache) >= self.config.cache_size:
                            # Remove oldest entry
                            oldest_key = next(iter(self._feature_cache))
                            del self._feature_cache[oldest_key]
                        
                        # Add new entry
                        cache_key = self._get_cache_key(features)
                        self._feature_cache[cache_key] = features
                
                # Update statistics
                self._stats['total_processed'] += len(batch)
                
            except Exception as e:
                self.logger.error(f"Postprocessing worker error: {str(e)}")

    def _get_cache_key(self, data: Union[np.ndarray, torch.Tensor]) -> str:
        """Generate cache key for data."""
        if isinstance(data, np.ndarray):
            return hash(data.tobytes())
        elif isinstance(data, torch.Tensor):
            return hash(data.cpu().numpy().tobytes())
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

    def _update_metrics(self,
                       inference_time: float,
                       preprocessing_time: float,
                       postprocessing_time: float,
                       batch_size: int) -> None:
        """Update performance metrics."""
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
                
            # Update statistics
            self._stats.update({
                'average_inference_time': np.mean([m.inference_time for m in self._metrics_history]),
                'gpu_utilization': gpu_util,
                'memory_usage': mem_usage
            })
                
        except Exception as e:
            self.logger.error(f"Metrics update error: {str(e)}")

    async def get_metrics(self,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[PerformanceMetrics]:
        """Get performance metrics for specified time range."""
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
        """Get current optimization statistics."""
        return self._stats.copy()

    def optimize_model(self, model: nn.Module) -> nn.Module:
        """Apply optimization techniques to model"""
        try:
            # Enable AMP if configured
            if self.config.use_amp:
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