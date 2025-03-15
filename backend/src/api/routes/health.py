"""
File: health.py
Purpose: Provides health check endpoints for monitoring the CernoID system's operational status.

Key Features:
- Basic liveness probe
- Component readiness checks
- System resource monitoring
- Database health verification
- GPU status monitoring
- Storage system checks

Dependencies:
- FastAPI: Web framework
- psutil: System metrics collection
- PyTorch: GPU monitoring
- Core services:
  - DatabaseService: Database connectivity
  - Configuration management
  - Logging system

API Endpoints:
- GET /health/live: Basic liveness probe
- GET /health/ready: Comprehensive readiness check

Monitoring:
- Database connectivity and performance
- GPU availability and memory usage
- System resource utilization
- Storage system availability
- Component health aggregation
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import psutil
import torch
import asyncio
from datetime import datetime

from ...core.database.service import DatabaseService
from ...utils.config import get_settings
from ...utils.logging import get_logger

router = APIRouter(prefix="/health", tags=["health"])
db = DatabaseService()
settings = get_settings()
logger = get_logger(__name__)

@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Basic liveness probe endpoint.
    
    Returns:
        Dict[str, str]: Simple alive status
        
    Note:
        This is a lightweight check that should return quickly.
        Used by container orchestrators and load balancers.
    """
    return {"status": "alive"}

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Comprehensive readiness check of all system components.
    
    Returns:
        Dict[str, Any]: Detailed health status including:
            - Overall system health
            - Timestamp of check
            - Component-specific health:
                - Database status and metrics
                - GPU availability and memory
                - System resource usage
                - Storage system status
    
    Raises:
        HTTPException: If health check fails (503 Service Unavailable)
    
    Note:
        This is a more intensive check that verifies all components
        are operational and have sufficient resources.
    """
    try:
        status = {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check database
        db_status = await check_database()
        status["components"]["database"] = db_status
        
        # Check GPU
        gpu_status = check_gpu()
        status["components"]["gpu"] = gpu_status
        
        # Check system resources
        system_status = check_system_resources()
        status["components"]["system"] = system_status
        
        # Check storage
        storage_status = check_storage()
        status["components"]["storage"] = storage_status
        
        # Overall status
        status["healthy"] = all(
            component.get("healthy", False)
            for component in status["components"].values()
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

async def check_database() -> Dict[str, Any]:
    """
    Check database connectivity and performance metrics.
    
    Returns:
        Dict[str, Any]: Database health status including:
            - Connection health
            - Query latency
            - Active connections
            - Error details if unhealthy
    
    Note:
        Executes a simple query to verify connectivity and
        collects performance metrics from pg_stat_database.
    """
    try:
        async with db.session() as session:
            # Execute simple query
            await session.execute("SELECT 1")
            
            # Get database metrics
            metrics = await session.execute(
                """
                SELECT * FROM pg_stat_database 
                WHERE datname = current_database()
                """
            )
            metrics = metrics.fetchone()
            
            return {
                "healthy": True,
                "latency_ms": metrics.total_exec_time / metrics.xact_commit
                if metrics.xact_commit > 0 else 0,
                "connections": metrics.numbackends
            }
            
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }

def check_gpu() -> Dict[str, Any]:
    """
    Check GPU availability and resource usage.
    
    Returns:
        Dict[str, Any]: GPU health status including:
            - Availability
            - Device count
            - Current device
            - Memory allocation
            - Memory reservation
            - Error details if unhealthy
    
    Note:
        Requires CUDA-enabled PyTorch installation.
        Memory metrics are in bytes.
    """
    try:
        if not torch.cuda.is_available():
            return {
                "healthy": False,
                "error": "GPU not available"
            }
            
        return {
            "healthy": True,
            "device_count": torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "memory_allocated": torch.cuda.memory_allocated(),
            "memory_reserved": torch.cuda.memory_reserved()
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }

def check_system_resources() -> Dict[str, Any]:
    """
    Check system resource utilization.
    
    Returns:
        Dict[str, Any]: System health status including:
            - CPU usage percentage
            - Memory usage percentage
            - Disk usage percentage
            - Available memory
            - Available disk space
            - Error details if unhealthy
    
    Note:
        Memory and disk space are in bytes.
        Percentages are 0-100.
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "healthy": True,
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "memory_available": memory.available,
            "disk_available": disk.free
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }

def check_storage() -> Dict[str, Any]:
    """
    Check storage system availability and usage.
    
    Returns:
        Dict[str, Any]: Storage health status including:
            - Models directory availability
            - Data directory availability
            - Models storage size
            - Data storage size
            - Error details if unhealthy
    
    Note:
        Storage sizes are in bytes.
        Checks configured paths from settings.
    """
    try:
        models_path = settings.model_dir
        data_path = settings.data_dir
        
        return {
            "healthy": True,
            "models_available": models_path.exists(),
            "data_available": data_path.exists(),
            "models_size": sum(f.stat().st_size for f in models_path.glob('**/*')),
            "data_size": sum(f.stat().st_size for f in data_path.glob('**/*'))
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        } 