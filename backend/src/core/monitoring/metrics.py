"""Metrics collection module."""
from typing import Dict, Any, Optional
import time
import psutil
from prometheus_client import Counter, Gauge, Histogram
from prometheus_client.metrics import MetricWrapperBase

from core.logging.base import get_logger

logger = get_logger(__name__)

class MetricsCollector:
    """System metrics collector."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._metrics: Dict[str, MetricWrapperBase] = {}
        self._initialized = False
        self._last_collection = 0
        self._collection_interval = 15  # seconds

    async def initialize(self) -> None:
        """Initialize metrics collector."""
        try:
            self.logger.info("Initializing metrics collector...")
            
            # System metrics
            self._metrics['cpu_usage'] = Gauge(
                'system_cpu_usage',
                'CPU usage percentage',
                ['cpu']
            )
            
            self._metrics['memory_usage'] = Gauge(
                'system_memory_usage',
                'Memory usage in bytes',
                ['type']
            )
            
            self._metrics['disk_usage'] = Gauge(
                'system_disk_usage',
                'Disk usage in bytes',
                ['mountpoint']
            )
            
            self._metrics['network_io'] = Counter(
                'system_network_io',
                'Network I/O bytes',
                ['interface', 'direction']
            )
            
            # Application metrics
            self._metrics['request_count'] = Counter(
                'app_request_count',
                'Total number of requests',
                ['method', 'endpoint', 'status']
            )
            
            self._metrics['request_latency'] = Histogram(
                'app_request_latency',
                'Request latency in seconds',
                ['method', 'endpoint']
            )
            
            self._metrics['error_count'] = Counter(
                'app_error_count',
                'Total number of errors',
                ['type']
            )
            
            self._initialized = True
            self.logger.info("Metrics collector initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics collector: {str(e)}")
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """Cleanup metrics collector."""
        try:
            self.logger.info("Cleaning up metrics collector...")
            self._metrics.clear()
            self._initialized = False
            self.logger.info("Metrics collector cleanup completed")
        except Exception as e:
            self.logger.error(f"Failed to cleanup metrics collector: {str(e)}")
            raise

    async def collect_system_metrics(self) -> None:
        """Collect system metrics."""
        if not self._initialized:
            return
            
        try:
            current_time = time.time()
            if current_time - self._last_collection < self._collection_interval:
                return
                
            # CPU metrics
            for i, percentage in enumerate(psutil.cpu_percent(percpu=True)):
                self._metrics['cpu_usage'].labels(cpu=f'cpu{i}').set(percentage)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self._metrics['memory_usage'].labels(type='used').set(memory.used)
            self._metrics['memory_usage'].labels(type='free').set(memory.free)
            self._metrics['memory_usage'].labels(type='total').set(memory.total)
            
            # Disk metrics
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self._metrics['disk_usage'].labels(
                        mountpoint=partition.mountpoint
                    ).set(usage.used)
                except Exception as e:
                    self.logger.error(f"Failed to collect disk metrics: {str(e)}")
            
            # Network metrics
            net_io = psutil.net_io_counters()
            self._metrics['network_io'].labels(
                interface='total',
                direction='sent'
            ).inc(net_io.bytes_sent)
            self._metrics['network_io'].labels(
                interface='total',
                direction='received'
            ).inc(net_io.bytes_recv)
            
            self._last_collection = current_time
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {str(e)}")

    def record_request(self, method: str, endpoint: str, status: int, latency: float) -> None:
        """Record request metrics."""
        if not self._initialized:
            return
            
        try:
            self._metrics['request_count'].labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()
            
            self._metrics['request_latency'].labels(
                method=method,
                endpoint=endpoint
            ).observe(latency)
            
        except Exception as e:
            self.logger.error(f"Failed to record request metrics: {str(e)}")

    def record_error(self, error_type: str) -> None:
        """Record error metrics."""
        if not self._initialized:
            return
            
        try:
            self._metrics['error_count'].labels(type=error_type).inc()
        except Exception as e:
            self.logger.error(f"Failed to record error metrics: {str(e)}")

    @property
    def is_initialized(self) -> bool:
        """Check if metrics collector is initialized."""
        return self._initialized

# Create singleton instance
metrics_collector = MetricsCollector() 