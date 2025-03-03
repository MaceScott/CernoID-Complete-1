"""
Advanced ML model version control and management system.

This module provides:
- Model versioning and tracking
- Automatic model loading and saving
- Version rollback capabilities
- Model metrics tracking
- Hash-based integrity verification
"""

from typing import Dict, Optional, List, Any
import hashlib
import json
from datetime import datetime
from pathlib import Path
import shutil
import torch
import logging
from dataclasses import dataclass
import asyncio

from ..base import BaseComponent
from ..utils.errors import ModelError

@dataclass
class ModelVersion:
    """Model version information"""
    version_id: str
    model_type: str
    created_at: datetime
    metrics: Dict[str, Any]
    parameters: Dict[str, Any]
    file_hash: str
    is_active: bool
    framework: str  # pytorch, tensorflow, onnx etc.
    device: str  # cpu, cuda:0 etc.
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None

class ModelManager(BaseComponent):
    """Advanced ML model version control and management"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Model storage settings
        self.models_dir = Path(config.get('models.storage_path', 'data/models'))
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._version_file = self.models_dir / 'versions.json'
        
        # Version tracking
        self._versions: Dict[str, ModelVersion] = {}
        self._active_versions: Dict[str, str] = {}  # model_type -> version_id
        
        # Model cache
        self._model_cache: Dict[str, torch.nn.Module] = {}
        self._cache_lock = asyncio.Lock()
        
        # Load existing versions
        self._load_versions()
        
        # Start periodic cleanup
        self._cleanup_interval = config.get('models.cleanup_interval', 3600)  # 1 hour
        asyncio.create_task(self._periodic_cleanup())

    async def save_model(self,
                        model: torch.nn.Module,
                        model_type: str,
                        metrics: Dict[str, Any],
                        parameters: Dict[str, Any],
                        input_shape: Optional[List[int]] = None,
                        output_shape: Optional[List[int]] = None) -> ModelVersion:
        """
        Save model with version tracking
        
        Args:
            model: PyTorch model to save
            model_type: Type of model (e.g. 'face_detector', 'encoder')
            metrics: Model performance metrics
            parameters: Model parameters and configuration
            input_shape: Expected input tensor shape
            output_shape: Expected output tensor shape
            
        Returns:
            ModelVersion object for the saved model
        """
        try:
            # Generate version ID
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            version_id = f"{model_type}_{timestamp}"
            
            # Save model file
            model_path = self.models_dir / f"{version_id}.pt"
            torch.save({
                'state_dict': model.state_dict(),
                'parameters': parameters,
                'metrics': metrics
            }, model_path)
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(model_path)
            
            # Create version info
            version = ModelVersion(
                version_id=version_id,
                model_type=model_type,
                created_at=datetime.utcnow(),
                metrics=metrics,
                parameters=parameters,
                file_hash=file_hash,
                is_active=False,
                framework='pytorch',
                device=str(next(model.parameters()).device),
                input_shape=input_shape,
                output_shape=output_shape
            )
            
            # Update version tracking
            self._versions[version_id] = version
            self._save_versions()
            
            # Activate if first version of type
            if model_type not in self._active_versions:
                await self.activate_version(version_id)
            
            self.logger.info(f"Saved model version {version_id}")
            return version
            
        except Exception as e:
            self.logger.error(f"Failed to save model: {str(e)}")
            raise ModelError(f"Model save failed: {str(e)}")

    async def load_model(self,
                        model_type: str,
                        version_id: Optional[str] = None,
                        device: Optional[str] = None) -> torch.nn.Module:
        """
        Load model with caching
        
        Args:
            model_type: Type of model to load
            version_id: Specific version to load (default: active version)
            device: Device to load model on (default: model's original device)
            
        Returns:
            Loaded PyTorch model
        """
        try:
            # Get version to load
            if version_id is None:
                version_id = self._active_versions.get(model_type)
                if not version_id:
                    raise ModelError(f"No active version for model type {model_type}")
                    
            version = self._versions.get(version_id)
            if not version:
                raise ModelError(f"Version {version_id} not found")
                
            # Check cache
            cache_key = f"{version_id}_{device or version.device}"
            async with self._cache_lock:
                if cache_key in self._model_cache:
                    return self._model_cache[cache_key]
            
            # Load model file
            model_path = self.models_dir / f"{version_id}.pt"
            if not model_path.exists():
                raise ModelError(f"Model file not found: {model_path}")
                
            # Verify hash
            if self._calculate_file_hash(model_path) != version.file_hash:
                raise ModelError(f"Model file hash mismatch for version {version_id}")
                
            # Load state dict
            checkpoint = torch.load(model_path, map_location=device or version.device)
            model = self._create_model_instance(version.model_type)
            model.load_state_dict(checkpoint['state_dict'])
            
            # Cache model
            async with self._cache_lock:
                self._model_cache[cache_key] = model
            
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            raise ModelError(f"Model load failed: {str(e)}")

    async def activate_version(self, version_id: str) -> None:
        """Activate a model version"""
        try:
            version = self._versions.get(version_id)
            if not version:
                raise ModelError(f"Version {version_id} not found")
                
            # Deactivate current version
            current_active = self._active_versions.get(version.model_type)
            if current_active:
                self._versions[current_active].is_active = False
                
            # Activate new version
            version.is_active = True
            self._active_versions[version.model_type] = version_id
            self._save_versions()
            
            # Clear cache for this model type
            await self._clear_model_cache(version.model_type)
            
            self.logger.info(f"Activated model version {version_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to activate version: {str(e)}")
            raise ModelError(f"Version activation failed: {str(e)}")

    async def rollback_version(self, model_type: str) -> Optional[ModelVersion]:
        """Rollback to previous version of a model type"""
        try:
            # Get version history for model type
            versions = [v for v in self._versions.values() 
                       if v.model_type == model_type]
            versions.sort(key=lambda v: v.created_at, reverse=True)
            
            if len(versions) < 2:
                self.logger.warning(f"No version to rollback to for {model_type}")
                return None
                
            # Get previous version
            prev_version = versions[1]  # Second most recent
            await self.activate_version(prev_version.version_id)
            
            return prev_version
            
        except Exception as e:
            self.logger.error(f"Failed to rollback version: {str(e)}")
            raise ModelError(f"Version rollback failed: {str(e)}")

    async def get_version_history(self, model_type: Optional[str] = None) -> List[ModelVersion]:
        """Get version history for all or specific model type"""
        try:
            versions = list(self._versions.values())
            if model_type:
                versions = [v for v in versions if v.model_type == model_type]
                
            versions.sort(key=lambda v: v.created_at, reverse=True)
            return versions
            
        except Exception as e:
            self.logger.error(f"Failed to get version history: {str(e)}")
            raise ModelError(f"Failed to get version history: {str(e)}")

    async def _clear_model_cache(self, model_type: str) -> None:
        """Clear cached models of specified type"""
        async with self._cache_lock:
            keys_to_remove = [k for k in self._model_cache.keys() 
                            if k.startswith(f"{model_type}_")]
            for key in keys_to_remove:
                del self._model_cache[key]

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up old model files"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                # Get all model files
                model_files = list(self.models_dir.glob('*.pt'))
                
                # Keep active versions and recent history
                keep_versions = set()
                for model_type, active_id in self._active_versions.items():
                    keep_versions.add(active_id)
                    
                    # Keep recent history
                    versions = await self.get_version_history(model_type)
                    for version in versions[:2]:  # Keep 2 most recent
                        keep_versions.add(version.version_id)
                
                # Remove old files
                for file in model_files:
                    version_id = file.stem
                    if version_id not in keep_versions:
                        file.unlink()
                        if version_id in self._versions:
                            del self._versions[version_id]
                            
                self._save_versions()
                
            except Exception as e:
                self.logger.error(f"Periodic cleanup failed: {str(e)}")

    def _load_versions(self) -> None:
        """Load version information from disk"""
        try:
            if self._version_file.exists():
                with open(self._version_file, 'r') as f:
                    data = json.load(f)
                    
                self._versions = {}
                self._active_versions = {}
                
                for version_data in data['versions']:
                    version = ModelVersion(
                        version_id=version_data['version_id'],
                        model_type=version_data['model_type'],
                        created_at=datetime.fromisoformat(version_data['created_at']),
                        metrics=version_data['metrics'],
                        parameters=version_data['parameters'],
                        file_hash=version_data['file_hash'],
                        is_active=version_data['is_active'],
                        framework=version_data.get('framework', 'pytorch'),
                        device=version_data.get('device', 'cpu'),
                        input_shape=version_data.get('input_shape'),
                        output_shape=version_data.get('output_shape')
                    )
                    
                    self._versions[version.version_id] = version
                    if version.is_active:
                        self._active_versions[version.model_type] = version.version_id
                        
                self.logger.info(f"Loaded {len(self._versions)} model versions")
                
        except Exception as e:
            self.logger.error(f"Failed to load versions: {str(e)}")
            self._versions = {}
            self._active_versions = {}

    def _save_versions(self) -> None:
        """Save version information to disk"""
        try:
            data = {
                'versions': [
                    {
                        'version_id': v.version_id,
                        'model_type': v.model_type,
                        'created_at': v.created_at.isoformat(),
                        'metrics': v.metrics,
                        'parameters': v.parameters,
                        'file_hash': v.file_hash,
                        'is_active': v.is_active,
                        'framework': v.framework,
                        'device': v.device,
                        'input_shape': v.input_shape,
                        'output_shape': v.output_shape
                    }
                    for v in self._versions.values()
                ]
            }
            
            with open(self._version_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save versions: {str(e)}")

    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest()

    def _create_model_instance(self, model_type: str) -> torch.nn.Module:
        """Create a new instance of a model architecture"""
        # This should be implemented based on your model architectures
        raise NotImplementedError("Model creation not implemented")

# Global model manager instance
model_manager = ModelManager({}) 