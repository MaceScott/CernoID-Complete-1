from typing import Dict, List, Optional, Any, Union, Callable
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json
import psutil
import aioredis
import prometheus_client as prom
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
import socket
import platform
import os
import statistics
from collections import defaultdict

@dataclass
class MonitorConfig:
    """Monitoring configuration"""
    enabled: bool = True
    interval: int = 60  # seconds
    metrics_port: int = 9090
    history_size: int = 1000
    alert_thresholds: Dict[str, float] = None
    custom_metrics: List[Dict] = None
    enable_prometheus: bool = True
    enable_health_checks: bool = True
    retention_days: int = 7
    alert_callbacks: List[str] = None

class MonitoringManager:
    """System monitoring management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('MonitoringManager')
        self._monitor_config = MonitorConfig(**config.get('monitoring', {}))
        self._redis: Optional[aioredis.Redis] = None
        self._registry = CollectorRegistry()
        self._metrics: Dict[str, Any] = {}
        self._health_checks: Dict[str, Callable] = {}
        self._alert_history: List[Dict] = []
        self._collection_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._alert_callbacks: List[Callable] = []
        self._setup_metrics()

    async def initialize(self) -> None:
        """Initialize monitoring system"""
        try:
            if not self._monitor_config.enabled:
                self.logger.info("Monitoring system is disabled")
                return
                
            # Connect to Redis
            self._redis = await aioredis.create_redis_pool(
                self.config['redis_url']
            )
            
            # Start collection task
            self._collection_task = asyncio.create_task(
                self._collect_metrics()
            )
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(
                self._cleanup_old_data()
            )
            
            # Setup Prometheus metrics server if enabled
            if self._monitor_config.enable_prometheus:
                await self._setup_prometheus()
                
            # Register default health checks
            if self._monitor_config.enable_health_checks:
                self._register_default_health_checks()
                
            # Register alert callbacks
            await self._setup_alert_callbacks()
            
            self.logger.info("Monitoring system initialized")
            
        except Exception as e:
            self.logger.error(f"Monitoring initialization failed: {str(e)}")
            raise

    def _setup_metrics(self) -> None:
        """Setup monitoring metrics"""
        try:
            # System metrics
            self._metrics["cpu_usage"] = Gauge(
                "system_cpu_usage",
                "System CPU usage percentage",
                registry=self._registry
            )
            
            self._metrics["memory_usage"] = Gauge(
                "system_memory_usage",
                "System memory usage percentage",
                registry=self._registry
            )
            
            self._metrics["disk_usage"] = Gauge(
                "system_disk_usage",
                "System disk usage percentage",
                registry=self._registry
            )
            
            # Application metrics
            self._metrics["request_count"] = Counter(
                "app_request_count",
                "Total request count",
                ["method", "path"],
                registry=self._registry
            )
            
            self._metrics["request_latency"] = Histogram(
                "app_request_latency_seconds",
                "Request latency in seconds",
                ["method", "path"],
                registry=self._registry
            )
            
            self._metrics["error_count"] = Counter(
                "app_error_count",
                "Total error count",
                ["type"],
                registry=self._registry
            )
            
            # Custom metrics
            if self._monitor_config.custom_metrics:
                for metric in self._monitor_config.custom_metrics:
                    self._add_custom_metric(metric)
                    
        except Exception as e:
            self.logger.error(f"Metrics setup failed: {str(e)}")
            raise

    async def record_request(self,
                           method: str,
                           path: str,
                           duration: float,
                           status_code: int) -> None:
        """Record request metrics"""
        try:
            self._metrics["request_count"].labels(
                method=method,
                path=path
            ).inc()
            
            self._metrics["request_latency"].labels(
                method=method,
                path=path
            ).observe(duration)
            
            if status_code >= 400:
                self._metrics["error_count"].labels(
                    type=f"http_{status_code}"
                ).inc()
                
        except Exception as e:
            self.logger.error(f"Request recording failed: {str(e)}")

    async def add_health_check(self,
                             name: str,
                             check_func: Callable) -> None:
        """Add health check"""
        self._health_checks[name] = check_func
        self.logger.info(f"Added health check: {name}")

    async def get_health_status(self) -> Dict[str, bool]:
        """Get system health status"""
        try:
            status = {}
            for name, check in self._health_checks.items():
                try:
                    result = await check()
                    status[name] = result
                except Exception as e:
                    self.logger.error(
                        f"Health check failed - {name}: {str(e)}"
                    )
                    status[name] = False
            return status
            
        except Exception as e:
            self.logger.error(f"Health status check failed: {str(e)}")
            return {"error": False}

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        try:
            metrics = {}
            for name, metric in self._metrics.items():
                if isinstance(metric, (Counter, Gauge)):
                    metrics[name] = metric._value.get()
                elif isinstance(metric, Histogram):
                    metrics[name] = {
                        "count": metric._count.get(),
                        "sum": metric._sum.get(),
                        "buckets": metric._buckets
                    }
            return metrics
            
        except Exception as e:
            self.logger.error(f"Metrics retrieval failed: {str(e)}")
            return {}

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                "hostname": socket.gethostname(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage('/').total,
                "boot_time": datetime.fromtimestamp(
                    psutil.boot_time()
                ).isoformat(),
                "process_id": os.getpid(),
                "process_memory": psutil.Process().memory_info().rss,
                "thread_count": threading.active_count()
            }
        except Exception as e:
            self.logger.error(f"System info retrieval failed: {str(e)}")
            return {}

    async def cleanup(self) -> None:
        """Cleanup monitoring resources"""
        try:
            if self._collection_task:
                self._collection_task.cancel()
                
            if self._cleanup_task:
                self._cleanup_task.cancel()
                
            if self._redis:
                self._redis.close()
                await self._redis.wait_closed()
                
            self.logger.info("Monitoring system cleaned up")
            
        except Exception as e:
            self.logger.error(f"Monitoring cleanup failed: {str(e)}")

    def _add_custom_metric(self, metric_config: Dict) -> None:
        """Add custom metric"""
        try:
            metric_type = metric_config.get('type', 'counter')
            name = metric_config['name']
            description = metric_config.get(
                'description',
                f"Custom metric: {name}"
            )
            labels = metric_config.get('labels', [])
            
            if metric_type == 'counter':
                self._metrics[name] = Counter(
                    name,
                    description,
                    labels,
                    registry=self._registry
                )
            elif metric_type == 'gauge':
                self._metrics[name] = Gauge(
                    name,
                    description,
                    labels,
                    registry=self._registry
                )
            elif metric_type == 'histogram':
                buckets = metric_config.get('buckets', None)
                self._metrics[name] = Histogram(
                    name,
                    description,
                    labels,
                    buckets=buckets,
                    registry=self._registry
                )
                
        except Exception as e:
            self.logger.error(
                f"Custom metric addition failed - {name}: {str(e)}"
            )

    def _register_default_health_checks(self) -> None:
        """Register default health checks"""
        self._health_checks.update({
            "cpu": self._check_cpu_health,
            "memory": self._check_memory_health,
            "disk": self._check_disk_health,
            "redis": self._check_redis_health
        })

    async def _check_cpu_health(self) -> bool:
        """Check CPU health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            threshold = self._monitor_config.alert_thresholds.get(
                'cpu',
                90.0
            )
            return cpu_percent < threshold
        except Exception:
            return False

    async def _check_memory_health(self) -> bool:
        """Check memory health"""
        try:
            memory = psutil.virtual_memory()
            threshold = self._monitor_config.alert_thresholds.get(
                'memory',
                90.0
            )
            return memory.percent < threshold
        except Exception:
            return False

    async def _check_disk_health(self) -> bool:
        """Check disk health"""
        try:
            disk = psutil.disk_usage('/')
            threshold = self._monitor_config.alert_thresholds.get(
                'disk',
                90.0
            )
            return disk.percent < threshold
        except Exception:
            return False

    async def _check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            return await self._redis.ping()
        except Exception:
            return False

    async def _collect_metrics(self) -> None:
        """Collect system metrics periodically"""
        while True:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                self._metrics["cpu_usage"].set(cpu_percent)
                self._metrics["memory_usage"].set(memory.percent)
                self._metrics["disk_usage"].set(disk.percent)
                
                # Store historical data
                timestamp = datetime.utcnow().isoformat()
                historical_data = {
                    "timestamp": timestamp,
                    "cpu": cpu_percent,
                    "memory": memory.percent,
                    "disk": disk.percent
                }
                
                await self._redis.lpush(
                    "metrics_history",
                    json.dumps(historical_data)
                )
                
                # Check thresholds and trigger alerts
                await self._check_thresholds({
                    "cpu": cpu_percent,
                    "memory": memory.percent,
                    "disk": disk.percent
                })
                
                # Wait for next collection
                await asyncio.sleep(self._monitor_config.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection failed: {str(e)}")
                await asyncio.sleep(5)

    async def _cleanup_old_data(self) -> None:
        """Cleanup old monitoring data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Calculate cutoff time
                cutoff = datetime.utcnow() - timedelta(
                    days=self._monitor_config.retention_days
                )
                
                # Cleanup metrics history
                history = await self._redis.lrange(
                    "metrics_history",
                    0,
                    -1
                )
                for item in history:
                    data = json.loads(item)
                    if datetime.fromisoformat(
                        data["timestamp"]
                    ) < cutoff:
                        await self._redis.lrem(
                            "metrics_history",
                            1,
                            item
                        )
                        
                # Cleanup alert history
                self._alert_history = [
                    alert for alert in self._alert_history
                    if datetime.fromisoformat(
                        alert["timestamp"]
                    ) >= cutoff
                ]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Data cleanup failed: {str(e)}")
                await asyncio.sleep(60)

    async def _check_thresholds(self, metrics: Dict[str, float]) -> None:
        """Check metric thresholds and trigger alerts"""
        if not self._monitor_config.alert_thresholds:
            return
            
        for metric, value in metrics.items():
            threshold = self._monitor_config.alert_thresholds.get(metric)
            if threshold and value >= threshold:
                alert = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "metric": metric,
                    "value": value,
                    "threshold": threshold
                }
                
                self._alert_history.append(alert)
                await self._trigger_alert(alert)

    async def _trigger_alert(self, alert: Dict) -> None:
        """Trigger alert callbacks"""
        for callback in self._alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                self.logger.error(
                    f"Alert callback failed: {str(e)}"
                )

    async def _setup_prometheus(self) -> None:
        """Setup Prometheus metrics server"""
        try:
            from prometheus_client import start_http_server
            start_http_server(
                self._monitor_config.metrics_port,
                registry=self._registry
            )
            self.logger.info(
                f"Prometheus metrics server started on "
                f"port {self._monitor_config.metrics_port}"
            )
        except Exception as e:
            self.logger.error(
                f"Prometheus server setup failed: {str(e)}"
            )

    async def _setup_alert_callbacks(self) -> None:
        """Setup alert callbacks"""
        if not self._monitor_config.alert_callbacks:
            return
            
        for callback in self._monitor_config.alert_callbacks:
            try:
                module_name, func_name = callback.rsplit('.', 1)
                module = importlib.import_module(module_name)
                callback_func = getattr(module, func_name)
                self._alert_callbacks.append(callback_func)
            except Exception as e:
                self.logger.error(
                    f"Alert callback setup failed - {callback}: {str(e)}"
                ) 