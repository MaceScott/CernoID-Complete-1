from typing import Dict, Optional, List
import hashlib
import json
from datetime import datetime
from pathlib import Path
import shutil
import torch
import logging
from dataclasses import dataclass

@dataclass
class ModelVersion:
    """Model version information"""
    version_id: str
    model_type: str
    created_at: datetime
    metrics: Dict
    parameters: Dict
    file_hash: str
    is_active: bool

class ModelManager:
    """ML model version control and management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.models_dir = Path(config['models_dir'])
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('ModelManager')
        self._version_file = self.models_dir / 'versions.json'
        self._versions: Dict[str, ModelVersion] = {}
        self._load_versions()

    async def save_model(self, model: torch.nn.Module, 
                        model_type: str, 
                        metrics: Dict,
                        parameters: Dict) -> ModelVersion:
        """Save new model version"""
        try:
            # Generate version ID
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            version_id = f"{model_type}_{timestamp}"
            
            # Save model file
            model_path = self.models_dir / f"{version_id}.pt"
            torch.save(model.state_dict(), model_path)
            
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
                is_active=False
            )
            
            # Save version info
            self._versions[version_id] = version
            self._save_versions()
            
            self.logger.info(f"Saved new model version: {version_id}")
            return version
            
        except Exception as e:
            self.logger.error(f"Model save failed: {str(e)}")
            raise

    async def load_model(self, version_id: Optional[str] = None) -> torch.nn.Module:
        """Load model by version ID or latest active version"""
        try:
            if not version_id:
                version = self._get_active_version()
            else:
                version = self._versions.get(version_id)
                
            if not version:
                raise ValueError("Model version not found")
                
            model_path = self.models_dir / f"{version.version_id}.pt"
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
                
            # Verify file hash
            current_hash = self._calculate_file_hash(model_path)
            if current_hash != version.file_hash:
                raise ValueError("Model file hash mismatch")
                
            # Load model
            model = self._create_model_instance(version.model_type)
            model.load_state_dict(torch.load(model_path))
            
            return model
            
        except Exception as e:
            self.logger.error(f"Model load failed: {str(e)}")
            raise

    async def activate_version(self, version_id: str) -> None:
        """Set model version as active"""
        if version_id not in self._versions:
            raise ValueError(f"Version not found: {version_id}")
            
        # Deactivate current active version
        current_active = self._get_active_version()
        if current_active:
            current_active.is_active = False
            
        # Activate new version
        self._versions[version_id].is_active = True
        self._save_versions()
        
        self.logger.info(f"Activated model version: {version_id}")

    async def rollback_version(self, version_id: str) -> None:
        """Rollback to previous model version"""
        if version_id not in self._versions:
            raise ValueError(f"Version not found: {version_id}")
            
        await self.activate_version(version_id)
        self.logger.info(f"Rolled back to version: {version_id}")

    async def get_version_history(self) -> List[ModelVersion]:
        """Get model version history"""
        return sorted(
            self._versions.values(),
            key=lambda v: v.created_at,
            reverse=True
        )

    def _load_versions(self) -> None:
        """Load version information from file"""
        if self._version_file.exists():
            with open(self._version_file, 'r') as f:
                data = json.load(f)
                self._versions = {
                    k: ModelVersion(**v) for k, v in data.items()
                }

    def _save_versions(self) -> None:
        """Save version information to file"""
        with open(self._version_file, 'w') as f:
            data = {
                k: v.__dict__ for k, v in self._versions.items()
            }
            json.dump(data, f, default=str)

    def _get_active_version(self) -> Optional[ModelVersion]:
        """Get current active model version"""
        active_versions = [
            v for v in self._versions.values() if v.is_active
        ]
        return active_versions[0] if active_versions else None

    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of model file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _create_model_instance(self, model_type: str) -> torch.nn.Module:
        """Create new model instance based on type"""
        # Implement model creation based on type
        pass 