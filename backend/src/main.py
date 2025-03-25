"""Main application entry point."""
import os
import sys
from pathlib import Path
from typing import Optional
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.logging.base import setup_basic_logging, get_logger
from core.config import Settings, settings
from core.database import db_pool
from core.face_recognition import face_recognition_system
from core.utils.setup import setup_directories, load_environment
from api.routes import router as api_router
from core.monitoring.health import router as health_router
from core.system.bootstrap import SystemBootstrap

# Setup basic logging first
setup_basic_logging(level="INFO")
logger = get_logger(__name__)

def setup_environment() -> None:
    """Setup environment variables and load configuration."""
    try:
        # Load environment variables
        load_environment()
        
        # Create required directories
        os.makedirs("/app/logs", exist_ok=True)
        os.makedirs("/app/data", exist_ok=True)
        os.makedirs("/app/models", exist_ok=True)
        
        logger.info("Environment setup completed")
    except Exception as e:
        logger.error(f"Failed to setup environment: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    try:
        # Initialize system bootstrap first
        system = SystemBootstrap()
        await system.initialize()
        
        # Initialize database
        logger.info("Initializing database...")
        await db_pool.initialize()
        
        # Initialize face recognition system
        logger.info("Initializing face recognition system...")
        await face_recognition_system.initialize()
        
        logger.info("Application initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    finally:
        # Cleanup in reverse order
        logger.info("Starting application cleanup...")
        await face_recognition_system.cleanup()
        await db_pool.cleanup()
        await system.cleanup()
        logger.info("Application shutdown complete")

def create_app() -> FastAPI:
    """Create FastAPI application."""
    try:
        app = FastAPI(
            title=settings.APP_NAME,
            description=settings.APP_DESCRIPTION,
            version=settings.APP_VERSION,
            docs_url="/api/docs",
            redoc_url="/api/redoc",
            lifespan=lifespan
        )

        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Mount static files if they exist
        static_dir = "/app/static"
        if os.path.exists(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")

        # Health check endpoint
        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        # Include routers
        app.include_router(health_router, prefix="/api/health", tags=["health"])
        app.include_router(api_router, prefix="/api")

        return app
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise

# Create the FastAPI application instance
app = create_app()

def main():
    """Main entry point."""
    try:
        # Setup environment
        setup_environment()
        
        # Run the application
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            workers=1,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 