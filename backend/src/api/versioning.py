from typing import Dict, List, Optional, Any, Callable, Type
import re
from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.routing import APIRoute
from ..base import BaseComponent
from ..utils.errors import handle_errors

class VersionManager(BaseComponent):
    """API version management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._versions: Dict[str, APIRouter] = {}
        self._deprecated: Dict[str, str] = {}
        self._default_version = self.config.get('api.default_version', '1')
        self._version_header = self.config.get(
            'api.version_header',
            'X-API-Version'
        )
        
        # Version matching
        self._version_pattern = re.compile(r'v(\d+)')
        self._path_pattern = re.compile(r'/v(\d+)/')

    async def initialize(self) -> None:
        """Initialize version manager"""
        pass

    async def cleanup(self) -> None:
        """Cleanup version manager resources"""
        self._versions.clear()
        self._deprecated.clear()

    def register_version(self,
                        version: str,
                        router: APIRouter,
                        deprecated: bool = False) -> None:
        """Register API version"""
        if version in self._versions:
            raise ValueError(f"Version already registered: {version}")
            
        self._versions[version] = router
        
        if deprecated:
            latest = max(self._versions.keys())
            self._deprecated[version] = latest

    def get_router(self, version: str) -> Optional[APIRouter]:
        """Get version router"""
        return self._versions.get(version)

    def list_versions(self) -> List[Dict[str, Any]]:
        """List available API versions"""
        return [
            {
                'version': version,
                'deprecated': version in self._deprecated,
                'successor': self._deprecated.get(version),
                'routes': len(router.routes)
            }
            for version, router in self._versions.items()
        ]

    def setup_versioning(self, app: FastAPI) -> None:
        """Setup API versioning middleware"""
        @app.middleware("http")
        async def version_middleware(
            request: Request,
            call_next: Callable
        ) -> Response:
            # Get version from header or URL
            version = self._get_version(request)
            
            # Check if version is deprecated
            if version in self._deprecated:
                latest = self._deprecated[version]
                response = await call_next(request)
                response.headers['X-API-Deprecated'] = 'true'
                response.headers['X-API-Latest-Version'] = latest
                return response
                
            return await call_next(request)

    def create_versioned_route(self,
                             path: str,
                             version: str) -> str:
        """Create versioned route path"""
        return f"/v{version}{path}"

    def _get_version(self, request: Request) -> str:
        """Get API version from request"""
        # Check header
        version = request.headers.get(self._version_header)
        if version:
            match = self._version_pattern.match(version)
            if match:
                return match.group(1)
                
        # Check URL path
        match = self._path_pattern.match(request.url.path)
        if match:
            return match.group(1)
            
        return self._default_version

class VersionedAPIRouter(APIRouter):
    """Router with version support"""
    
    def __init__(self,
                 version: str,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.version = version
        
    def add_api_route(self,
                     path: str,
                     endpoint: Callable,
                     **kwargs):
        """Add versioned API route"""
        versioned_path = f"/v{self.version}{path}"
        return super().add_api_route(versioned_path, endpoint, **kwargs)

class APIVersionMiddleware:
    """Middleware for API version handling"""
    
    def __init__(self,
                 app: FastAPI,
                 version_manager: VersionManager):
        self.app = app
        self.version_manager = version_manager

    async def __call__(self,
                      request: Request,
                      call_next: Callable) -> Response:
        # Get API version
        version = self.version_manager._get_version(request)
        
        # Store version in request state
        request.state.api_version = version
        
        # Process request
        response = await call_next(request)
        
        # Add version headers
        response.headers[self.version_manager._version_header] = f"v{version}"
        
        # Add deprecation headers if needed
        if version in self.version_manager._deprecated:
            latest = self.version_manager._deprecated[version]
            response.headers['X-API-Deprecated'] = 'true'
            response.headers['X-API-Latest-Version'] = f"v{latest}"
            
        return response 