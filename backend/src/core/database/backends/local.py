from typing import Dict, Optional, Any, BinaryIO
import asyncio
from pathlib import Path
import shutil
import aiofiles
from ...base import BaseComponent

class LocalBackend(BaseComponent):
    """Local file storage backend"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._base_path = Path(
            self.config.get('storage.local.path', 'storage')
        )
        self._base_url = self.config.get('storage.local.url', '')
        self._create_dirs = self.config.get(
            'storage.local.create_dirs',
            True
        )
        self._stats = {
            'size': 0,
            'files': 0
        }

    async def initialize(self) -> None:
        """Initialize local backend"""
        # Create base directory
        if self._create_dirs:
            self._base_path.mkdir(parents=True, exist_ok=True)
            
        # Calculate initial stats
        await self._update_stats()

    async def cleanup(self) -> None:
        """Cleanup backend resources"""
        pass

    async def upload(self,
                    data: bytes,
                    path: str,
                    bucket: str,
                    content_type: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> Optional[str]:
        """Upload file to local storage"""
        try:
            # Get full path
            full_path = self._get_full_path(path, bucket)
            
            # Create parent directories
            if self._create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
            # Write file
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(data)
                
            # Update stats
            self._stats['size'] += len(data)
            self._stats['files'] += 1
            
            # Return URL
            return self.get_url(path, bucket)
            
        except Exception as e:
            self.logger.error(f"Local upload error: {str(e)}")
            return None

    async def download(self,
                      path: str,
                      bucket: str) -> Optional[bytes]:
        """Download file from local storage"""
        try:
            # Get full path
            full_path = self._get_full_path(path, bucket)
            if not full_path.exists():
                return None
                
            # Read file
            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
                
        except Exception as e:
            self.logger.error(f"Local download error: {str(e)}")
            return None

    async def delete(self,
                    path: str,
                    bucket: str) -> bool:
        """Delete file from local storage"""
        try:
            # Get full path
            full_path = self._get_full_path(path, bucket)
            if not full_path.exists():
                return True
                
            # Delete file
            full_path.unlink()
            
            # Update stats
            size = full_path.stat().st_size
            self._stats['size'] -= size
            self._stats['files'] -= 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Local delete error: {str(e)}")
            return False

    async def exists(self,
                    path: str,
                    bucket: str) -> bool:
        """Check if file exists"""
        try:
            # Get full path
            full_path = self._get_full_path(path, bucket)
            return full_path.exists()
            
        except Exception as e:
            self.logger.error(f"Local exists error: {str(e)}")
            return False

    def get_url(self,
                path: str,
                bucket: str) -> str:
        """Get public URL for file"""
        if not self._base_url:
            return ''
            
        return f"{self._base_url}/{bucket}/{path}"

    async def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        await self._update_stats()
        return self._stats.copy()

    def _get_full_path(self,
                      path: str,
                      bucket: str) -> Path:
        """Get full file path"""
        return self._base_path / bucket / path

    async def _update_stats(self) -> None:
        """Update storage statistics"""
        total_size = 0
        total_files = 0
        
        # Walk directory tree
        for path in self._base_path.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
                total_files += 1
                
        self._stats.update({
            'size': total_size,
            'files': total_files
        }) 