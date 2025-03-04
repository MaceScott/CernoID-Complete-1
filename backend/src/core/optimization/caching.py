from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import asyncio

class CacheManager:
    """Efficient caching system"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def get(self, key: str) -> Optional[Any]:
        """Get cached item with TTL check"""
        if key in self._cache:
            if self._is_valid(key):
                return self._cache[key]
            else:
                await self._remove(key)
        return None

    async def set(self, key: str, value: Any) -> None:
        """Set cache item with size management"""
        if len(self._cache) >= self._max_size:
            await self._evict_oldest()
        self._cache[key] = value
        self._timestamps[key] = datetime.now()

    async def _periodic_cleanup(self) -> None:
        """Periodically clean expired items"""
        while True:
            await asyncio.sleep(300)  # Clean every 5 minutes
            await self._cleanup_expired()

    def _is_valid(self, key: str) -> bool:
        """Check if cache item is still valid"""
        if key not in self._timestamps:
            return False
        age = datetime.now() - self._timestamps[key]
        return age.total_seconds() < self._ttl 