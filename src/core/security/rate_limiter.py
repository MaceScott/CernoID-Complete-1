from typing import Dict, Optional, Tuple
import time
import asyncio
from datetime import datetime
import redis.asyncio as redis
import logging
from fastapi import Request, HTTPException, status

class RateLimiter:
    """API rate limiting implementation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redis = redis.Redis.from_url(config['redis_url'])
        self.logger = logging.getLogger('RateLimiter')
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Rate limit configurations
        self._default_limit = config['rate_limiting']['rate']
        self._default_period = config['rate_limiting']['period']
        self._endpoint_limits = config['rate_limiting'].get('endpoints', {})

    async def start(self) -> None:
        """Start rate limiter and cleanup task"""
        try:
            await self.redis.ping()
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_keys())
            self.logger.info("Rate limiter started successfully and connected to Redis")
        except Exception as e:
            self.logger.error(f"Rate limiter start failed: {str(e)}")
            raise

    async def stop(self) -> None:
        """Stop rate limiter"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                self.logger.info("Cleanup task cancelled successfully")
        await self.redis.close()
        self.logger.info("Rate limiter stopped and Redis connection closed")

    async def check_rate_limit(self, request: Request) -> None:
        """Check if request exceeds rate limit"""
        try:
            key = self._generate_key(request)
            limit, period = self._get_limits(request)
            
            # Check current request count
            current_time = time.time()
            window_start = current_time - period
            
            # Remove old requests
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Get current request count
            request_count = await self.redis.zcard(key)
            
            if request_count >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": limit,
                        "period": period,
                        "retry_after": self._calculate_retry_after(key)
                    }
                )
            
            # Add current request
            await self.redis.zadd(key, {str(current_time): current_time})
            await self.redis.expire(key, period)
            
            # Set rate limit headers
            request.state.rate_limit_headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(limit - request_count - 1),
                "X-RateLimit-Reset": str(int(current_time + period))
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {str(e)}")
            raise

    def _generate_key(self, request: Request) -> str:
        """Generate rate limit key"""
        try:
            ip = request.client.host
            endpoint = request.url.path
            key = f"rate_limit:{ip}:{endpoint}"
            self.logger.debug(f"Generated rate limit key: {key}")
            return key
        except Exception as e:
            self.logger.error(f"Failed to generate rate limit key: {str(e)}")
            raise

    def _get_limits(self, request: Request) -> Tuple[int, int]:
        """Get rate limit and period for endpoint"""
        endpoint = request.url.path
        if endpoint in self._endpoint_limits:
            return (
                self._endpoint_limits[endpoint]['rate'],
                self._endpoint_limits[endpoint]['period']
            )
        return self._default_limit, self._default_period

    async def _calculate_retry_after(self, key: str) -> int:
        """Calculate retry after time"""
        oldest_request = await self.redis.zrange(key, 0, 0, withscores=True)
        if not oldest_request:
            return 0
        
        _, timestamp = oldest_request[0]
        return int(timestamp + self._default_period - time.time())

    async def _cleanup_expired_keys(self) -> None:
        """Cleanup expired rate limit keys"""
        while True:
            try:
                # Scan for rate limit keys
                cursor = 0
                while True:
                    cursor, keys = await self.redis.scan(
                        cursor,
                        match="rate_limit:*",
                        count=100
                    )
                    
                    # Remove expired entries
                    current_time = time.time()
                    for key in keys:
                        await self.redis.zremrangebyscore(
                            key,
                            0,
                            current_time - self._default_period
                        )
                        
                    if cursor == 0:
                        break
                        
                await asyncio.sleep(60)  # Run cleanup every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Rate limit cleanup failed: {str(e)}")
                await asyncio.sleep(5)  # Wait before retry 