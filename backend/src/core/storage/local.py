"""
Local filesystem storage implementation with advanced features.
"""
from typing import Dict, Optional, Any, List, Union, BinaryIO
import asyncio
from datetime import datetime
import os
from pathlib import Path
import shutil
import aiofiles
import mimetypes
from ...base import BaseComponent

class LocalStorage(BaseComponent):
    """Local filesystem storage with advanced features"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = 'local'
        self._base_path = Path(config.get('path', 'storage'))
        self._base_url = config.get('url', '/storage')
        self._permissions = config.get('permissions', 0o644)
        self._stats = {
            'files': 0,
            'size': 0
        }

    async def initialize(self) -> None:
        """Initialize local storage"""
        # Create base directory
        self._base_path.mkdir(parents=True, exist_ok=True)
        
        # Update stats
        await self._update_stats()

    async def cleanup(self) -> None:
        """Cleanup storage resources"""
        pass

    async def upload(self,
                    path: str,
                    content: Union[bytes, BinaryIO],
                    **kwargs) -> str:
        """Upload file"""
        try:
            # Generate file path
            file_path = self._base_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            async with aiofiles.open(file_path, 'wb') as f:
                if isinstance(content, bytes):
                    await f.write(content)
                else:
                    # Copy file object
                    content.seek(0)
                    while chunk := content.read(8192):
                        await f.write(chunk)
                        
            # Set permissions
            os.chmod(file_path, self._permissions)
            
            # Update stats
            await self._update_stats()
            
            return self.get_url(path)
            
        except Exception as e:
            self.logger.error(f"Local upload error: {str(e)}")
            raise

    async def download(self, path: str) -> bytes:
        """Download file"""
        try:
            file_path = self._base_path / path
            
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
                
        except Exception as e:
            self.logger.error(f"Local download error: {str(e)}")
            raise

    async def delete(self, path: str) -> bool:
        """Delete file"""
        try:
            file_path = self._base_path / path
            
            if file_path.exists():
                file_path.unlink()
                
                # Cleanup empty directories
                self._cleanup_dirs(file_path.parent)
                
                # Update stats
                await self._update_stats()
                
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Local delete error: {str(e)}")
            return False

    async def exists(self, path: str) -> bool:
        """Check if file exists"""
        file_path = self._base_path / path
        return file_path.exists()

    def get_url(self, path: str) -> str:
        """Get file URL"""
        return f"{self._base_url}/{path}"

    async def get_metadata(self, path: str) -> Dict:
        """Get file metadata"""
        try:
            file_path = self._base_path / path
            stats = file_path.stat()
            
            return {
                'name': file_path.name,
                'path': str(file_path.relative_to(self._base_path)),
                'size': stats.st_size,
                'created_at': datetime.fromtimestamp(stats.st_ctime),
                'modified_at': datetime.fromtimestamp(stats.st_mtime),
                'mime_type': self._get_mime_type(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"Local metadata error: {str(e)}")
            raise

    async def list_files(self, path: str = '') -> List[Dict]:
        """List files in directory"""
        try:
            dir_path = self._base_path / path
            files = []
            
            for item in dir_path.rglob('*'):
                if item.is_file():
                    files.append(
                        await self.get_metadata(
                            str(item.relative_to(self._base_path))
                        )
                    )
                    
            return files
            
        except Exception as e:
            self.logger.error(f"Local list error: {str(e)}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return self._stats.copy()

    def _cleanup_dirs(self, path: Path) -> None:
        """Cleanup empty directories"""
        try:
            while path != self._base_path:
                if not any(path.iterdir()):
                    path.rmdir()
                path = path.parent
        except Exception:
            pass

    def _get_mime_type(self, path: Path) -> str:
        """Get file MIME type"""
        mime_type, _ = mimetypes.guess_type(str(path))
        return mime_type or 'application/octet-stream'

    async def _update_stats(self) -> None:
        """Update storage statistics"""
        try:
            files = 0
            size = 0
            
            for item in self._base_path.rglob('*'):
                if item.is_file():
                    files += 1
                    size += item.stat().st_size
                    
            self._stats.update({
                'files': files,
                'size': size
            })
            
        except Exception as e:
            self.logger.error(f"Stats update error: {str(e)}") 