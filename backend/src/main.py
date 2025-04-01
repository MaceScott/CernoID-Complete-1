"""
Main application module.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from core.config import get_settings
from core.database import init_db
from api.routes import api_router
import psutil
from datetime import datetime

# Configure module logger
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/health")
    async def health_check():
        """Health check endpoint with basic metrics."""
        try:
            # Get basic system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_available": memory.available,
                    "disk_available": disk.free
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics():
        """Metrics endpoint for Prometheus."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get process metrics
            process = psutil.Process()
            process_metrics = {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds()
            }
            
            # Format metrics in Prometheus format
            metrics_text = """
# HELP cernoid_system_cpu_percent CPU usage percentage
# TYPE cernoid_system_cpu_percent gauge
cernoid_system_cpu_percent{instance="backend"} %f

# HELP cernoid_system_memory_percent Memory usage percentage
# TYPE cernoid_system_memory_percent gauge
cernoid_system_memory_percent{instance="backend"} %f

# HELP cernoid_system_disk_percent Disk usage percentage
# TYPE cernoid_system_disk_percent gauge
cernoid_system_disk_percent{instance="backend"} %f

# HELP cernoid_system_memory_available Available memory in bytes
# TYPE cernoid_system_memory_available gauge
cernoid_system_memory_available{instance="backend"} %d

# HELP cernoid_system_disk_available Available disk space in bytes
# TYPE cernoid_system_disk_available gauge
cernoid_system_disk_available{instance="backend"} %d

# HELP cernoid_process_cpu_percent Process CPU usage percentage
# TYPE cernoid_process_cpu_percent gauge
cernoid_process_cpu_percent{instance="backend"} %f

# HELP cernoid_process_memory_percent Process memory usage percentage
# TYPE cernoid_process_memory_percent gauge
cernoid_process_memory_percent{instance="backend"} %f

# HELP cernoid_process_num_threads Number of process threads
# TYPE cernoid_process_num_threads gauge
cernoid_process_num_threads{instance="backend"} %d

# HELP cernoid_process_num_fds Number of process file descriptors
# TYPE cernoid_process_num_fds gauge
cernoid_process_num_fds{instance="backend"} %d
""" % (
    cpu_percent,
    memory.percent,
    disk.percent,
    memory.available,
    disk.free,
    process_metrics["cpu_percent"],
    process_metrics["memory_percent"],
    process_metrics["num_threads"],
    process_metrics["num_fds"]
)
            return metrics_text.strip()
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {str(e)}")
            return f"# Error collecting metrics: {str(e)}"

    @app.on_event("startup")
    async def startup_event():
        """Initialize application resources."""
        logger.info("Starting up application...")
        await init_db()

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up application resources."""
        logger.info("Shutting down application...")

    return app

# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 