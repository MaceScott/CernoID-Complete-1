"""
Advanced rate limiting middleware with Redis backend.
"""
from typing import Optional, Tuple, Dict, Any
from fastapi import Request, HTTPException, status
import asyncio
import time
import hashlib
from aioredis import Redis  # Removed unused datetime import

from ...utils.config import get_settings
from ...utils.logging import get_logger

class RateLimiter:
    """
    Distributed rate limiter using Redis
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize Redis connection
        self.redis = Redis.from_url(self.settings.redis_url)
        
        # Configure rate limits
        self.rate_limits = {
            "default": (100, 60),  # 100 requests per minute
            "auth": (20, 60),      # 20 auth requests per minute
            "recognition": (50, 60),# 50 recognition requests per minute
            "admin": (200, 60)     # 200 admin requests per minute
        }
        
    async def check_rate_limit(self,
                             request: Request,
                             key: Optional[str] = None,
                             limit_type: str = "default") -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits."""
        try:
            # Get rate limit configuration
            max_requests, window = self.rate_limits.get(
                limit_type,
                self.rate_limits["default"]
            )
            
            # Generate rate limit key
            rate_key = self._generate_key(request, key)
            
            # Get current window
            current_time = int(time.time())
            window_key = f"{rate_key}:{current_time // window}"
            
            # Increment request count
            request_count = await self.redis.incr(window_key)
            
            # Set expiration if first request in window
            if request_count == 1:
                await self.redis.expire(window_key, window)
                
            # Get remaining window time
            ttl = await self.redis.ttl(window_key)
            
            # Check if limit exceeded
            if request_count > max_requests:
                return False, {
                    "limit": max_requests,
                    "remaining": 0,
                    "reset": ttl,
                    "window": window
                }
                
            return True, {
                "limit": max_requests,
                "remaining": max_requests - request_count,
                "reset": ttl,
                "window": window
            }
            
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {str(e)}")
            return True, {}  # Allow request on error
            
    def _generate_key(self, request: Request, key: Optional[str] = None) -> str:
        """Generate rate limit key."""
        if key:
            base_key = key
        else:
            # Use IP address and path as default key
            ip = request.client.host
            path = request.url.path
            base_key = f"{ip}:{path}"
            
        # Hash the key
        return hashlib.sha256(base_key.encode()).hexdigest()
        
    async def cleanup(self):
        """Simplified cleanup."""
        await self.redis.close()  # Removed redundant try/except

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    try:
        # Determine limit type based on path
        path = request.url.path
        limit_type = "default"
        
        if path.startswith("/auth"):
            limit_type = "auth"
        elif path.startswith("/recognition"):
            limit_type = "recognition"
        elif path.startswith("/admin"):
            limit_type = "admin"
            
        # Check rate limit
        allowed, info = await rate_limiter.check_rate_limit(
            request,
            limit_type=limit_type
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "info": info
                }
            )
            
        # Add rate limit info to response headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info.get("limit", ""))
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", ""))
        response.headers["X-RateLimit-Reset"] = str(info.get("reset", ""))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limit middleware error: {str(e)}")
        return await call_next(request) 