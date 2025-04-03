from typing import Dict, Optional
import time
import logging
from fastapi import HTTPException
from ..logging.config import LogConfig

logger = LogConfig().get_logger(__name__)

class RateLimiter:
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        block_duration: int = 300
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in window
            window_seconds: Time window in seconds
            block_duration: Duration to block IP in seconds after exceeding limit
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration = block_duration
        self.requests: Dict[str, list] = {}
        self.blocked_ips: Dict[str, float] = {}
        
    def is_rate_limited(self, ip: str) -> bool:
        """
        Check if IP is rate limited.
        
        Args:
            ip: IP address to check
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        current_time = time.time()
        
        # Check if IP is blocked
        if ip in self.blocked_ips:
            if current_time - self.blocked_ips[ip] < self.block_duration:
                logger.warning(f"Blocked IP {ip} attempted access")
                return True
            else:
                del self.blocked_ips[ip]
                
        # Initialize request history for IP
        if ip not in self.requests:
            self.requests[ip] = []
            
        # Remove old requests outside window
        self.requests[ip] = [
            req_time for req_time in self.requests[ip]
            if current_time - req_time < self.window_seconds
        ]
        
        # Check if rate limit exceeded
        if len(self.requests[ip]) >= self.max_requests:
            self.blocked_ips[ip] = current_time
            logger.warning(f"IP {ip} rate limit exceeded")
            return True
            
        # Add current request
        self.requests[ip].append(current_time)
        return False
        
    def get_remaining_requests(self, ip: str) -> Optional[int]:
        """
        Get remaining requests for IP.
        
        Args:
            ip: IP address to check
            
        Returns:
            Optional[int]: Remaining requests or None if blocked
        """
        if ip in self.blocked_ips:
            return None
            
        current_time = time.time()
        if ip not in self.requests:
            return self.max_requests
            
        # Remove old requests
        self.requests[ip] = [
            req_time for req_time in self.requests[ip]
            if current_time - req_time < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(self.requests[ip]))
        
    def reset(self, ip: str) -> None:
        """
        Reset rate limit for IP.
        
        Args:
            ip: IP address to reset
        """
        if ip in self.requests:
            del self.requests[ip]
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            
    def clear(self) -> None:
        """Clear all rate limiting data."""
        self.requests.clear()
        self.blocked_ips.clear()

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(ip: str) -> None:
    """
    Check rate limit for IP and raise exception if exceeded.
    
    Args:
        ip: IP address to check
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    if rate_limiter.is_rate_limited(ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        ) 