"""System management schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SystemMetrics(BaseModel):
    """System health metrics."""
    cpu: float = Field(..., description="CPU usage percentage")
    memory: float = Field(..., description="Memory usage percentage")
    disk: float = Field(..., description="Disk usage percentage")
    uptime: str = Field(..., description="System uptime")
    activeUsers: int = Field(..., description="Number of active users")
    lastUpdate: str = Field(..., description="Last metrics update timestamp")

class StorageMetrics(BaseModel):
    """Storage usage metrics."""
    total: int = Field(..., description="Total storage in bytes")
    used: int = Field(..., description="Used storage in bytes")
    available: int = Field(..., description="Available storage in bytes")
    backupSize: int = Field(..., description="Size of latest backup in bytes")
    lastBackup: str = Field(..., description="Last backup timestamp")
    recordingsSize: int = Field(..., description="Size of recordings in bytes")
    logsSize: int = Field(..., description="Size of logs in bytes")

class BackupConfig(BaseModel):
    """Backup configuration."""
    schedule: str = Field(..., description="Cron schedule for automatic backups")
    retention: int = Field(..., description="Number of days to retain backups")
    location: str = Field(..., description="Backup storage location") 