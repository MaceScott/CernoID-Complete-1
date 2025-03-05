from typing import Dict, Any, Optional
import psutil
import GPUtil
from datetime import datetime
from core.logging import get_logger
from core.base import BaseComponent
from core.config import config

logger = get_logger(__name__)

class MonitoringService(BaseComponent):
    """Service for monitoring system metrics and health."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._metrics: Dict[str, Any] = {}
        self._health_status: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None
        self._update_interval = config.get('monitoring.update_interval', 60)
        
    async def initialize(self) -> None:
        """Initialize monitoring service."""
        self._start_time = datetime.utcnow()
        self._metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'gpu_usage': 0.0,
            'gpu_memory': 0.0,
            'network_io': {'sent': 0, 'received': 0},
            'process_count': 0,
            'thread_count': 0,
            'open_files': 0
        }
        self._health_status = {
            'status': 'healthy',
            'last_check': None,
            'errors': []
        }
        
    async def cleanup(self) -> None:
        """Clean up monitoring resources."""
        self._metrics.clear()
        self._health_status.clear()
        
    async def update_metrics(self) -> None:
        """Update system metrics."""
        try:
            # CPU metrics
            self._metrics['cpu_usage'] = psutil.cpu_percent(interval=1)
            self._metrics['process_count'] = len(psutil.pids())
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self._metrics['memory_usage'] = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self._metrics['disk_usage'] = disk.percent
            
            # Network metrics
            net_io = psutil.net_io_counters()
            self._metrics['network_io'] = {
                'sent': net_io.bytes_sent,
                'received': net_io.bytes_recv
            }
            
            # Process metrics
            process = psutil.Process()
            self._metrics['thread_count'] = process.num_threads()
            self._metrics['open_files'] = len(process.open_files())
            
            # GPU metrics if available
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    self._metrics['gpu_usage'] = gpu.load * 100
                    self._metrics['gpu_memory'] = gpu.memoryUtil * 100
            except Exception as e:
                logger.warning(f"Failed to get GPU metrics: {e}")
                
            self._last_update = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            
    async def check_health(self) -> None:
        """Check system health."""
        try:
            # Update metrics first
            await self.update_metrics()
            
            # Check critical metrics
            errors = []
            
            # CPU check
            if self._metrics['cpu_usage'] > 90:
                errors.append("High CPU usage")
                
            # Memory check
            if self._metrics['memory_usage'] > 90:
                errors.append("High memory usage")
                
            # Disk check
            if self._metrics['disk_usage'] > 90:
                errors.append("High disk usage")
                
            # GPU check if available
            if self._metrics.get('gpu_usage', 0) > 90:
                errors.append("High GPU usage")
                
            # Update health status
            self._health_status.update({
                'status': 'unhealthy' if errors else 'healthy',
                'last_check': datetime.utcnow(),
                'errors': errors
            })
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._health_status.update({
                'status': 'error',
                'last_check': datetime.utcnow(),
                'errors': [str(e)]
            })
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return self._metrics.copy()
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self._health_status.copy()
        
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self._health_status.get('status') == 'healthy'

# Global monitoring service instance
monitoring_service = MonitoringService(config.to_dict()) 