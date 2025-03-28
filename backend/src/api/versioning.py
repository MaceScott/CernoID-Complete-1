"""
File: versioning.py
Purpose: Manages API versioning for the CernoID system, providing version control, deprecation handling,
         and middleware for routing requests to appropriate API versions.

Key Features:
- Version management and registration
- Deprecation handling with upgrade paths
- Version detection from headers and URLs
- Middleware for version-aware request processing
- Versioned router implementation

Dependencies:
- FastAPI for API framework
- BaseComponent from base module
- Error handling utilities

Environment Variables: None required

Expected Inputs:
- API version specified via X-API-Version header or URL path (/v1/, /v2/, etc.)
- Configuration dict for VersionManager initialization

Expected Outputs:
- Versioned API routes
- Version information in response headers
- Deprecation notices when applicable
"""

from typing import Dict, List, Optional, Any, Callable, Type
import re
from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.routing import APIRoute
from ..base import BaseComponent
from core.utils.decorators import handle_errors

class VersionManager(BaseComponent):
    """
    API version management system that handles routing, deprecation, and version detection.
    
    Attributes:
        _versions (Dict[str, APIRouter]): Mapping of version strings to routers
        _deprecated (Dict[str, str]): Mapping of deprecated versions to their successors
        _default_version (str): Default API version when none specified
        _version_header (str): Header key for API version
        _version_pattern (Pattern): Regex for version extraction from header
        _path_pattern (Pattern): Regex for version extraction from URL path
    """
    
    def __init__(self, config: dict):
        """
        Initialize version manager with configuration.
        
        Args:
            config (dict): Configuration dictionary containing:
                - api.default_version: Default API version
                - api.version_header: Custom header for version specification
        """
        super().__init__(config)
        self._versions: Dict[str, APIRouter] = {}
        self._deprecated: Dict[str, str] = {}
        self._default_version = self.config.get('api.default_version', '1')
        self._version_header = self.config.get(
            'api.version_header',
            'X-API-Version'
        )
        
        # Version matching patterns
        self._version_pattern = re.compile(r'v(\d+)')
        self._path_pattern = re.compile(r'/v(\d+)/')

    async def initialize(self) -> None:
        """Initialize version manager resources"""
        pass

    async def cleanup(self) -> None:
        """Cleanup version manager resources and clear registered versions"""
        self._versions.clear()
        self._deprecated.clear()

    def register_version(self,
                        version: str,
                        router: APIRouter,
                        deprecated: bool = False) -> None:
        """
        Register an API version with its router.
        
        Args:
            version (str): Version identifier (e.g., "1", "2")
            router (APIRouter): FastAPI router for this version
            deprecated (bool): Whether this version is deprecated
            
        Raises:
            ValueError: If version is already registered
        """
        if version in self._versions:
            raise ValueError(f"Version already registered: {version}")
            
        self._versions[version] = router
        
        if deprecated:
            latest = max(self._versions.keys())
            self._deprecated[version] = latest

    def get_router(self, version: str) -> Optional[APIRouter]:
        """
        Get router for specified version.
        
        Args:
            version (str): Version identifier
            
        Returns:
            Optional[APIRouter]: Router for version or None if not found
        """
        return self._versions.get(version)

    def list_versions(self) -> List[Dict[str, Any]]:
        """
        List all available API versions with their status.
        
        Returns:
            List[Dict[str, Any]]: List of version information including:
                - version: Version identifier
                - deprecated: Whether version is deprecated
                - successor: Next version if deprecated
                - routes: Number of routes in version
        """
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
        """
        Setup API versioning middleware for the application.
        
        Args:
            app (FastAPI): FastAPI application instance
        """
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
        """
        Create a versioned route path.
        
        Args:
            path (str): Original route path
            version (str): Version identifier
            
        Returns:
            str: Versioned route path
        """
        return f"/v{version}{path}"

    def _get_version(self, request: Request) -> str:
        """
        Extract API version from request.
        
        Args:
            request (Request): FastAPI request object
            
        Returns:
            str: Version identifier, defaults to _default_version
        """
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
    """
    Router with built-in version support that automatically prefixes routes.
    
    Attributes:
        version (str): Version identifier for this router
    """
    
    def __init__(self,
                 version: str,
                 *args,
                 **kwargs):
        """
        Initialize versioned router.
        
        Args:
            version (str): Version identifier
            *args: Arguments for APIRouter
            **kwargs: Keyword arguments for APIRouter
        """
        super().__init__(*args, **kwargs)
        self.version = version
        
    def add_api_route(self,
                     path: str,
                     endpoint: Callable,
                     **kwargs):
        """
        Add a versioned API route.
        
        Args:
            path (str): Route path
            endpoint (Callable): Route handler
            **kwargs: Additional route configuration
            
        Returns:
            APIRoute: Created route
        """
        versioned_path = f"/v{self.version}{path}"
        return super().add_api_route(versioned_path, endpoint, **kwargs)

class APIVersionMiddleware:
    """
    Middleware for handling API version information in requests and responses.
    
    Attributes:
        app (FastAPI): FastAPI application instance
        version_manager (VersionManager): Version manager instance
    """
    
    def __init__(self,
                 app: FastAPI,
                 version_manager: VersionManager):
        """
        Initialize version middleware.
        
        Args:
            app (FastAPI): FastAPI application instance
            version_manager (VersionManager): Version manager instance
        """
        self.app = app
        self.version_manager = version_manager

    async def __call__(self,
                      request: Request,
                      call_next: Callable) -> Response:
        """
        Process request and add version information.
        
        Args:
            request (Request): FastAPI request
            call_next (Callable): Next middleware in chain
            
        Returns:
            Response: Modified response with version headers
        """
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