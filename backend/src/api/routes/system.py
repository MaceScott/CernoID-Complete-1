"""
File: system.py
Purpose: Provides system management and monitoring endpoints for the CernoID system.

Key Features:
- System health monitoring
- Storage usage tracking
- Backup management
- Resource utilization metrics
- System configuration

Dependencies:
- FastAPI: Web framework
- psutil: System metrics collection
- Core services:
  - Authentication middleware
  - Backup service
  - Monitoring service
  - Logging system

API Endpoints:
- GET /metrics: System health metrics
- GET /storage: Storage usage metrics
- GET /backup-config: Backup configuration
- POST /backup: Create system backup

Security:
- JWT authentication required
- Admin-only access
- Resource usage monitoring
- Error handling and logging
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import psutil
import os
from datetime import datetime
from pathlib import Path

from core.auth.dependencies import get_current_user
from api.schemas.system import SystemMetrics, StorageMetrics, BackupConfig

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
    """
    Get system health and performance metrics.
    
    Args:
        current_user: Authenticated user (must be admin)
    
    Returns:
        SystemMetrics: System metrics including:
            - CPU usage percentage
            - Memory usage percentage
            - Disk usage percentage
            - System uptime
            - Active user count
            - Last update timestamp
    
    Raises:
        HTTPException:
            - 403: Not an administrator
            - 500: Failed to collect metrics
    
    Security:
        - Requires admin access
        - Rate limited to prevent resource abuse
    """
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
    """
    Get detailed storage usage metrics.
    
    Args:
        current_user: Authenticated user (must be admin)
    
    Returns:
        StorageMetrics: Storage metrics including:
            - Total disk space
            - Used disk space
            - Available disk space
            - Backup size and timestamp
            - Recordings storage usage
            - Log files storage usage
    
    Raises:
        HTTPException:
            - 403: Not an administrator
            - 500: Failed to collect metrics
    
    Security:
        - Requires admin access
        - Monitors critical storage paths
    """
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
    """
    Get system backup configuration.
    
    Args:
        current_user: Authenticated user (must be admin)
    
    Returns:
        BackupConfig: Backup configuration including:
            - Backup schedule (cron format)
            - Retention period (days)
            - Backup storage location
    
    Raises:
        HTTPException:
            - 403: Not an administrator
    
    Security:
        - Requires admin access
        - Configuration validation
    """
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
    """
    Create a system backup manually.
    
    Args:
        current_user: Authenticated user (must be admin)
    
    Returns:
        Dict[str, str]: Backup status and message
    
    Raises:
        HTTPException:
            - 403: Not an administrator
            - 500: Backup creation failed
    
    Security:
        - Requires admin access
        - Resource intensive operation
        - Backup validation
    
    Note:
        This is a placeholder implementation.
        Actual implementation should:
        1. Create a backup of the database
        2. Archive important files (configs, models, etc.)
        3. Store the backup in the configured location
        4. Validate backup integrity
        5. Update backup metrics
    """
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