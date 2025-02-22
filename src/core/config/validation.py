from pydantic import BaseModel, Field
from typing import List, Optional

class DatabaseConfig(BaseModel):
    host: str
    port: int = Field(ge=1, le=65535)
    name: str
    user: str
    password: str
    pool_size: int = Field(ge=1, le=100)

class RecognitionConfig(BaseModel):
    model_path: str
    confidence_threshold: float = Field(ge=0.0, le=1.0)
    batch_size: int = Field(ge=1)
    gpu_enabled: bool

class CameraConfig(BaseModel):
    name: str
    url: str
    enabled: bool
    resolution: List[int]
    fps: int = Field(ge=1, le=60)

class SystemConfig(BaseModel):
    database: DatabaseConfig
    recognition: RecognitionConfig
    cameras: List[CameraConfig] 