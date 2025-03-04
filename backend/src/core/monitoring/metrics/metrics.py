from typing import Dict, Any, List, Callable, Optional, Union
import psutil
import time
from dataclasses import dataclass
import logging
from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    CollectorRegistry, multiprocess, generate_latest
)
from ..base import BaseComponent
from ..utils.errors import handle_errors

@dataclass
class SystemMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    timestamp: float

class MetricsCollector(BaseComponent):
    """Advanced metrics collection system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._registry = CollectorRegistry()
        self._metrics: Dict[str, Any] = {}
        self._labels: Dict[str, List[str]] = {}
        self._collect_interval = self.config.get('metrics.interval', 15)
        self._buckets = self.config.get(
            'metrics.buckets',
            [0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Initialize default metrics
        self._setup_default_metrics()

    async def initialize(self) -> None:
        """Initialize metrics collector"""
        # Start collection task
        if self._collect_interval > 0:
            self.add_cleanup_task(
                asyncio.create_task(self._collect_metrics())
            )

    async def cleanup(self) -> None:
        """Cleanup metrics resources"""
        self._metrics.clear()
        self._labels.clear()

    def create_counter(self,
                      name: str,
                      description: str,
                      labels: Optional[List[str]] = None) -> Counter:
        """Create Prometheus counter"""
        if name in self._metrics:
            return self._metrics[name]
            
        counter = Counter(
            name,
            description,
            labels or [],
            registry=self._registry
        )
        
        self._metrics[name] = counter
        self._labels[name] = labels or []
        
        return counter

    def create_gauge(self,
                    name: str,
                    description: str,
                    labels: Optional[List[str]] = None) -> Gauge:
        """Create Prometheus gauge"""
        if name in self._metrics:
            return self._metrics[name]
            
        gauge = Gauge(
            name,
            description,
            labels or [],
            registry=self._registry
        )
        
        self._metrics[name] = gauge
        self._labels[name] = labels or []
        
        return gauge

    def create_histogram(self,
                        name: str,
                        description: str,
                        labels: Optional[List[str]] = None,
                        buckets: Optional[List[float]] = None) -> Histogram:
        """Create Prometheus histogram"""
        if name in self._metrics:
            return self._metrics[name]
            
        histogram = Histogram(
            name,
            description,
            labels or [],
            buckets=buckets or self._buckets,
            registry=self._registry
        )
        
        self._metrics[name] = histogram
        self._labels[name] = labels or []
        
        return histogram

    def create_summary(self,
                      name: str,
                      description: str,
                      labels: Optional[List[str]] = None) -> Summary:
        """Create Prometheus summary"""
        if name in self._metrics:
            return self._metrics[name]
            
        summary = Summary(
            name,
            description,
            labels or [],
            registry=self._registry
        )
        
        self._metrics[name] = summary
        self._labels[name] = labels or []
        
        return summary

    @handle_errors(logger=None)
    def increment(self,
                 name: str,
                 value: float = 1,
                 labels: Optional[Dict] = None) -> None:
        """Increment counter metric"""
        metric = self._metrics.get(name)
        if not metric or not isinstance(metric, Counter):
            raise ValueError(f"Counter not found: {name}")
            
        if labels:
            metric.labels(**labels).inc(value)
        else:
            metric.inc(value)

    @handle_errors(logger=None)
    def set_gauge(self,
                 name: str,
                 value: float,
                 labels: Optional[Dict] = None) -> None:
        """Set gauge metric value"""
        metric = self._metrics.get(name)
        if not metric or not isinstance(metric, Gauge):
            raise ValueError(f"Gauge not found: {name}")
            
        if labels:
            metric.labels(**labels).set(value)
        else:
            metric.set(value)

    @handle_errors(logger=None)
    def observe(self,
               name: str,
               value: float,
               labels: Optional[Dict] = None) -> None:
        """Observe histogram/summary metric"""
        metric = self._metrics.get(name)
        if not metric or not isinstance(
            metric,
            (Histogram, Summary)
        ):
            raise ValueError(f"Histogram/Summary not found: {name}")
            
        if labels:
            metric.labels(**labels).observe(value)
        else:
            metric.observe(value)

    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        return generate_latest(self._registry)

    def _setup_default_metrics(self) -> None:
        """Setup default metrics"""
        # System metrics
        self.create_gauge(
            'system_cpu_usage',
            'CPU usage percentage'
        )
        
        self.create_gauge(
            'system_memory_usage',
            'Memory usage in bytes'
        )
        
        # HTTP metrics
        self.create_counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'path', 'status']
        )
        
        self.create_histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'path']
        )
        
        # Database metrics
        self.create_gauge(
            'database_connections',
            'Active database connections'
        )
        
        self.create_histogram(
            'database_query_duration_seconds',
            'Database query duration',
            ['query']
        )
        
        # Cache metrics
        self.create_gauge(
            'cache_items',
            'Number of cached items'
        )
        
        self.create_counter(
            'cache_hits_total',
            'Total cache hits'
        )
        
        self.create_counter(
            'cache_misses_total',
            'Total cache misses'
        )

    async def _collect_metrics(self) -> None:
        """Collect metrics periodically"""
        while True:
            try:
                await asyncio.sleep(self._collect_interval)
                
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect component metrics
                await self._collect_component_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection failed: {str(e)}")
                await asyncio.sleep(5)

    async def _collect_system_metrics(self) -> None:
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.set_gauge('system_cpu_usage', cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge('system_memory_usage', memory.used)
            
        except ImportError:
            self.logger.warning("psutil not available for system metrics")
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {str(e)}")

    async def _collect_component_metrics(self) -> None:
        """Collect component metrics"""
        try:
            # Database metrics
            db = self.app.get_component('database')
            if db:
                pool = await db.get_pool()
                self.set_gauge(
                    'database_connections',
                    pool.size
                )
                
            # Cache metrics
            cache = self.app.get_component('cache_manager')
            if cache:
                stats = await cache.get_stats()
                self.set_gauge(
                    'cache_items',
                    stats.get('size', 0)
                )
                
        except Exception as e:
            self.logger.error(
                f"Component metrics collection failed: {str(e)}"
            )

class MetricsManager(BaseComponent):
    """Advanced metrics collection and management"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._registry = CollectorRegistry()
        self._metrics: Dict[str, Dict] = {}
        self._labels: Dict[str, List[str]] = {}
        
        # Configure default metrics
        self._setup_default_metrics()

    async def initialize(self) -> None:
        """Initialize metrics manager"""
        # Initialize multiprocess metrics if enabled
        if self.config.get('metrics.multiprocess', False):
            multiprocess.MultiProcessCollector(self._registry)

    async def cleanup(self) -> None:
        """Cleanup metrics resources"""
        self._metrics.clear()
        self._labels.clear()

    def counter(self,
                name: str,
                description: str,
                labels: Optional[List[str]] = None) -> Counter:
        """Create or get counter metric"""
        return self._get_or_create_metric(
            name,
            description,
            Counter,
            labels
        )

    def gauge(self,
             name: str,
             description: str,
             labels: Optional[List[str]] = None) -> Gauge:
        """Create or get gauge metric"""
        return self._get_or_create_metric(
            name,
            description,
            Gauge,
            labels
        )

    def histogram(self,
                 name: str,
                 description: str,
                 labels: Optional[List[str]] = None,
                 buckets: Optional[List[float]] = None) -> Histogram:
        """Create or get histogram metric"""
        return self._get_or_create_metric(
            name,
            description,
            Histogram,
            labels,
            buckets=buckets or Histogram.DEFAULT_BUCKETS
        )

    def summary(self,
               name: str,
               description: str,
               labels: Optional[List[str]] = None) -> Summary:
        """Create or get summary metric"""
        return self._get_or_create_metric(
            name,
            description,
            Summary,
            labels
        )

    def _get_or_create_metric(self,
                             name: str,
                             description: str,
                             metric_type: type,
                             labels: Optional[List[str]] = None,
                             **kwargs) -> Any:
        """Get existing metric or create new one"""
        if name not in self._metrics:
            # Store label names for this metric
            self._labels[name] = labels or []
            
            # Create new metric
            self._metrics[name] = {
                'metric': metric_type(
                    name,
                    description,
                    labelnames=self._labels[name],
                    registry=self._registry,
                    **kwargs
                ),
                'type': metric_type
            }
            
        return self._metrics[name]['metric']

    def _setup_default_metrics(self) -> None:
        """Setup default system metrics"""
        # System metrics
        self.gauge(
            'system_cpu_usage',
            'System CPU usage percentage'
        )
        
        self.gauge(
            'system_memory_usage',
            'System memory usage percentage'
        )
        
        self.gauge(
            'system_disk_usage',
            'System disk usage percentage'
        )
        
        # Application metrics
        self.counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        self.gauge(
            'http_requests_in_progress',
            'In-progress HTTP requests',
            ['method', 'endpoint']
        )
        
        # Database metrics
        self.gauge(
            'db_connections_active',
            'Active database connections'
        )
        
        self.histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['query_type']
        )
        
        # Cache metrics
        self.counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_type']
        )
        
        self.counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_type']
        )
        
        # Rate limit metrics
        self.counter(
            'rate_limit_hits_total',
            'Total rate limit hits',
            ['limit_type']
        )
