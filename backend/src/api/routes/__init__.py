"""
API router initialization and configuration.
Combines all route modules into a single router.
"""

from fastapi import APIRouter
from .recognition import router as recognition_router
from .persons import router as persons_router
from .logs import router as logs_router
from core.config.settings import get_settings

settings = get_settings()

# Create main router with version prefix
main_router = APIRouter(prefix=settings.api_prefix)

# Include all route modules
main_router.include_router(
    recognition_router,
    prefix="/recognition",
    tags=["recognition"]
)

main_router.include_router(
    persons_router,
    prefix="/persons",
    tags=["persons"]
)

main_router.include_router(
    logs_router,
    prefix="/logs",
    tags=["logs"]
)

# Health check endpoint
@main_router.get("/health", tags=["system"])
async def health_check():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.api_version,
        "environment": settings.environment
    }

# Export the configured router
__all__ = ["main_router"]
