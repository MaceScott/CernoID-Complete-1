"""
File: main.py
Purpose: Main FastAPI application configuration and initialization.

Key Features:
- API application setup and configuration
- CORS middleware configuration
- Route registration
- Error handling
- API versioning
- Security middleware
- Rate limiting
- Documentation setup

Dependencies:
- FastAPI: Web framework
- CORS middleware: Cross-origin resource sharing
- Custom middleware:
  - Security
  - Rate limiting
  - Error handling
- API routes
- Configuration settings

Environment Variables:
- CORS_ORIGINS: Allowed origins for CORS
- API_VERSION: Current API version
- DEBUG: Debug mode flag
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from .routes import router as api_router
from .middleware import SecurityMiddleware, RateLimitMiddleware
from .versioning import VersionManager
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

class APIManager:
    """
    API application manager responsible for setting up and configuring
    the FastAPI application with all necessary middleware and routes.
    """
    
    def __init__(self):
        """Initialize API manager and create FastAPI application."""
        self.app = self._create_app()
        self.version_manager = VersionManager()

    def _create_app(self) -> FastAPI:
        """
        Create and configure FastAPI application.
        
        Returns:
            FastAPI: Configured application instance
        """
        app = FastAPI(
            title="CernoID API",
            description="Face Recognition and Authentication System",
            version=settings.API_VERSION,
            docs_url="/api/docs" if settings.DEBUG else None,
            redoc_url="/api/redoc" if settings.DEBUG else None,
        )

        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add custom middleware
        app.add_middleware(SecurityMiddleware)
        app.add_middleware(RateLimitMiddleware)

        # Add error handlers
        self._add_error_handlers(app)

        # Include API routes
        app.include_router(api_router, prefix="/api")

        # Configure API versioning
        self.version_manager.setup_versioning(app)

        return app

    def _add_error_handlers(self, app: FastAPI) -> None:
        """
        Add global error handlers to the application.
        
        Args:
            app: FastAPI application instance
        """
        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            """Handle all unhandled exceptions."""
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return Response(
                status_code=500,
                content={"detail": "Internal server error"}
            )

        @app.exception_handler(404)
        async def not_found_handler(request: Request, exc: Exception):
            """Handle 404 Not Found errors."""
            return Response(
                status_code=404,
                content={"detail": "Resource not found"}
            )

    async def startup(self):
        """
        Perform startup tasks.
        - Initialize services
        - Check database connection
        - Load configuration
        """
        logger.info("Starting API server...")
        # Add startup tasks here

    async def shutdown(self):
        """
        Perform cleanup tasks.
        - Close database connections
        - Clean up resources
        - Stop background tasks
        """
        logger.info("Shutting down API server...")
        # Add cleanup tasks here

# Create global API manager instance
api_manager = APIManager() 