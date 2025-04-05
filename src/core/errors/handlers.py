import logging
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from .base import BaseError

logger = logging.getLogger(__name__)

async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global error handler for all exceptions."""
    if isinstance(exc, BaseError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                    "metadata": exc.metadata
                }
            }
        )
    
    # Log unexpected errors
    logger.error(
        "Unexpected error occurred",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    # Return generic error for unexpected exceptions
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "metadata": {}
            }
        }
    )

def setup_error_handlers(app: Any) -> None:
    """Set up error handlers for the FastAPI application."""
    app.add_exception_handler(Exception, error_handler) 