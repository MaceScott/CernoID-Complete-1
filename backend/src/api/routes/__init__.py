"""
API router initialization and configuration.
Combines all route modules into a single router.
"""

from fastapi import APIRouter
from .recognition import router as recognition_router
from .persons import router as persons_router
from .logs import router as logs_router
from .auth import router as auth_router

# Create main router
main_router = APIRouter()

# Include all route modules
main_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"]
)

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

# Export the main router
router = main_router

@main_router.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
