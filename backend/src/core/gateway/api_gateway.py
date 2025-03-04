from typing import Dict, List, Optional, Callable
import asyncio
import aiohttp
from datetime import datetime
import logging
from dataclasses import dataclass
import jwt
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, ValidationError

@dataclass
class RouteConfig:
    """API route configuration"""
    path: str
    method: str
    service: str
    endpoint: str
    auth_required: bool = True
    rate_limit: Optional[Dict] = None
    cache_config: Optional[Dict] = None
    timeout: int = 30

class GatewayConfig(BaseModel):
    cors_origins: List[str] = ["*"]
    jwt_secret: str
    forward_headers: List[str] = []
    host: str = '0.0.0.0'
    port: int = 8000
    workers: int = 4

class APIGateway:
    """API Gateway implementation"""
    
    def __init__(self, config: Dict):
        try:
            self.config = GatewayConfig(**config)
        except ValidationError as e:
            logging.error(f"Invalid gateway configuration: {e}")
            raise
        self.logger = logging.getLogger('APIGateway')
        self.app = FastAPI(title="CernoID API Gateway")
        self._routes: Dict[str, RouteConfig] = {}
        self._services: Dict[str, str] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._setup_middleware()
        self._setup_routes()

    async def initialize(self) -> None:
        """Initialize API Gateway"""
        try:
            self._session = aiohttp.ClientSession()
            await self._discover_services()
            self.logger.info("API Gateway initialized")
        except Exception as e:
            self.logger.error(f"Gateway initialization failed: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup gateway resources"""
        if self._session:
            await self._session.close()
        self.logger.info("API Gateway cleaned up")

    def _setup_middleware(self) -> None:
        """Setup API middleware"""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Authentication middleware
        self.app.middleware("http")(self._auth_middleware)
        
        # Rate limiting middleware
        self.app.middleware("http")(self._rate_limit_middleware)
        
        # Logging middleware
        self.app.middleware("http")(self._logging_middleware)
        
        # Error handling middleware
        self.app.middleware("http")(self._error_middleware)

    def _setup_routes(self) -> None:
        """Setup API routes"""
        for route in self.config['routes']:
            route_config = RouteConfig(**route)
            self._routes[route_config.path] = route_config
            
            # Register route handler
            self.app.add_route(
                route_config.path,
                self._create_route_handler(route_config),
                methods=[route_config.method]
            )

    def _create_route_handler(self, 
                            route_config: RouteConfig) -> Callable:
        """Create route handler"""
        async def handler(request: Request) -> Response:
            try:
                # Get service URL
                service_url = self._services.get(route_config.service)
                if not service_url:
                    raise ValueError(f"Service not found: {route_config.service}")
                    
                # Build target URL
                target_url = f"{service_url}{route_config.endpoint}"
                
                # Check cache
                if route_config.cache_config:
                    cached_response = await self._get_cached_response(
                        request, route_config
                    )
                    if cached_response:
                        return cached_response
                
                # Forward request
                async with self._session.request(
                    method=request.method,
                    url=target_url,
                    headers=self._forward_headers(request),
                    data=await request.body(),
                    timeout=route_config.timeout
                ) as response:
                    content = await response.read()
                    
                    # Cache response if configured
                    if route_config.cache_config and response.status == 200:
                        await self._cache_response(
                            request, response, content, route_config
                        )
                    
                    return Response(
                        content=content,
                        status_code=response.status,
                        headers=dict(response.headers)
                    )
                    
            except Exception as e:
                self.logger.error(f"Request handling failed: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal server error"}
                )
                
        return handler

    async def _auth_middleware(self,
                             request: Request,
                             call_next: Callable) -> Response:
        """Authentication middleware"""
        route_config = self._routes.get(request.url.path)
        
        if route_config and route_config.auth_required:
            token = request.headers.get('Authorization')
            
            if not token:
                self.logger.warning("Missing authentication token")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required"}
                )
                
            try:
                # Verify JWT token
                payload = jwt.decode(
                    token.split()[1],
                    self.config.jwt_secret,
                    algorithms=["HS256"]
                )
                request.state.user = payload
                
            except jwt.ExpiredSignatureError:
                self.logger.warning("Expired JWT token")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Token expired"}
                )
            except jwt.InvalidTokenError as e:
                self.logger.warning(f"Invalid JWT token: {str(e)}")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid token"}
                )
                
        return await call_next(request)

    async def _rate_limit_middleware(self,
                                   request: Request,
                                   call_next: Callable) -> Response:
        """Rate limiting middleware"""
        route_config = self._routes.get(request.url.path)
        
        if route_config and route_config.rate_limit:
            client_ip = request.client.host
            rate_key = f"rate:{request.url.path}:{client_ip}"
            
            # Check rate limit
            current_rate = await self._check_rate_limit(
                rate_key,
                route_config.rate_limit
            )
            
            if current_rate > route_config.rate_limit['max_requests']:
                self.logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
                
        return await call_next(request)

    async def _discover_services(self) -> None:
        """Discover available services"""
        # Implement service discovery here
        pass

    def _forward_headers(self, request: Request) -> Dict:
        """Forward necessary headers"""
        headers = {}
        for header in self.config.forward_headers:
            if header in request.headers:
                headers[header] = request.headers[header]
        return headers

    async def run(self) -> None:
        """Run API Gateway"""
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            workers=self.config.workers
        )
        server = uvicorn.Server(config)
        await server.serve() 