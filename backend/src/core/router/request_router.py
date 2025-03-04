from typing import Dict, List, Optional, Any, Callable
import asyncio
from datetime import datetime
import logging
from dataclasses import dataclass
import re
from urllib.parse import urlparse, parse_qs
import json
from fastapi import Request, Response
from fastapi.routing import APIRoute
import aiohttp

@dataclass
class RouteConfig:
    """Route configuration"""
    path: str
    methods: List[str]
    service: str
    timeout: float = 30.0
    retry_count: int = 3
    cache_ttl: Optional[int] = None
    rate_limit: Optional[Dict] = None
    transform: Optional[Callable] = None
    middleware: List[Callable] = None

class RequestRouter:
    """Advanced request routing system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('RequestRouter')
        self._routes: Dict[str, RouteConfig] = {}
        self._cache: Dict[str, Dict] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._middleware_stack: List[Callable] = []

    async def initialize(self) -> None:
        """Initialize request router"""
        try:
            self._session = aiohttp.ClientSession()
            
            # Start cache cleanup
            self._cleanup_task = asyncio.create_task(
                self._cleanup_cache()
            )
            
            self.logger.info("Request router initialized")
            
        except Exception as e:
            self.logger.error(f"Request router initialization failed: {str(e)}")
            raise

    def add_route(self, route: RouteConfig) -> None:
        """Add route configuration"""
        try:
            route_key = f"{route.path}:{','.join(route.methods)}"
            self._routes[route_key] = route
            self.logger.info(f"Added route: {route_key}")
            
        except Exception as e:
            self.logger.error(f"Route addition failed: {str(e)}")
            raise

    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the stack"""
        self._middleware_stack.append(middleware)

    async def route_request(self,
                          request: Request,
                          **kwargs) -> Response:
        """Route incoming request"""
        start_time = datetime.utcnow()
        
        try:
            # Find matching route
            route = self._find_route(request.url.path, request.method)
            if not route:
                return Response(
                    content=json.dumps({
                        "error": "Route not found"
                    }),
                    status_code=404
                )
                
            # Apply middleware
            context = {
                "start_time": start_time,
                "route": route,
                **kwargs
            }
            
            for middleware in self._middleware_stack:
                request = await middleware(request, context)
                if isinstance(request, Response):
                    return request
                    
            # Check cache
            if route.cache_ttl:
                cache_key = self._build_cache_key(request)
                cached = self._get_cached(cache_key)
                if cached:
                    return Response(
                        content=cached["content"],
                        status_code=cached["status"],
                        headers=cached["headers"]
                    )
                    
            # Forward request
            response = await self._forward_request(request, route)
            
            # Cache response if configured
            if route.cache_ttl and 200 <= response.status_code < 300:
                self._cache_response(
                    cache_key,
                    response,
                    route.cache_ttl
                )
                
            return response
            
        except Exception as e:
            self.logger.error(f"Request routing failed: {str(e)}")
            return Response(
                content=json.dumps({
                    "error": "Internal server error"
                }),
                status_code=500
            )

    async def cleanup(self) -> None:
        """Cleanup router resources"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                
            if self._session:
                await self._session.close()
                
            self.logger.info("Request router cleaned up")
            
        except Exception as e:
            self.logger.error(f"Router cleanup failed: {str(e)}")

    def _find_route(self,
                   path: str,
                   method: str) -> Optional[RouteConfig]:
        """Find matching route configuration"""
        for route_key, route in self._routes.items():
            route_path, route_methods = route_key.split(':')
            if self._match_path(path, route_path) and \
               method in route_methods.split(','):
                return route
        return None

    def _match_path(self, path: str, pattern: str) -> bool:
        """Match URL path against route pattern"""
        # Convert route pattern to regex
        regex_pattern = re.sub(
            r'{([^:}]+)(?::([^}]+))?}',
            lambda m: f'(?P<{m.group(1)}>[^/]+)',
            pattern
        )
        return bool(re.match(f'^{regex_pattern}$', path))

    async def _forward_request(self,
                             request: Request,
                             route: RouteConfig) -> Response:
        """Forward request to service"""
        try:
            # Build request
            url = f"http://{route.service}{request.url.path}"
            headers = dict(request.headers)
            body = await request.body()
            
            # Apply retries
            for attempt in range(route.retry_count + 1):
                try:
                    async with self._session.request(
                        method=request.method,
                        url=url,
                        headers=headers,
                        data=body,
                        timeout=route.timeout,
                        allow_redirects=False
                    ) as response:
                        content = await response.read()
                        
                        # Apply response transform if configured
                        if route.transform and response.status == 200:
                            content = await route.transform(content)
                            
                        return Response(
                            content=content,
                            status_code=response.status,
                            headers=dict(response.headers)
                        )
                        
                except asyncio.TimeoutError:
                    if attempt == route.retry_count:
                        raise
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Request forwarding failed: {str(e)}")
            raise

    def _build_cache_key(self, request: Request) -> str:
        """Build cache key from request"""
        components = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
            str(sorted(request.headers.items()))
        ]
        return ":".join(components)

    def _get_cached(self, cache_key: str) -> Optional[Dict]:
        """Get cached response"""
        cached = self._cache.get(cache_key)
        if not cached:
            return None
            
        if datetime.utcnow() > cached["expires"]:
            del self._cache[cache_key]
            return None
            
        return cached

    def _cache_response(self,
                       cache_key: str,
                       response: Response,
                       ttl: int) -> None:
        """Cache response"""
        self._cache[cache_key] = {
            "content": response.body,
            "status": response.status_code,
            "headers": dict(response.headers),
            "expires": datetime.utcnow() + timedelta(seconds=ttl)
        }

    async def _cleanup_cache(self) -> None:
        """Cleanup expired cache entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Clean every minute
                
                now = datetime.utcnow()
                expired = [
                    key for key, cached in self._cache.items()
                    if now > cached["expires"]
                ]
                
                for key in expired:
                    del self._cache[key]
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cache cleanup failed: {str(e)}") 