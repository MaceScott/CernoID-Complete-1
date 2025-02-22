from typing import Dict, List, Optional
import asyncio
import time
from datetime import datetime
import psutil
import logging
from dataclasses import dataclass
import prometheus_client as prom
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram

@dataclass
class MetricDefinition:
    """Metric definition"""
    name: str
    type: str
    description: str
    labels: List[str]
    buckets: Optional[List[float]] = None

class MetricsCollector:
    """System metrics collection and export"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('MetricsCollector')
        self.registry = CollectorRegistry()
        self._metrics: Dict[str, prom.Metric] = {}
        self._collection_task: Optional[asyncio.Task] = None
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Setup system metrics"""
        # System metrics
        self._create_metric(MetricDefinition(
            name="system_cpu_usage",
            type="gauge",
            description="System CPU usage percentage",
            labels=["cpu"]
        ))
        
        self._create_metric(MetricDefinition(
            name="system_memory_usage",
            type="gauge",
            description="System memory usage in bytes",
            labels=["type"]
        ))
        
        # API metrics
        self._create_metric(MetricDefinition(
            name="api_request_total",
            type="counter",
            description="Total API requests",
            labels=["endpoint", "method", "status"]
        ))
        
        self._create_metric(MetricDefinition(
            name="api_request_duration_seconds",
            type="histogram",
            description="API request duration in seconds",
            labels=["endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        ))
        
        # Recognition metrics
        self._create_metric(MetricDefinition(
            name="recognition_processing_time",
            type="histogram",
            description="Face recognition processing time",
            labels=["model"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        ))
        
        self._create_metric(MetricDefinition(
            name="recognition_accuracy",
            type="gauge",
            description="Face recognition accuracy",
            labels=["model"]
        ))
        
        # Database metrics
        self._create_metric(MetricDefinition(
            name="database_connections",
            type="gauge",
            description="Active database connections",
            labels=["database"]
        ))
        
        self._create_metric(MetricDefinition(
            name="database_query_duration_seconds",
            type="histogram",
            description="Database query duration in seconds",
            labels=["query_type"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
        ))

    def _create_metric(self, definition: MetricDefinition) -> None:
        """Create Prometheus metric"""
        if definition.type == "gauge":
            metric = Gauge(
                definition.name,
                definition.description,
                definition.labels,
                registry=self.registry
            )
        elif definition.type == "counter":
            metric = Counter(
                definition.name,
                definition.description,
                definition.labels,
                registry=self.registry
            )
        elif definition.type == "histogram":
            metric = Histogram(
                definition.name,
                definition.description,
                definition.labels,
                buckets=definition.buckets,
                registry=self.registry
            )
        else:
            raise ValueError(f"Unknown metric type: {definition.type}")
            
        self._metrics[definition.name] = metric

    async def start_collection(self) -> None:
        """Start metrics collection"""
        self._collection_task = asyncio.create_task(self._collect_metrics())
        self.logger.info("Metrics collection started")

    async def stop_collection(self) -> None:
        """Stop metrics collection"""
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Metrics collection stopped")

    async def _collect_metrics(self) -> None:
        """Continuous metrics collection"""
        while True:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect application metrics
                await self._collect_application_metrics()
                
                # Sleep until next collection
                await asyncio.sleep(self.config.get('collection_interval', 15))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection failed: {str(e)}")
                await asyncio.sleep(5)

    async def _collect_system_metrics(self) -> None:
        """Collect system metrics"""
        # CPU metrics
        for cpu_num, cpu_percent in enumerate(psutil.cpu_percent(percpu=True)):
            self._metrics['system_cpu_usage'].labels(cpu=str(cpu_num)).set(
                cpu_percent
            )
            
        # Memory metrics
        memory = psutil.virtual_memory()
        self._metrics['system_memory_usage'].labels(type="total").set(
            memory.total
        )
        self._metrics['system_memory_usage'].labels(type="used").set(
            memory.used
        )
        self._metrics['system_memory_usage'].labels(type="available").set(
            memory.available
        )

    async def _collect_application_metrics(self) -> None:
        """Collect application-specific metrics"""
        # Implement application metrics collection
        pass

    def track_request(self,
                     endpoint: str,
                     method: str,
                     status: int,
                     duration: float) -> None:
        """Track API request metrics"""
        self._metrics['api_request_total'].labels(
            endpoint=endpoint,
            method=method,
            status=str(status)
        ).inc()
        
        self._metrics['api_request_duration_seconds'].labels(
            endpoint=endpoint
        ).observe(duration)

    def track_recognition(self,
                         model: str,
                         processing_time: float,
                         accuracy: float) -> None:
        """Track recognition metrics"""
        self._metrics['recognition_processing_time'].labels(
            model=model
        ).observe(processing_time)
        
        self._metrics['recognition_accuracy'].labels(
            model=model
        ).set(accuracy)

    def track_database_query(self,
                           query_type: str,
                           duration: float) -> None:
        """Track database query metrics"""
        self._metrics['database_query_duration_seconds'].labels(
            query_type=query_type
        ).observe(duration)

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        return prometheus_client.generate_latest(self.registry).decode('utf-8') 