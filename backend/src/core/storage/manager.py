"""
Storage management system for handling file operations across different storage backends.
"""

from typing import Dict, Optional, Any, List, Union, BinaryIO
import asyncio
from datetime import datetime
import os
from pathlib import Path
import mimetypes
import importlib
from ..base import BaseComponent
from ..utils.errors import handle_errors

class StorageManager(BaseComponent):
    """Advanced storage management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._drivers: Dict[str, Any] = {}
        self._default = self.config.get('storage.default', 'local')
        self._base_path = Path(self.config.get('storage.base_path', 'storage'))
        self._max_size = self.config.get('storage.max_size', 10 * 1024 * 1024)  # 10MB
        self._allowed_types = self.config.get('storage.allowed_types', ['*/*'])
        self._stats = {
            'uploads': 0,
            'downloads': 0,
            'deletes': 0,
            'errors': 0
        }

    async def initialize(self) -> None:
        """Initialize storage manager"""
        # Create base directory
        self._base_path.mkdir(parents=True, exist_ok=True)
        
        # Load storage configurations
        storages = self.config.get('storage.drivers', {})
        for name, config in storages.items():
            await self.add_driver(name, config)

    async def cleanup(self) -> None:
        """Cleanup storage resources"""
        for driver in self._drivers.values():
            await driver.cleanup()
        self._drivers.clear()

    @handle_errors(logger=None)
    async def add_driver(self,
                        name: str,
                        config: Dict) -> bool:
        """Add storage driver"""
        try:
            # Get driver type
            driver_type = config.get('type', 'local')
            
            # Import driver module
            module = importlib.import_module(
                f".drivers.{driver_type}",
                package="core.storage"
            )
            
            # Create driver
            driver = await module.create_driver(config)
            self._drivers[name] = driver
            
            return True
            
        except Exception as e:
            self.logger.error(f"Driver creation error: {str(e)}")
            return False

    @handle_errors(logger=None)
    async def upload(self,
                    path: str,
                    content: Union[bytes, BinaryIO],
                    driver: Optional[str] = None,
                    **kwargs) -> str:
        """Upload file to storage"""
        try:
            # Get driver
            storage = self._get_driver(driver)
            
            # Validate file
            await self._validate_file(path, content)
            
            # Generate path
            full_path = self._generate_path(path)
            
            # Upload file
            url = await storage.upload(full_path, content, **kwargs)
            
            self._stats['uploads'] += 1
            
            # Emit event
            await self.app.events.emit(
                'storage.uploaded',
                {
                    'path': full_path,
                    'driver': storage.name,
                    'url': url
                }
            )
            
            return url
            
        except Exception as e:
            self.logger.error(f"File upload error: {str(e)}")
            self._stats['errors'] += 1
            raise

    @handle_errors(logger=None)
    async def download(self,
                      path: str,
                      driver: Optional[str] = None) -> bytes:
        """Download file from storage"""
        try:
            # Get driver
            storage = self._get_driver(driver)
            
            # Generate path
            full_path = self._generate_path(path)
            
            # Download file
            content = await storage.download(full_path)
            
            self._stats['downloads'] += 1
            return content
            
        except Exception as e:
            self.logger.error(f"File download error: {str(e)}")
            self._stats['errors'] += 1
            raise

    @handle_errors(logger=None)
    async def delete(self,
                    path: str,
                    driver: Optional[str] = None) -> bool:
        """Delete file from storage"""
        try:
            # Get driver
            storage = self._get_driver(driver)
            
            # Generate path
            full_path = self._generate_path(path)
            
            # Delete file
            success = await storage.delete(full_path)
            
            if success:
                self._stats['deletes'] += 1
                
                # Emit event
                await self.app.events.emit(
                    'storage.deleted',
                    {
                        'path': full_path,
                        'driver': storage.name
                    }
                )
                
            return success
            
        except Exception as e:
            self.logger.error(f"File deletion error: {str(e)}")
            self._stats['errors'] += 1
            return False

    async def exists(self,
                    path: str,
                    driver: Optional[str] = None) -> bool:
        """Check if file exists"""
        try:
            # Get driver
            storage = self._get_driver(driver)
            
            # Generate path
            full_path = self._generate_path(path)
            
            # Check file
            return await storage.exists(full_path)
            
        except Exception as e:
            self.logger.error(f"File check error: {str(e)}")
            return False

    async def get_url(self,
                     path: str,
                     driver: Optional[str] = None) -> str:
        """Get file URL"""
        try:
            # Get driver
            storage = self._get_driver(driver)
            
            # Generate path
            full_path = self._generate_path(path)
            
            # Get URL
            return await storage.get_url(full_path)
            
        except Exception as e:
            self.logger.error(f"URL generation error: {str(e)}")
            raise

    async def get_metadata(self,
                         path: str,
                         driver: Optional[str] = None) -> Dict:
        """Get file metadata"""
        try:
            # Get driver
            storage = self._get_driver(driver)
            
            # Generate path
            full_path = self._generate_path(path)
            
            # Get metadata
            return await storage.get_metadata(full_path)
            
        except Exception as e:
            self.logger.error(f"Metadata retrieval error: {str(e)}")
            raise

    async def list_files(self,
                        path: str = '',
                        driver: Optional[str] = None) -> List[Dict]:
        """List files in directory"""
        try:
            # Get driver
            storage = self._get_driver(driver)
            
            # Generate path
            full_path = self._generate_path(path)
            
            # List files
            return await storage.list_files(full_path)
            
        except Exception as e:
            self.logger.error(f"File listing error: {str(e)}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = self._stats.copy()
        
        # Add driver stats
        stats['drivers'] = {
            name: await driver.get_stats()
            for name, driver in self._drivers.items()
        }
        
        return stats

    def _get_driver(self, name: Optional[str] = None) -> Any:
        """Get storage driver"""
        if name is None:
            name = self._default
            
        if name not in self._drivers:
            raise ValueError(f"Storage driver '{name}' not found")
            
        return self._drivers[name]

    def _generate_path(self, path: str) -> str:
        """Generate full file path"""
        return str(self._base_path / path)

    async def _validate_file(self,
                           path: str,
                           content: Union[bytes, BinaryIO]) -> None:
        """Validate file before upload"""
        # Check file size
        if isinstance(content, bytes):
            size = len(content)
        else:
            content.seek(0, 2)  # Seek to end
            size = content.tell()
            content.seek(0)  # Reset to start
            
        if size > self._max_size:
            raise ValueError(f"File size exceeds maximum allowed size of {self._max_size} bytes")
            
        # Check file type
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type and self._allowed_types != ['*/*']:
            if mime_type not in self._allowed_types:
                raise ValueError(f"File type '{mime_type}' not allowed") 