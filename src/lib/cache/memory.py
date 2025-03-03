from typing import Dict, Optional, Any, List, Union
import asyncio
from datetime import datetime, timedelta
from collections import OrderedDict
from ...base import BaseComponent

class MemoryBackend(BaseComponent):
    """In-memory cache backend"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._data: OrderedDict = OrderedDict()
        self._expires: Dict[str, float] = {}
        self._max_size = self.config.get('cache.max_size', 1000)
        self._stats = {
            'size': 0,
            'evictions': 0
        }

    async def initialize(self) -> None:
        """Initialize memory backend"""
        pass

    async def cleanup(self) -> None:
        """Cleanup backend resources"""
        self._data.clear()
        self._expires.clear()

    async def get(self, key: str) -> Optional[bytes]:
        """Get cached value"""
        try:
            # Check expiration
            if key in self._expires:
                if datetime.utcnow().timestamp() > self._expires[key]:
                    await self.delete(key)
                    return None
                    
            return self._data.get(key)
            
        except Exception as e:
            self.logger.error(f"Memory get error: {str(e)}")
            return None

    async def set(self,
                 key: str,
                 value: bytes,
                 ttl: int) -> bool:
        """Set cached value"""
        try:
            # Check size limit
            if len(self._data) >= self._max_size:
                # Remove oldest entry
                self._data.popitem(last=False)
                self._stats['evictions'] += 1
                
            # Store value
            self._data[key] = value
            self._expires[key] = datetime.utcnow().timestamp() + ttl
            
            # Update stats
            self._stats['size'] = len(self._data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Memory set error: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            self._data.pop(key, None)
            self._expires.pop(key, None)
            
            # Update stats
            self._stats['size'] = len(self._data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Memory delete error: {str(e)}")
            return False

    async def clear(self) -> bool:
        """Clear all cached values"""
        try:
            self._data.clear()
            self._expires.clear()
            
            # Update stats
            self._stats['size'] = 0
            
            return True
            
        except Exception as e:
            self.logger.error(f"Memory clear error: {str(e)}")
            return False

    async def get_many(self,
                      keys: List[str]) -> List[Optional[bytes]]:
        """Get multiple cached values"""
        return [await self.get(key) for key in keys]

    async def set_many(self,
                      mapping: Dict[str, bytes],
                      ttl: int) -> bool:
        """Set multiple cached values"""
        try:
            for key, value in mapping.items():
                await self.set(key, value, ttl)
            return True
            
        except Exception as e:
            self.logger.error(f"Memory set_many error: {str(e)}")
            return False

    async def delete_many(self,
                         keys: List[str]) -> bool:
        """Delete multiple cached values"""
        try:
            for key in keys:
                await self.delete(key)
            return True
            
        except Exception as e:
            self.logger.error(f"Memory delete_many error: {str(e)}")
            return False

    async def cleanup(self) -> None:
        """Cleanup expired entries"""
        try:
            now = datetime.utcnow().timestamp()
            
            # Find expired keys
            expired = [
                key for key, expires in self._expires.items()
                if now > expires
            ]
            
            # Delete expired entries
            for key in expired:
                await self.delete(key)
                
        except Exception as e:
            self.logger.error(f"Memory cleanup error: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        return self._stats.copy() 