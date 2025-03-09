"""Main application entry point."""
import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.core.logging import setup_logging, get_logger
from src.core.config import Settings
from src.core.database import db_pool
from src.api.routes import main_router

# Initialize logging
setup_logging(log_level="INFO", log_file="logs/app.log")
logger = get_logger(__name__)

# Load environment variables
def setup_environment() -> None:
    """Setup environment variables."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        logger.info("Loaded environment variables from .env file")
    else:
        logger.warning(".env file not found, using system environment variables")

def create_app() -> FastAPI:
    """Create FastAPI application."""
    # Initialize environment
    setup_environment()
    
    # Create FastAPI app
    app = FastAPI(
        title="CernoID API",
        description="Face Recognition and Identity Management API",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize components
    settings = Settings()
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize application components on startup."""
        try:
            logger.info("Application initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup application components on shutdown."""
        try:
            await db_pool.close()
            logger.info("Application shutdown complete")
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")
            raise
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "1.0.0"
        }
    
    # Register API routes
    app.include_router(main_router, prefix="/api/v1")
    
    return app

# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 