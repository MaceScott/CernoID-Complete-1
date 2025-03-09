"""System management routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import psutil
import os
from datetime import datetime
from pathlib import Path

from ..dependencies import get_current_user
from ..schemas.system import SystemMetrics, StorageMetrics, BackupConfig

router = APIRouter(
    prefix="/api/v1/system",
    tags=["system"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    }
)

@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SystemMetrics:
    """Get system health metrics."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access system metrics"
        )
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get active users (this is a placeholder - implement actual user tracking)
        active_users = 1  # Replace with actual active user count
        
        return SystemMetrics(
            cpu=cpu_percent,
            memory=memory.percent,
            disk=disk.percent,
            uptime=str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())),
            activeUsers=active_users,
            lastUpdate=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )

@router.get("/storage", response_model=StorageMetrics)
async def get_storage_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> StorageMetrics:
    """Get storage usage metrics."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access storage metrics"
        )
    
    try:
        # Get total disk usage
        disk = psutil.disk_usage('/')
        
        # Get recordings directory size
        recordings_dir = Path("data/recordings")
        recordings_size = sum(f.stat().st_size for f in recordings_dir.rglob('*') if f.is_file()) if recordings_dir.exists() else 0
        
        # Get logs directory size
        logs_dir = Path("logs")
        logs_size = sum(f.stat().st_size for f in logs_dir.rglob('*') if f.is_file()) if logs_dir.exists() else 0
        
        # Get backup size (placeholder - implement actual backup tracking)
        backup_size = 0  # Replace with actual backup size
        last_backup = datetime.now().isoformat()  # Replace with actual last backup time
        
        return StorageMetrics(
            total=disk.total,
            used=disk.used,
            available=disk.free,
            backupSize=backup_size,
            lastBackup=last_backup,
            recordingsSize=recordings_size,
            logsSize=logs_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage metrics: {str(e)}"
        )

@router.get("/backup-config", response_model=BackupConfig)
async def get_backup_config(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> BackupConfig:
    """Get backup configuration."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access backup configuration"
        )
    
    # Placeholder - implement actual backup configuration retrieval
    return BackupConfig(
        schedule="0 0 * * *",  # Daily at midnight
        retention=7,  # Keep 7 days of backups
        location="/backups"  # Backup location
    )

@router.post("/backup")
async def create_backup(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """Create a system backup."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create backups"
        )
    
    try:
        # Placeholder - implement actual backup creation
        # This should:
        # 1. Create a backup of the database
        # 2. Archive important files (configs, models, etc.)
        # 3. Store the backup in the configured location
        
        return {"status": "success", "message": "Backup created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        ) 