"""
API router initialization and configuration.
Combines all route modules into a single router.
"""

from fastapi import APIRouter
from . import auth, recognition, system
from .persons import router as persons_router
from .logs import router as logs_router

# Create main router
main_router = APIRouter()

# Include all route modules
from .auth import router as auth_router
from .recognition import router as recognition_router
from .system import router as system_router

main_router.include_router(auth_router)
main_router.include_router(recognition_router)
main_router.include_router(system_router)

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

# Export the main router
api_router = main_router

@main_router.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
