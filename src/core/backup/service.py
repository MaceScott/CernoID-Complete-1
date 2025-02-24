"""
Backup service with encryption and verification.
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio
import aiofiles
import json
from datetime import datetime

from ..utils.config import get_settings
from ..utils.logging import get_logger
from ..security.encryption import encryption_service
from ..database.service import DatabaseService

class BackupService:
    """Advanced backup service with encryption"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.db = DatabaseService()
        
        # Initialize backup directory
        self.backup_dir = Path(self.settings.backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    async def create_backup(self,
                          backup_type: str = "full") -> Dict[str, Any]:
        """Create encrypted backup."""
        try:
            backup_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{backup_type}_{backup_id}"
            backup_path.mkdir(exist_ok=True)
            
            # Simplified backup process
            backup_files = await self._collect_backup_files(backup_type)
            await self._encrypt_backup_files(backup_files, backup_path)
            
            return {
                "backup_id": backup_id,
                "type": backup_type,
                "path": str(backup_path),
                "files": len(backup_files)
            }
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            raise
            
    async def restore_backup(self, backup_id: str) -> bool:
        """Restore system from backup."""
        try:
            # Download backup
            backup_path = await self._download_from_cloud(backup_id)
            
            # Extract archive
            restore_path = self.backup_dir / "restore"
            await self._extract_archive(backup_path, restore_path)
            
            # Restore components
            await self._restore_database(restore_path)
            await self._restore_models(restore_path)
            await self._restore_configs(restore_path)
            
            # Cleanup
            shutil.rmtree(restore_path)
            backup_path.unlink()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {str(e)}")
            return False
            
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        try:
            async with self.session.client('s3') as s3:
                response = await s3.list_objects_v2(
                    Bucket=self.settings.backup_bucket,
                    Prefix="backups/"
                )
                
                backups = []
                for obj in response.get('Contents', []):
                    backups.append({
                        "backup_id": obj['Key'].split('/')[-1],
                        "timestamp": obj['LastModified'],
                        "size": obj['Size']
                    })
                    
                return backups
                
        except Exception as e:
            self.logger.error(f"Listing backups failed: {str(e)}")
            return []
            
    async def _backup_database(self, backup_path: Path):
        """Backup database to file."""
        dump_path = backup_path / "database.sql"
        await self.db.backup_to_file(str(dump_path))
        
    async def _backup_models(self, backup_path: Path):
        """Backup model files."""
        models_path = backup_path / "models"
        models_path.mkdir(exist_ok=True)
        
        # Copy model files
        source_path = Path(self.settings.model_dir)
        for model_file in source_path.glob("*.pt"):
            shutil.copy2(model_file, models_path)
            
    async def _backup_configs(self, backup_path: Path):
        """Backup configuration files."""
        config_path = backup_path / "config"
        config_path.mkdir(exist_ok=True)
        
        # Copy config files
        source_path = Path(self.settings.config_dir)
        for config_file in source_path.glob("*.yml"):
            shutil.copy2(config_file, config_path)
            
    async def _create_archive(self, backup_path: Path) -> Path:
        """Create compressed archive of backup."""
        archive_path = self.backup_dir / f"{backup_path.name}.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_path.name)
            
        return archive_path
        
    async def _upload_to_cloud(self, file_path: Path) -> str:
        """Upload backup to cloud storage."""
        try:
            async with self.session.client('s3') as s3:
                key = f"backups/{file_path.name}"
                await s3.upload_file(
                    str(file_path),
                    self.settings.backup_bucket,
                    key
                )
                
                return f"s3://{self.settings.backup_bucket}/{key}"
                
        except Exception as e:
            self.logger.error(f"Upload failed: {str(e)}")
            raise 