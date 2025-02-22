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

from ..base import BaseComponent
from ..utils.errors import OptimizationError

@dataclass
class OptimizationConfig:
    batch_size: int
    use_amp: bool
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

class RecognitionOptimizer(BaseComponent):
    """Advanced performance optimization system"""
    
    def __init__(self, config: dict):
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
        """Start worker threads"""
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
        """Preprocessing worker thread"""
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
                    # Resize and normalize
                    face_tensor = self._preprocess_face(face_img)
                    if face_tensor is not None:
                        processed_batch.append(face_tensor)
                
                # Put processed batch in inference queue
                if processed_batch:
                    self._inference_queue.put(processed_batch)
                
            except Exception as e:
                self.logger.error(f"Preprocessing worker error: {str(e)}")

    def _inference_worker(self) -> None:
        """Inference worker thread"""
        while True:
            try:
                # Get batch from queue
                batch = self._inference_queue.get()
                if not batch:
                    continue
                
                # Stack tensors
                batch_input = torch.cat(batch, dim=0)
                
                # Run inference
                start_time = datetime.utcnow()
                
                if self._enable_tensorrt:
                    features = self._trt_inference(batch_input)
                else:
                    with torch.no_grad():
                        features = self.model(batch_input)
                
                inference_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Put results in postprocessing queue
                self._postprocessing_queue.put((features, inference_time))
                
            except Exception as e:
                self.logger.error(f"Inference worker error: {str(e)}")

    def _postprocessing_worker(self) -> None:
        """Postprocessing worker thread"""
        while True:
            try:
                # Get results from queue
                results = self._postprocessing_queue.get()
                if not results:
                    continue
                
                features, inference_time = results
                
                # Process features
                start_time = datetime.utcnow()
                
                processed_features = []
                for feature in features:
                    # Normalize feature vector
                    feature = feature.cpu().numpy()
                    feature = feature / np.linalg.norm(feature)
                    processed_features.append(feature)
                
                postprocessing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Update metrics
                self._update_metrics(
                    inference_time=inference_time,
                    postprocessing_time=postprocessing_time,
                    batch_size=len(processed_features)
                )
                
            except Exception as e:
                self.logger.error(f"Postprocessing worker error: {str(e)}")

    def _preprocess_face(self, face_img: np.ndarray) -> Optional[torch.Tensor]:
        """Preprocess face image"""
        try:
            # Check cache if enabled
            if self._enable_caching:
                cache_key = self._get_cache_key(face_img)
                with self._cache_lock:
                    if cache_key in self._feature_cache:
                        self._stats['cache_hits'] += 1
                        return self._feature_cache[cache_key]
            
            # Resize image
            face_img = cv2.resize(face_img, (224, 224))
            
            # Convert to RGB
            if len(face_img.shape) == 2:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2RGB)
            elif face_img.shape[2] == 4:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGRA2RGB)
            elif face_img.shape[2] == 3:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            
            # Normalize
            face_img = face_img.astype(np.float32) / 255.0
            face_img = (face_img - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
            
            # Convert to tensor
            face_tensor = torch.from_numpy(face_img).permute(2, 0, 1)
            face_tensor = face_tensor.unsqueeze(0)
            
            if torch.cuda.is_available():
                face_tensor = face_tensor.cuda()
            
            # Update cache
            if self._enable_caching:
                with self._cache_lock:
                    if len(self._feature_cache) >= self._cache_size:
                        self._feature_cache.pop(next(iter(self._feature_cache)))
                    self._feature_cache[cache_key] = face_tensor
                    self._stats['cache_misses'] += 1
            
            return face_tensor
            
        except Exception as e:
            self.logger.error(f"Face preprocessing failed: {str(e)}")
            return None

    def _get_cache_key(self, face_img: np.ndarray) -> str:
        """Generate cache key for face image"""
        try:
            # Calculate image hash
            return str(hash(face_img.tobytes()))
        except Exception:
            return ""

    def _trt_inference(self, batch_input: torch.Tensor) -> torch.Tensor:
        """Run TensorRT inference"""
        try:
            # Get engine context
            context = self._trt_engine.create_execution_context()
            
            # Prepare input
            input_batch = batch_input.cpu().numpy()
            
            # Allocate output buffer
            output_shape = (len(input_batch), 512)  # Adjust size as needed
            output = np.empty(output_shape, dtype=np.float32)
            
            # Run inference
            context.execute_v2(
                bindings=[
                    input_batch.ctypes.data,
                    output.ctypes.data
                ]
            )
            
            # Convert to tensor
            return torch.from_numpy(output)
            
        except Exception as e:
            raise OptimizationError(f"TensorRT inference failed: {str(e)}")

    def _update_metrics(self,
                       inference_time: float,
                       postprocessing_time: float,
                       batch_size: int) -> None:
        """Update performance metrics"""
        try:
            # Get GPU metrics
            gpu = GPUtil.getGPUs()[0]
            gpu_util = gpu.load * 100
            mem_util = gpu.memoryUtil * 100
            
            # Calculate throughput
            total_time = inference_time + postprocessing_time
            throughput = batch_size / (total_time / 1000)
            
            # Create metrics
            metrics = PerformanceMetrics(
                inference_time=inference_time,
                preprocessing_time=0.0,  # Set by preprocessing worker
                postprocessing_time=postprocessing_time,
                total_time=total_time,
                batch_size=batch_size,
                gpu_utilization=gpu_util,
                memory_usage=mem_util,
                throughput=throughput,
                timestamp=datetime.utcnow()
            )
            
            # Update history
            self._metrics_history.append(metrics)
            if len(self._metrics_history) > self._max_history:
                self._metrics_history.pop(0)
            
            # Update statistics
            self._stats['total_processed'] += batch_size
            self._stats['average_inference_time'] = np.mean([
                m.inference_time for m in self._metrics_history
            ])
            self._stats['gpu_utilization'] = gpu_util
            self._stats['memory_usage'] = mem_util
            
        except Exception as e:
            self.logger.error(f"Metrics update failed: {str(e)}")

    async def get_metrics(self,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[PerformanceMetrics]:
        """Get performance metrics"""
        try:
            if start_time is None and end_time is None:
                return self._metrics_history.copy()
            
            # Filter by time range
            metrics = [
                m for m in self._metrics_history
                if (start_time is None or m.timestamp >= start_time) and
                   (end_time is None or m.timestamp <= end_time)
            ]
            
            return metrics
            
        except Exception as e:
            raise OptimizationError(f"Failed to get metrics: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get optimization statistics"""
        return self._stats.copy()

    def optimize_model(self, model: nn.Module) -> nn.Module:
        """Apply model optimizations"""
        # Move model to device
        model = model.to(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
        
        # Enable fusion optimizations
        if hasattr(torch, 'backends'):
            torch.backends.cudnn.benchmark = True
            
        # Quantize model if supported
        if hasattr(torch.quantization, 'quantize_dynamic'):
            try:
                model = torch.quantization.quantize_dynamic(
                    model, {torch.nn.Linear}, dtype=torch.qint8
                )
            except Exception as e:
                self.logger.warning(f"Quantization failed: {str(e)}")
                
        return model 