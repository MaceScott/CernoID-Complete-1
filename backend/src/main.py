"""Main application entry point."""
import os
import sys
import logging
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import multiprocessing

from core.logging import setup_logging, get_logger
from core.config import Settings
from core.database.connection import db_pool
from core.face_recognition import face_recognition_system
from core.utils.setup import setup_directories, load_environment
from api.routes import router as api_router
from core.monitoring.health import router as health_router
from core.system.bootstrap import SystemBootstrap
from core.config import settings

def setup_environment(app_dir: Path = None) -> Path:
    """Setup environment and logging."""
    # Setup directories
    app_dir = setup_directories(app_dir)
    
    # Setup logging
    log_file = app_dir / 'logs/app.log'
    setup_logging(log_level="INFO", log_file=str(log_file))
    
    # Load environment
    load_environment(app_dir)
    
    return app_dir

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    logger = get_logger(__name__)
    try:
        # Initialize components in parallel
        await asyncio.gather(
            db_pool.create_pool(),
            face_recognition_system.initialize()
        )
        logger.info("Application initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    finally:
        # Cleanup
        await asyncio.gather(
            db_pool.close(),
            face_recognition_system.cleanup()
        )
        logger.info("Application shutdown complete")

def create_app(app_dir: Path) -> FastAPI:
    """Create FastAPI application."""
    logger = get_logger(__name__)
    try:
        app = FastAPI(
            title="CernoID API",
            description="CernoID Security System API",
            version="1.0.0",
            lifespan=lifespan
        )

        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Mount static files
        static_dir = app_dir / 'static'
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # Health check endpoint
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "version": "1.0.0",
                "database": await db_pool.is_connected(),
                "face_recognition": face_recognition_system.is_initialized
            }

        # Register API routes
        app.include_router(api_router, prefix="/api/v1")
        
        # Include health check routes
        app.include_router(health_router, tags=["health"])
        
        # System bootstrap
        system = SystemBootstrap()

        @app.on_event("startup")
        async def startup_event():
            await system.initialize()

        @app.on_event("shutdown")
        async def shutdown_event():
            await system.cleanup()

        return app
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise

def run_app():
    """Run the application - entry point for installed package."""
    # Setup environment
    app_dir = setup_environment()
    
    # Get the number of workers based on CPU cores
    workers = min(multiprocessing.cpu_count(), 4)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=workers,
        log_level="info",
        reload=False,
        access_log=True
    )

# Create application instance
app_dir = setup_environment()
app = create_app(app_dir)

if __name__ == "__main__":
    run_app() 