from typing import Dict, List, Optional, Union, Any
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json
import aioredis
import prometheus_client as prom
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
import psutil
import statistics

@dataclass
class MetricDefinition:
    """Metric definition"""
    name: str
    type: str  # counter, gauge, histogram
    description: str
    labels: List[str] = None
    buckets: Optional[List[float]] = None

class MetricsCollector:
    """System metrics collection"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('MetricsCollector')
        self.registry = CollectorRegistry()
        self._redis: Optional[aioredis.Redis] = None
        self._metrics: Dict[str, Any] = {}
        self._collection_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._setup_metrics()

    async def initialize(self) -> None:
        """Initialize metrics collector"""
        try:
            # Connect to Redis
            self._redis = await aioredis.create_redis_pool(
                self.config['redis_url']
            )
            
            # Start collection
            self._running = True
            self._collection_task = asyncio.create_task(
                self._collect_metrics()
            )
            
            self.logger.info("Metrics collector initialized")
            
        except Exception as e:
            self.logger.error(f"Metrics collector initialization failed: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup metrics collector resources"""
        try:
            self._running = False
            
            if self._collection_task:
                self._collection_task.cancel()
                try:
                    await self._collection_task
                except asyncio.CancelledError:
                    pass
                    
            if self._redis:
                self._redis.close()
                await self._redis.wait_closed()
                
            self.logger.info("Metrics collector cleaned up")
            
        except Exception as e:
            self.logger.error(f"Metrics collector cleanup failed: {str(e)}")

    def register_metric(self, metric: MetricDefinition) -> None:
        """Register new metric"""
        try:
            if metric.name in self._metrics:
                raise ValueError(f"Metric already exists: {metric.name}")
                
            if metric.type == "counter":
                self._metrics[metric.name] = Counter(
                    metric.name,
                    metric.description,
                    metric.labels or [],
                    registry=self.registry
                )
            elif metric.type == "gauge":
                self._metrics[metric.name] = Gauge(
                    metric.name,
                    metric.description,
                    metric.labels or [],
                    registry=self.registry
                )
            elif metric.type == "histogram":
                self._metrics[metric.name] = Histogram(
                    metric.name,
                    metric.description,
                    metric.labels or [],
                    buckets=metric.buckets or Histogram.DEFAULT_BUCKETS,
                    registry=self.registry
                )
            else:
                raise ValueError(f"Unknown metric type: {metric.type}")
                
            self.logger.info(f"Registered metric: {metric.name}")
            
        except Exception as e:
            self.logger.error(f"Metric registration failed: {str(e)}")
            raise

    def track_value(self,
                   metric_name: str,
                   value: Union[int, float],
                   labels: Optional[Dict] = None) -> None:
        """Track metric value"""
        try:
            metric = self._metrics.get(metric_name)
            if not metric:
                raise ValueError(f"Unknown metric: {metric_name}")
                
            if isinstance(metric, Counter):
                if labels:
                    metric.labels(**labels).inc(value)
                else:
                    metric.inc(value)
            elif isinstance(metric, Gauge):
                if labels:
                    metric.labels(**labels).set(value)
                else:
                    metric.set(value)
            elif isinstance(metric, Histogram):
                if labels:
                    metric.labels(**labels).observe(value)
                else:
                    metric.observe(value)
                    
        except Exception as e:
            self.logger.error(f"Metric tracking failed: {str(e)}")

    async def get_metrics(self) -> Dict:
        """Get current metrics"""
        try:
            metrics = {}
            
            for metric_name, metric in self._metrics.items():
                if isinstance(metric, Counter):
                    metrics[metric_name] = {
                        "type": "counter",
                        "value": metric._value.get()
                    }
                elif isinstance(metric, Gauge):
                    metrics[metric_name] = {
                        "type": "gauge",
                        "value": metric._value.get()
                    }
                elif isinstance(metric, Histogram):
                    metrics[metric_name] = {
                        "type": "histogram",
                        "count": metric._count.get(),
                        "sum": metric._sum.get(),
                        "buckets": {
                            str(b): c.get()
                            for b, c in metric._buckets.items()
                        }
                    }
                    
            return metrics
            
        except Exception as e:
            self.logger.error(f"Metrics retrieval failed: {str(e)}")
            return {}

    async def get_system_metrics(self) -> Dict:
        """Get system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "per_cpu": psutil.cpu_percent(interval=1, percpu=True)
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "network": self._get_network_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {str(e)}")
            return {}

    def _setup_metrics(self) -> None:
        """Setup default metrics"""
        # System metrics
        self.register_metric(MetricDefinition(
            name="system_cpu_usage",
            type="gauge",
            description="System CPU usage percentage"
        ))
        
        self.register_metric(MetricDefinition(
            name="system_memory_usage",
            type="gauge",
            description="System memory usage percentage"
        ))
        
        self.register_metric(MetricDefinition(
            name="system_disk_usage",
            type="gauge",
            description="System disk usage percentage"
        ))
        
        # Application metrics
        self.register_metric(MetricDefinition(
            name="request_duration_seconds",
            type="histogram",
            description="Request duration in seconds",
            labels=["endpoint", "method"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        ))
        
        self.register_metric(MetricDefinition(
            name="request_count",
            type="counter",
            description="Total request count",
            labels=["endpoint", "method", "status"]
        ))

    async def _collect_metrics(self) -> None:
        """Collect metrics periodically"""
        while self._running:
            try:
                # Collect system metrics
                system_metrics = await self.get_system_metrics()
                
                # Update Prometheus metrics
                self._metrics["system_cpu_usage"].set(
                    system_metrics["cpu"]["usage_percent"]
                )
                
                self._metrics["system_memory_usage"].set(
                    system_metrics["memory"]["percent"]
                )
                
                self._metrics["system_disk_usage"].set(
                    system_metrics["disk"]["percent"]
                )
                
                # Store in Redis
                await self._redis.set(
                    "system_metrics",
                    json.dumps(system_metrics)
                )
                
                # Wait for next collection
                await asyncio.sleep(
                    self.config.get('collection_interval', 60)
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection failed: {str(e)}")
                await asyncio.sleep(5)

    def _get_network_stats(self) -> Dict:
        """Get network statistics"""
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout
            }
        except Exception:
            return {} 