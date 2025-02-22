from typing import Dict, Any
from contextlib import asynccontextmanager
import asyncio

class ResourceManager:
    """Manage system resources and cleanup"""
    
    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self.logger = self._setup_logger()

    @asynccontextmanager
    async def acquire(self, resource_id: str):
        """Safely acquire and release resources"""
        if resource_id not in self._locks:
            self._locks[resource_id] = asyncio.Lock()
            
        try:
            async with self._locks[resource_id]:
                resource = await self._get_or_create_resource(resource_id)
                yield resource
        finally:
            await self._cleanup_resource(resource_id)

    async def _get_or_create_resource(self, resource_id: str) -> Any:
        """Get existing resource or create new one"""
        if resource_id not in self._resources:
            self._resources[resource_id] = await self._create_resource(resource_id)
        return self._resources[resource_id]

    async def _cleanup_resource(self, resource_id: str) -> None:
        """Cleanup specific resource"""
        if resource_id in self._resources:
            try:
                await self._resources[resource_id].cleanup()
            except Exception as e:
                self.logger.error(f"Resource cleanup failed: {str(e)}") 