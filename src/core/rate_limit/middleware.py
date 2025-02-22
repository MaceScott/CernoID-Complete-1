from typing import Optional, Callable, Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from ..base import BaseComponent
from ..utils.errors import handle_errors

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self,
                 app: ASGIApp,
                 component: BaseComponent,
                 **options):
        super().__init__(app)
        self.component = component
        self.options = options
        self.exclude_paths = options.get('exclude', set())
        self.key_func = options.get('key_func')
        self.limit_func = options.get('limit_func')
        self.error_handler = options.get('error_handler')
        
        # Get rate limiter
        self.limiter = self.component.app.get_component('rate_limiter')
        if not self.limiter:
            raise RuntimeError("Rate limiter component not available")

    async def dispatch(self,
                      request: Request,
                      call_next: Callable) -> Response:
        """Process request with rate limiting"""
        # Check if path should be excluded
        if self._should_exclude(request):
            return await call_next(request)
            
        # Generate rate limit key
        key = await self._get_key(request)
        
        # Get limit rule
        rule = await self._get_limit_rule(request)
        
        # Check rate limit
        is_allowed, info = await self.limiter.check_limit(key, rule)
        
        # Add rate limit headers
        response = await self._handle_request(
            request,
            call_next,
            is_allowed,
            info
        )
        
        self._add_headers(response, info)
        return response

    def _should_exclude(self, request: Request) -> bool:
        """Check if request should be excluded"""
        path = request.url.path
        
        # Check exact matches
        if path in self.exclude_paths:
            return True
            
        # Check patterns
        for pattern in self.exclude_paths:
            if pattern.endswith('*'):
                if path.startswith(pattern[:-1]):
                    return True
                    
        return False

    async def _get_key(self, request: Request) -> str:
        """Get rate limit key for request"""
        if self.key_func:
            return await self.key_func(request)
            
        # Default to IP-based limiting
        return self.limiter.generate_key(request, 'ip')

    async def _get_limit_rule(self,
                            request: Request) -> Optional[str]:
        """Get rate limit rule for request"""
        if self.limit_func:
            return await self.limit_func(request)
            
        # Default limit rule
        if request.state.user:
            return 'api'  # Authenticated requests
        return 'normal'  # Anonymous requests

    async def _handle_request(self,
                            request: Request,
                            call_next: Callable,
                            is_allowed: bool,
                            info: Dict) -> Response:
        """Handle rate limited request"""
        if not is_allowed:
            if self.error_handler:
                return await self.error_handler(request, info)
                
            # Default error response
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers=self._get_headers(info)
            )
            
        return await call_next(request)

    def _add_headers(self,
                    response: Response,
                    info: Dict) -> None:
        """Add rate limit headers to response"""
        headers = self._get_headers(info)
        response.headers.update(headers)

    def _get_headers(self, info: Dict) -> Dict[str, str]:
        """Get rate limit response headers"""
        return {
            'X-RateLimit-Limit': str(info['limit']),
            'X-RateLimit-Remaining': str(info['remaining']),
            'X-RateLimit-Reset': str(info['reset']),
            'X-RateLimit-Window': str(info['window'])
        } 