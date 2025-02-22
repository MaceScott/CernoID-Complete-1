from typing import Dict, Optional, Any, Callable, List, Union
from fastapi import APIRouter, Request, Response, HTTPException
import httpx
import asyncio
from datetime import datetime
import json
from urllib.parse import urljoin
from ..base import BaseComponent
from ..utils.errors import handle_errors

class APIGateway(BaseComponent):
    """Advanced API Gateway and routing system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._routes: Dict[str, Dict] = {}
        self._services: Dict[str, Dict] = {}
        self._middlewares: List[Callable] = []
        self._client = httpx.AsyncClient()
        self._timeout = self.config.get('gateway.timeout', 30)
        self._retry_attempts = self.config.get('gateway.retry_attempts', 3)
        self._circuit_breaker = self.config.get('gateway.circuit_breaker', True)
        self._breaker_threshold = self.config.get('gateway.breaker_threshold', 5)
        self._breaker_timeout = self.config.get('gateway.breaker_timeout', 60)
        self._health_interval = self.config.get('gateway.health_interval', 30)
        self._router = APIRouter()

    async def initialize(self) -> None:
        """Initialize API gateway"""
        # Load route configurations
        await self._load_routes()
        
        # Start health checks
        if self._health_interval > 0:
            self.add_cleanup_task(
                asyncio.create_task(self._health_check())
            )

    async def cleanup(self) -> None:
        """Cleanup gateway resources"""
        await self._client.aclose()
        self._routes.clear()
        self._services.clear()
        self._middlewares.clear()

    def get_router(self) -> APIRouter:
        """Get FastAPI router"""
        return self._router

    @handle_errors(logger=None)
    async def register_service(self,
                             name: str,
                             url: str,
                             routes: List[Dict],
                             metadata: Optional[Dict] = None) -> None:
        """Register service and routes"""
        # Add service
        self._services[name] = {
            'url': url.rstrip('/'),
            'status': 'unknown',
            'last_check': None,
            'failures': 0,
            'metadata': metadata or {}
        }
        
        # Add routes
        for route in routes:
            route_id = f"{name}:{route['path']}"
            self._routes[route_id] = {
                'service': name,
                'path': route['path'],
                'methods': route.get('methods', ['GET']),
                'strip_prefix': route.get('strip_prefix', False),
                'rewrite': route.get('rewrite', None),
                'middleware': route.get('middleware', [])
            }
            
            # Register FastAPI route
            self._router.add_api_route(
                route['path'],
                self._handle_request,
                methods=route['methods'],
                name=route_id
            )

    def add_middleware(self,
                      middleware: Callable) -> None:
        """Add gateway middleware"""
        self._middlewares.append(middleware)

    async def get_service_status(self,
                               name: Optional[str] = None) -> Dict:
        """Get service status"""
        if name:
            return self._services.get(name, {})
            
        return self._services

    async def get_routes(self) -> Dict:
        """Get registered routes"""
        return self._routes

    async def _handle_request(self, request: Request) -> Response:
        """Handle incoming request"""
        # Get route
        route_id = request.scope.get('endpoint').__name__
        route = self._routes.get(route_id)
        
        if not route:
            raise HTTPException(status_code=404)
            
        # Get service
        service = self._services.get(route['service'])
        if not service:
            raise HTTPException(status_code=503)
            
        # Check circuit breaker
        if (self._circuit_breaker and
            service['status'] == 'failed'):
            raise HTTPException(
                status_code=503,
                detail="Service unavailable"
            )
            
        # Build target URL
        target_url = self._build_url(request, route, service)
        
        # Apply middleware
        for middleware in self._middlewares:
            request = await middleware(request)
            
        # Forward request
        try:
            response = await self._forward_request(
                request,
                target_url,
                service
            )
            return response
            
        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise HTTPException(status_code=502)

    def _build_url(self,
                   request: Request,
                   route: Dict,
                   service: Dict) -> str:
        """Build target URL"""
        path = request.url.path
        
        # Strip prefix
        if route['strip_prefix']:
            prefix = route['path'].rstrip('/')
            if path.startswith(prefix):
                path = path[len(prefix):]
                
        # Apply rewrite
        if route['rewrite']:
            path = route['rewrite'].format(
                path=path,
                **request.path_params
            )
            
        # Build full URL
        return urljoin(service['url'], path.lstrip('/'))

    async def _forward_request(self,
                             request: Request,
                             url: str,
                             service: Dict) -> Response:
        """Forward request to service"""
        # Get request content
        body = await request.body()
        
        # Prepare headers
        headers = dict(request.headers)
        headers['X-Forwarded-For'] = request.client.host
        
        for attempt in range(self._retry_attempts):
            try:
                # Send request
                response = await self._client.request(
                    request.method,
                    url,
                    content=body,
                    headers=headers,
                    params=request.query_params,
                    timeout=self._timeout,
                    follow_redirects=True
                )
                
                # Update service status
                service['status'] = 'healthy'
                service['failures'] = 0
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
            except Exception as e:
                service['failures'] += 1
                
                if (service['failures'] >=
                    self._breaker_threshold):
                    service['status'] = 'failed'
                    
                if attempt == self._retry_attempts - 1:
                    raise e
                    
                await asyncio.sleep(1)

    async def _health_check(self) -> None:
        """Perform service health checks"""
        while True:
            try:
                await asyncio.sleep(self._health_interval)
                
                for name, service in self._services.items():
                    try:
                        # Check service health
                        response = await self._client.get(
                            f"{service['url']}/health",
                            timeout=5
                        )
                        
                        if response.status_code == 200:
                            service['status'] = 'healthy'
                            service['failures'] = 0
                        else:
                            service['failures'] += 1
                            
                    except Exception:
                        service['failures'] += 1
                        
                    # Update status
                    if (service['failures'] >=
                        self._breaker_threshold):
                        service['status'] = 'failed'
                        
                    service['last_check'] = datetime.utcnow().isoformat()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check failed: {str(e)}")
                await asyncio.sleep(5)

    async def _load_routes(self) -> None:
        """Load route configurations"""
        try:
            config = self.app.get_component('config_manager')
            if not config:
                return
                
            routes = config.get('gateway.routes', [])
            for route in routes:
                await self.register_service(
                    route['service'],
                    route['url'],
                    route['routes'],
                    route.get('metadata')
                )
                
        except Exception as e:
            self.logger.error(f"Failed to load routes: {str(e)}") 