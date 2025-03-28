from typing import Dict, Optional, Union, Tuple, List, Any
import asyncio
import time
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import aioredis
from collections import defaultdict
from ..base import BaseComponent
from ..connections.redis import RedisPool
from ..utils.decorators import handle_errors
import hashlib
from fastapi import Request, Response

@dataclass
class RateLimit:
    """Rate limit configuration"""
    name: str
    limit: int
    window: int  # in seconds
    strategy: str = "fixed"  # fixed, sliding, or token
    burst: Optional[int] = None
    namespace: Optional[str] = None

class RateLimiter(BaseComponent):
    """Advanced rate limiting system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._redis: Optional[RedisPool] = None
        self._local_limits: Dict[str, Dict] = {}
        self._storage: Dict[str, List[float]] = {}
        self._default_limit = self.config.get('rate_limit.default', 60)
        self._default_window = self.config.get('rate_limit.window', 60)
        self._cleanup_interval = self.config.get(
            'rate_limit.cleanup_interval',
            300
        )
        
        # Initialize default limits
        self._setup_default_limits()

    async def initialize(self) -> None:
        """Initialize rate limiter"""
        if self._enable_redis:
            self._redis = RedisPool(self.config)
            await self._redis.initialize()
            
        # Start cleanup task
        self.add_cleanup_task(
            asyncio.create_task(self._cleanup_local_limits())
        )
        self.add_cleanup_task(
            asyncio.create_task(self._cleanup_storage())
        )

    async def cleanup(self) -> None:
        """Cleanup rate limiter resources"""
        if self._redis:
            await self._redis.cleanup()
        self._local_limits.clear()
        self._storage.clear()

    @handle_errors(logger=None)
    async def check_limit(self,
                         key: str,
                         rule: Optional[str] = None) -> Tuple[bool, Dict]:
        """Check rate limit for key"""
        # Get limit rule
        limit_rule = self._limits.get(
            rule,
            {
                'limit': self._default_limit,
                'window': self._default_window
            }
        )
        
        # Get current window
        now = time.time()
        window_start = now - limit_rule['window']
        
        # Clean old requests
        if key in self._storage:
            self._storage[key] = [
                ts for ts in self._storage[key]
                if ts > window_start
            ]
        else:
            self._storage[key] = []
            
        # Check limit
        current_count = len(self._storage[key])
        is_allowed = current_count < limit_rule['limit']
        
        # Add request timestamp if allowed
        if is_allowed:
            self._storage[key].append(now)
            
        # Calculate reset time
        if current_count > 0:
            reset_time = self._storage[key][0] + limit_rule['window']
        else:
            reset_time = now + limit_rule['window']
            
        return is_allowed, {
            'limit': limit_rule['limit'],
            'remaining': max(0, limit_rule['limit'] - current_count),
            'reset': int(reset_time),
            'window': limit_rule['window']
        }

    async def get_limits(self,
                        key: str) -> Dict[str, Any]:
        """Get current limits for key"""
        limits = {}
        for rule, limit_rule in self._limits.items():
            is_allowed, info = await self.check_limit(key, rule)
            limits[rule] = info
            
        return limits

    def generate_key(self,
                    request: Request,
                    key_type: str = 'ip') -> str:
        """Generate rate limit key from request"""
        if key_type == 'ip':
            key = request.client.host
        elif key_type == 'user':
            key = str(request.state.user.get('id', 'anonymous'))
        elif key_type == 'endpoint':
            key = f"{request.method}:{request.url.path}"
        else:
            key = request.client.host
            
        return hashlib.md5(key.encode()).hexdigest()

    def _setup_default_limits(self) -> None:
        """Setup default rate limit rules"""
        defaults = {
            'strict': {'limit': 30, 'window': 60},
            'normal': {'limit': 60, 'window': 60},
            'relaxed': {'limit': 120, 'window': 60},
            'api': {'limit': 1000, 'window': 3600}
        }
        
        for name, rule in defaults.items():
            self.add_limit(name, rule['limit'], rule['window'])

    async def _cleanup_local_limits(self) -> None:
        """Cleanup expired local rate limits"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                now = datetime.utcnow()
                
                # Remove expired entries
                expired = [
                    key for key, entry in self._local_limits.items()
                    if entry['expires'] < now
                ]
                
                for key in expired:
                    del self._local_limits[key]
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Rate limit cleanup failed: {str(e)}")

    async def _cleanup_storage(self) -> None:
        """Cleanup expired rate limit data"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                now = time.time()
                max_window = max(
                    rule['window']
                    for rule in self._limits.values()
                )
                
                # Remove expired entries
                expired = []
                for key, timestamps in self._storage.items():
                    valid_timestamps = [
                        ts for ts in timestamps
                        if ts > now - max_window
                    ]
                    
                    if valid_timestamps:
                        self._storage[key] = valid_timestamps
                    else:
                        expired.append(key)
                        
                # Remove empty keys
                for key in expired:
                    del self._storage[key]
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Rate limit cleanup failed: {str(e)}"
                )
                await asyncio.sleep(60)

    def add_limit(self,
                 name: str,
                 limit: int,
                 window: int = 60) -> None:
        """Add rate limit rule"""
        self._limits[name] = {
            'limit': limit,
            'window': window
        }

    @handle_errors(logger=None)
    async def increment(self,
                       key: str,
                       limit: int,
                       window: int) -> Dict:
        """Increment rate limit counter"""
        now = datetime.utcnow()
        
        # Increment local counter
        if self._enable_local:
            self._increment_local(key, limit, window, now)
            
        # Increment Redis counter
        if self._enable_redis and self._redis:
            return await self._increment_redis(key, limit, window)
            
        return {
            'remaining': limit - 1,
            'reset': int(time.time()) + window
        }

    def _check_local_limit(self,
                          key: str,
                          limit: int,
                          window: int) -> Tuple[bool, Dict]:
        """Check local rate limit"""
        now = datetime.utcnow()
        if key not in self._local_limits:
            return False, {
                'remaining': limit,
                'reset': int(time.time()) + window
            }
            
        entry = self._local_limits[key]
        if entry['expires'] < now:
            del self._local_limits[key]
            return False, {
                'remaining': limit,
                'reset': int(time.time()) + window
            }
            
        remaining = limit - entry['count']
        return remaining <= 0, {
            'remaining': max(0, remaining),
            'reset': int(entry['expires'].timestamp())
        }

    async def _check_redis_limit(self,
                                key: str,
                                limit: int,
                                window: int) -> Tuple[bool, Dict]:
        """Check Redis rate limit"""
        redis_key = self._make_key(key)
        count = await self._redis.execute('get', redis_key) or 0
        count = int(count)
        
        ttl = await self._redis.execute('ttl', redis_key)
        if ttl < 0:
            return False, {
                'remaining': limit,
                'reset': int(time.time()) + window
            }
            
        remaining = limit - count
        return remaining <= 0, {
            'remaining': max(0, remaining),
            'reset': int(time.time()) + ttl
        }

    def _increment_local(self,
                        key: str,
                        limit: int,
                        window: int,
                        now: datetime) -> None:
        """Increment local rate limit counter"""
        if key not in self._local_limits:
            self._local_limits[key] = {
                'count': 1,
                'expires': now + timedelta(seconds=window)
            }
        else:
            entry = self._local_limits[key]
            if entry['expires'] < now:
                entry['count'] = 1
                entry['expires'] = now + timedelta(seconds=window)
            else:
                entry['count'] += 1

    async def _increment_redis(self,
                             key: str,
                             limit: int,
                             window: int) -> Dict:
        """Increment Redis rate limit counter"""
        redis_key = self._make_key(key)
        pipe = self._redis.pipeline()
        
        # Increment counter
        pipe.incr(redis_key)
        pipe.expire(redis_key, window)
        
        count, _ = await pipe.execute()
        
        remaining = limit - count
        return {
            'remaining': max(0, remaining),
            'reset': int(time.time()) + window
        }

    def _make_key(self, key: str) -> str:
        """Create namespaced rate limit key"""
        return f"{self._namespace}:{key}"

    async def check_rate_limit(self,
                             rate_limit: RateLimit,
                             key: str) -> Tuple[bool, Dict]:
        """Check if request is within rate limit"""
        try:
            limit_key = self._build_key(rate_limit, key)
            
            if rate_limit.strategy == "token":
                return await self._check_token_bucket(rate_limit, limit_key)
            elif rate_limit.strategy == "sliding":
                return await self._check_sliding_window(rate_limit, limit_key)
            else:  # fixed window
                return await self._check_fixed_window(rate_limit, limit_key)
                
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {str(e)}")
            return True, {}  # Allow request on error

    async def reset_limit(self,
                         rate_limit: RateLimit,
                         key: str) -> None:
        """Reset rate limit for key"""
        try:
            limit_key = self._build_key(rate_limit, key)
            
            # Clear Redis data
            await self._redis.execute('delete', limit_key)
            
            # Clear local cache
            if limit_key in self._local_limits:
                del self._local_limits[limit_key]
                
            self.logger.info(f"Reset rate limit for {limit_key}")
            
        except Exception as e:
            self.logger.error(f"Rate limit reset failed: {str(e)}")

    async def _check_fixed_window(self,
                                rate_limit: RateLimit,
                                key: str) -> Tuple[bool, Dict]:
        """Check fixed window rate limit"""
        try:
            now = int(time.time())
            window_start = now - (now % rate_limit.window)
            
            # Get current count
            count = await self._redis.execute('get', f"{key}:{window_start}")
            count = int(count) if count else 0
            
            if count >= rate_limit.limit:
                return False, {
                    "limit": rate_limit.limit,
                    "remaining": 0,
                    "reset": window_start + rate_limit.window,
                    "window": rate_limit.window
                }
                
            # Increment counter
            await self._redis.execute('incrby', f"{key}:{window_start}", 1)
            await self._redis.execute('expire', f"{key}:{window_start}", rate_limit.window)
            
            return True, {
                "limit": rate_limit.limit,
                "remaining": rate_limit.limit - (count + 1),
                "reset": window_start + rate_limit.window,
                "window": rate_limit.window
            }
            
        except Exception as e:
            self.logger.error(f"Fixed window check failed: {str(e)}")
            return True, {}

    async def _check_sliding_window(self,
                                  rate_limit: RateLimit,
                                  key: str) -> Tuple[bool, Dict]:
        """Check sliding window rate limit"""
        try:
            now = time.time()
            window_start = now - rate_limit.window
            
            # Remove old entries
            await self._redis.execute('zremrangebyscore', key, '-inf', window_start)
            
            # Get current count
            count = await self._redis.execute('zcard', key)
            
            if count >= rate_limit.limit:
                oldest = await self._redis.execute('zrange', key, 0, 0, withscores=True)
                if oldest:
                    reset_time = oldest[0][1] + rate_limit.window
                else:
                    reset_time = now + rate_limit.window
                    
                return False, {
                    "limit": rate_limit.limit,
                    "remaining": 0,
                    "reset": reset_time,
                    "window": rate_limit.window
                }
                
            # Add new request
            await self._redis.execute('zadd', key, now, f"{now}:{count}")
            await self._redis.execute('expire', key, rate_limit.window * 2)
            
            return True, {
                "limit": rate_limit.limit,
                "remaining": rate_limit.limit - (count + 1),
                "reset": now + rate_limit.window,
                "window": rate_limit.window
            }
            
        except Exception as e:
            self.logger.error(f"Sliding window check failed: {str(e)}")
            return True, {}

    async def _check_token_bucket(self,
                                rate_limit: RateLimit,
                                key: str) -> Tuple[bool, Dict]:
        """Check token bucket rate limit"""
        try:
            now = time.time()
            bucket = self._local_limits.get(key)
            
            if not bucket:
                # Initialize bucket
                bucket = {
                    "tokens": rate_limit.limit,
                    "last_update": now,
                    "rate": rate_limit.limit / rate_limit.window
                }
                self._local_limits[key] = bucket
            else:
                # Refill tokens
                time_passed = now - bucket["last_update"]
                new_tokens = time_passed * bucket["rate"]
                bucket["tokens"] = min(
                    rate_limit.limit,
                    bucket["tokens"] + new_tokens
                )
                bucket["last_update"] = now
                
            if bucket["tokens"] < 1:
                time_to_next = (1 - bucket["tokens"]) / bucket["rate"]
                return False, {
                    "limit": rate_limit.limit,
                    "remaining": 0,
                    "reset": now + time_to_next,
                    "window": rate_limit.window
                }
                
            # Consume token
            bucket["tokens"] -= 1
            
            return True, {
                "limit": rate_limit.limit,
                "remaining": int(bucket["tokens"]),
                "reset": now + (1 / bucket["rate"]),
                "window": rate_limit.window
            }
            
        except Exception as e:
            self.logger.error(f"Token bucket check failed: {str(e)}")
            return True, {}

    def _build_key(self, rate_limit: RateLimit, key: str) -> str:
        """Build rate limit key"""
        if rate_limit.namespace:
            return f"ratelimit:{rate_limit.namespace}:{rate_limit.name}:{key}"
        return f"ratelimit:{rate_limit.name}:{key}" 