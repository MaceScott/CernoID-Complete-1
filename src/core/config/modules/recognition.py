from dataclasses import dataclass
from typing import Tuple, Optional
import torch

@dataclass
class ModelConfig:
    """Face recognition model configuration"""
    model_path: str
    input_size: Tuple[int, int] = (224, 224)
    batch_size: int = 32
    confidence_threshold: float = 0.85
    gpu_enabled: bool = True
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    num_workers: int = 4
    pin_memory: bool = True
    use_amp: bool = True
    model_type: str = 'resnet50'
    embedding_size: int = 512
    quantization_enabled: bool = False
    use_jit: bool = True
    use_onnx: bool = False

@dataclass
class DetectionConfig:
    """Face detection configuration"""
    min_face_size: Tuple[int, int] = (30, 30)
    scale_factor: float = 1.1
    min_neighbors: int = 5
    use_gpu: bool = True
    batch_size: int = 8
    confidence_threshold: float = 0.9 