from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import shutil
from pathlib import Path
import logging
import boto3
import aiofiles
from dataclasses import dataclass
import json
import gzip

@dataclass
class BackupMetadata:
    """Backup metadata information"""
    backup_id: str
    timestamp: datetime
    type: str
    size: int
    checksum: str
    components: List[str]
    status: str

class BackupManager:
    """System backup and recovery management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('BackupManager')
        self.backup_dir = Path(config['backup_dir'])
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.s3_client = boto3.client('s3')
        self._backup_tasks: Dict[str, asyncio.Task] = {}
        self._metadata: Dict[str, BackupMetadata] = {}
        self._load_metadata()

    async def create_backup(self, 
                          components: List[str],
                          backup_type: str = "full") -> str:
        """Create new system backup"""
        try:
            # Generate backup ID
            backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir()
            
            # Start backup task
            task = asyncio.create_task(
                self._backup_components(backup_id, backup_path, components)
            )
            self._backup_tasks[backup_id] = task
            
            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=datetime.utcnow(),
                type=backup_type,
                size=0,
                checksum="",
                components=components,
                status="in_progress"
            )
            self._metadata[backup_id] = metadata
            
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            raise

    async def restore_backup(self, 
                           backup_id: str,
                           components: Optional[List[str]] = None) -> None:
        """Restore system from backup"""
        try:
            if backup_id not in self._metadata:
                raise ValueError(f"Backup not found: {backup_id}")
                
            metadata = self._metadata[backup_id]
            backup_path = self.backup_dir / backup_id
            
            # Verify backup integrity
            if not await self._verify_backup(backup_id):
                raise ValueError(f"Backup integrity check failed: {backup_id}")
                
            # Restore components
            components_to_restore = components or metadata.components
            for component in components_to_restore:
                await self._restore_component(backup_path, component)
                
            self.logger.info(f"Restored backup: {backup_id}")
            
        except Exception as e:
            self.logger.error(f"Backup restoration failed: {str(e)}")
            raise

    async def get_backup_status(self, backup_id: str) -> Dict:
        """Get backup status and information"""
        if backup_id not in self._metadata:
            raise ValueError(f"Backup not found: {backup_id}")
            
        metadata = self._metadata[backup_id]
        task = self._backup_tasks.get(backup_id)
        
        return {
            "backup_id": backup_id,
            "status": metadata.status,
            "timestamp": metadata.timestamp.isoformat(),
            "type": metadata.type,
            "size": metadata.size,
            "components": metadata.components,
            "in_progress": task is not None and not task.done()
        }

    async def _backup_components(self,
                               backup_id: str,
                               backup_path: Path,
                               components: List[str]) -> None:
        """Backup system components"""
        try:
            total_size = 0
            
            for component in components:
                component_size = await self._backup_component(
                    backup_path, component
                )
                total_size += component_size
                
            # Update metadata
            metadata = self._metadata[backup_id]
            metadata.size = total_size
            metadata.status = "completed"
            metadata.checksum = await self._calculate_backup_checksum(backup_path)
            
            # Upload to S3
            await self._upload_to_s3(backup_id)
            
            # Cleanup local backup
            if self.config.get('cleanup_local', True):
                shutil.rmtree(backup_path)
                
            self._save_metadata()
            self.logger.info(f"Completed backup: {backup_id}")
            
        except Exception as e:
            self._metadata[backup_id].status = "failed"
            self._save_metadata()
            raise

    async def _backup_component(self, backup_path: Path, component: str) -> int:
        """Backup individual component"""
        component_path = backup_path / component
        component_path.mkdir()
        
        if component == "database":
            return await self._backup_database(component_path)
        elif component == "files":
            return await self._backup_files(component_path)
        elif component == "models":
            return await self._backup_models(component_path)
        else:
            raise ValueError(f"Unknown component: {component}")

    async def _restore_component(self, backup_path: Path, component: str) -> None:
        """Restore individual component"""
        component_path = backup_path / component
        
        if not component_path.exists():
            raise ValueError(f"Component not found in backup: {component}")
            
        if component == "database":
            await self._restore_database(component_path)
        elif component == "files":
            await self._restore_files(component_path)
        elif component == "models":
            await self._restore_models(component_path)
        else:
            raise ValueError(f"Unknown component: {component}")

    async def _upload_to_s3(self, backup_id: str) -> None:
        """Upload backup to S3"""
        backup_path = self.backup_dir / backup_id
        s3_key = f"backups/{backup_id}"
        
        # Create backup archive
        archive_path = backup_path.with_suffix('.tar.gz')
        shutil.make_archive(
            str(backup_path),
            'gztar',
            str(backup_path)
        )
        
        # Upload to S3
        self.s3_client.upload_file(
            str(archive_path),
            self.config['s3_bucket'],
            s3_key
        )
        
        # Cleanup archive
        archive_path.unlink()

    def _load_metadata(self) -> None:
        """Load backup metadata"""
        metadata_file = self.backup_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                self._metadata = {
                    k: BackupMetadata(**v) for k, v in data.items()
                }

    def _save_metadata(self) -> None:
        """Save backup metadata"""
        metadata_file = self.backup_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            data = {
                k: v.__dict__ for k, v in self._metadata.items()
            }
            json.dump(data, f, default=str) 