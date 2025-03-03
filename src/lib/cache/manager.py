from typing import Dict, Optional, Any, Union, List, Callable, Set
import asyncio
import time
from datetime import datetime, timedelta
import logging
import json
import hashlib
import pickle
from ..base import BaseComponent
from ..connections.redis import RedisPool
from ..utils.errors import handle_errors

@dataclass
class CacheConfig:
    """Cache configuration"""
    backend: str
    url: str
    default_ttl: int
    max_size: Optional[int] = None
    enable_stats: bool = True
    compression: bool = False
    serializer: str = "json"

class CacheManager(BaseComponent):
    """Advanced caching system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._backend = None
        self._prefix = self.config.get('cache.prefix', 'cache:')
        self._default_ttl = self.config.get('cache.ttl', 3600)
        self._serializer = self.config.get('cache.serializer', 'json')
        self._namespace = self.config.get('cache.namespace', '')
        self._tags: Dict[str, Set[str]] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        self._redis: Optional[RedisPool] = None
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        
        # Cache configuration
        self._enable_local = self.config.get('cache.enable_local', True)
        self._enable_redis = self.config.get('cache.enable_redis', True)
        self._compression = self.config.get('cache.compression', False)
        self._max_size = self.config.get('cache.max_size', 1000)

    async def initialize(self) -> None:
        """Initialize cache manager"""
        # Initialize backend
        backend = self.config.get('cache.backend', 'memory')
        
        if backend == 'redis':
            from .backends.redis import RedisBackend
            self._backend = RedisBackend(self.config)
        elif backend == 'memcached':
            from .backends.memcached import MemcachedBackend
            self._backend = MemcachedBackend(self.config)
        else:
            from .backends.memory import MemoryBackend
            self._backend = MemoryBackend(self.config)
            
        await self._backend.initialize()
        
        if self._enable_redis:
            self._redis = RedisPool(self.config)
            await self._redis.initialize()
            
        # Start cleanup task
        if backend == 'memory':
            asyncio.create_task(self._cleanup_task())

    async def cleanup(self) -> None:
        """Cleanup cache resources"""
        if self._backend:
            await self._backend.cleanup()
        if self._redis:
            await self._redis.cleanup()
        self._tags.clear()
        self._local_cache.clear()
        self._locks.clear()

    @handle_errors(logger=None)
    async def get(self,
                 key: str,
                 default: Any = None) -> Any:
        """Get cached value"""
        full_key = self._get_key(key)
        
        # Get from backend
        value = await self._backend.get(full_key)
        
        if value is None:
            self._stats['misses'] += 1
            return default
            
        # Deserialize value
        try:
            value = self._deserialize(value)
            self._stats['hits'] += 1
            return value
        except Exception as e:
            self.logger.error(f"Cache deserialization error: {str(e)}")
            return default

    @handle_errors(logger=None)
    async def set(self,
                 key: str,
                 value: Any,
                 ttl: Optional[int] = None,
                 tags: Optional[List[str]] = None) -> bool:
        """Set cached value"""
        full_key = self._get_key(key)
        
        # Serialize value
        try:
            data = self._serialize(value)
        except Exception as e:
            self.logger.error(f"Cache serialization error: {str(e)}")
            return False
            
        # Set in backend
        ttl = ttl if ttl is not None else self._default_ttl
        success = await self._backend.set(full_key, data, ttl)
        
        if success:
            self._stats['sets'] += 1
            
            # Update tags
            if tags:
                for tag in tags:
                    if tag not in self._tags:
                        self._tags[tag] = set()
                    self._tags[tag].add(key)
                    
        return success

    @handle_errors(logger=None)
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        full_key = self._get_key(key)
        success = await self._backend.delete(full_key)
        
        if success:
            self._stats['deletes'] += 1
            
            # Remove from tags
            for tag_keys in self._tags.values():
                tag_keys.discard(key)
                
        return success

    @handle_errors(logger=None)
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        full_key = self._get_key(key)
        return await self._backend.exists(full_key)

    @handle_errors(logger=None)
    async def clear(self) -> bool:
        """Clear all cached values"""
        success = await self._backend.clear()
        if success:
            self._tags.clear()
        return success

    @handle_errors(logger=None)
    async def get_many(self,
                      keys: List[str],
                      default: Any = None) -> Dict[str, Any]:
        """Get multiple cached values"""
        full_keys = [self._get_key(k) for k in keys]
        values = await self._backend.get_many(full_keys)
        
        result = {}
        for key, value in zip(keys, values):
            if value is None:
                self._stats['misses'] += 1
                result[key] = default
            else:
                try:
                    result[key] = self._deserialize(value)
                    self._stats['hits'] += 1
                except Exception:
                    result[key] = default
                    
        return result

    @handle_errors(logger=None)
    async def set_many(self,
                      mapping: Dict[str, Any],
                      ttl: Optional[int] = None,
                      tags: Optional[List[str]] = None) -> bool:
        """Set multiple cached values"""
        data = {}
        for key, value in mapping.items():
            try:
                data[self._get_key(key)] = self._serialize(value)
            except Exception as e:
                self.logger.error(
                    f"Cache serialization error for {key}: {str(e)}"
                )
                return False
                
        ttl = ttl if ttl is not None else self._default_ttl
        success = await self._backend.set_many(data, ttl)
        
        if success:
            self._stats['sets'] += len(mapping)
            
            # Update tags
            if tags:
                for tag in tags:
                    if tag not in self._tags:
                        self._tags[tag] = set()
                    self._tags[tag].update(mapping.keys())
                    
        return success

    @handle_errors(logger=None)
    async def delete_many(self, keys: List[str]) -> bool:
        """Delete multiple cached values"""
        full_keys = [self._get_key(k) for k in keys]
        success = await self._backend.delete_many(full_keys)
        
        if success:
            self._stats['deletes'] += len(keys)
            
            # Remove from tags
            for tag_keys in self._tags.values():
                tag_keys.difference_update(keys)
                
        return success

    @handle_errors(logger=None)
    async def get_by_tag(self,
                        tag: str,
                        default: Any = None) -> Dict[str, Any]:
        """Get all values by tag"""
        if tag not in self._tags:
            return {}
            
        return await self.get_many(
            list(self._tags[tag]),
            default
        )

    @handle_errors(logger=None)
    async def delete_by_tag(self, tag: str) -> bool:
        """Delete all values by tag"""
        if tag not in self._tags:
            return True
            
        keys = list(self._tags[tag])
        success = await self.delete_many(keys)
        
        if success:
            del self._tags[tag]
            
        return success

    def _get_key(self, key: str) -> str:
        """Get full cache key"""
        parts = [self._prefix]
        
        if self._namespace:
            parts.append(self._namespace)
            
        parts.append(key)
        return ':'.join(parts)

    def _serialize(self, value: Any) -> Union[str, bytes]:
        """Serialize value"""
        if self._serializer == 'pickle':
            return pickle.dumps(value)
        else:
            return json.dumps(value)

    def _deserialize(self, value: Union[str, bytes]) -> Any:
        """Deserialize value"""
        if self._serializer == 'pickle':
            return pickle.loads(value)
        else:
            return json.loads(value)

    async def _cleanup_task(self) -> None:
        """Cleanup expired cache entries"""
        while True:
            try:
                await self._backend.cleanup()
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {str(e)}")
                await asyncio.sleep(60)

    def generate_key(self,
                    *args,
                    **kwargs) -> str:
        """Generate cache key from arguments"""
        # Create key components
        key_parts = [str(arg) for arg in args]
        key_parts.extend(
            f"{k}:{v}" for k, v in sorted(kwargs.items())
        )
        
        # Generate hash
        key = hashlib.md5(
            ':'.join(key_parts).encode()
        ).hexdigest()
        
        return key

    def _make_key(self, key: str) -> str:
        """Create namespaced cache key"""
        return f"{self._namespace}:{key}"

    def _get_local(self, key: str) -> Optional[Any]:
        """Get value from local cache"""
        if key not in self._local_cache:
            return None
            
        entry = self._local_cache[key]
        if entry['expires'] < datetime.utcnow():
            del self._local_cache[key]
            return None
            
        return entry['value']

    async def _set_local(self,
                        key: str,
                        value: Any,
                        ttl: int = None) -> None:
        """Set value in local cache"""
        # Ensure cache size limit
        if len(self._local_cache) >= self._max_size:
            # Remove oldest entry
            oldest = min(
                self._local_cache.items(),
                key=lambda x: x[1]['expires']
            )
            del self._local_cache[oldest[0]]
            
        self._local_cache[key] = {
            'value': value,
            'expires': datetime.utcnow() + timedelta(seconds=ttl or self._default_ttl)
        }

    async def _get_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        value = await self._redis.execute('get', self._make_key(key))
        return json.loads(value) if value else None

    async def _set_redis(self,
                        key: str,
                        value: Any,
                        ttl: int) -> None:
        """Set value in Redis cache"""
        await self._redis.execute(
            'setex',
            self._make_key(key),
            ttl,
            json.dumps(value)
        )

    async def get_or_set(self,
                        key: str,
                        func: callable,
                        ttl: Optional[int] = None) -> Any:
        """Get cached value or compute and cache it"""
        # Get lock for key
        lock = self._locks.setdefault(key, asyncio.Lock())
        
        async with lock:
            # Try to get from cache
            value = await self.get(key)
            if value is not None:
                return value
                
            # Compute value
            value = await func()
            
            # Cache value
            await self.set(key, value, ttl)
            return value

    async def _cleanup_local_cache(self) -> None:
        """Cleanup expired local cache entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                now = datetime.utcnow()
                
                # Remove expired entries
                expired = [
                    key for key, entry in self._local_cache.items()
                    if entry['expires'] < now
                ]
                
                for key in expired:
                    del self._local_cache[key]
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cache cleanup failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.config.enable_stats:
            return {}
            
        try:
            redis_info = await self._redis.info()
            
            stats = {
                "local_cache_size": len(self._local_cache),
                "redis_memory_used": redis_info["used_memory"],
                "redis_hits": redis_info["keyspace_hits"],
                "redis_misses": redis_info["keyspace_misses"],
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {str(e)}")
            return {} 