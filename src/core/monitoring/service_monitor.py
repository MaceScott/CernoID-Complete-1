from typing import Dict, List, Optional
import asyncio
import time
from datetime import datetime
import psutil
import logging
from dataclasses import dataclass

@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    service_name: str
    cpu_usage: float
    memory_usage: float
    request_count: int
    error_count: int
    average_response_time: float
    timestamp: datetime

class ServiceMonitor:
    """Service monitoring and metrics collection"""
    
    def __init__(self):
        self.logger = logging.getLogger('ServiceMonitor')
        self._metrics: Dict[str, List[ServiceMetrics]] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_thresholds = {
            'cpu_usage': 80.0,  # percent
            'memory_usage': 80.0,  # percent
            'error_rate': 5.0,  # percent
            'response_time': 1.0  # seconds
        }

    async def start_monitoring(self) -> None:
        """Start service monitoring"""
        self._monitoring_task = asyncio.create_task(self._monitor_services())
        self.logger.info("Service monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop service monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Service monitoring stopped")

    async def get_service_metrics(self, service_name: str) -> List[ServiceMetrics]:
        """Get metrics for specific service"""
        return self._metrics.get(service_name, [])

    async def get_system_health(self) -> Dict:
        """Get overall system health status"""
        try:
            current_metrics = {
                service: metrics[-1] 
                for service, metrics in self._metrics.items() 
                if metrics
            }
            
            return {
                'status': self._calculate_health_status(current_metrics),
                'services': {
                    service: self._get_service_health(metrics)
                    for service, metrics in current_metrics.items()
                },
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            raise

    async def _monitor_services(self) -> None:
        """Continuous service monitoring"""
        while True:
            try:
                for service_name in self._get_active_services():
                    metrics = await self._collect_service_metrics(service_name)
                    self._store_metrics(service_name, metrics)
                    await self._check_alerts(service_name, metrics)
                    
                await asyncio.sleep(60)  # Collect metrics every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring failed: {str(e)}")
                await asyncio.sleep(5)  # Wait before retry

    async def _collect_service_metrics(self, service_name: str) -> ServiceMetrics:
        """Collect service performance metrics"""
        try:
            process = psutil.Process()
            
            return ServiceMetrics(
                service_name=service_name,
                cpu_usage=process.cpu_percent(),
                memory_usage=process.memory_percent(),
                request_count=self._get_request_count(service_name),
                error_count=self._get_error_count(service_name),
                average_response_time=self._get_average_response_time(service_name),
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {str(e)}")
            raise

    def _store_metrics(self, service_name: str, metrics: ServiceMetrics) -> None:
        """Store service metrics"""
        if service_name not in self._metrics:
            self._metrics[service_name] = []
            
        self._metrics[service_name].append(metrics)
        
        # Keep last 24 hours of metrics
        max_metrics = 24 * 60  # 24 hours * 60 minutes
        if len(self._metrics[service_name]) > max_metrics:
            self._metrics[service_name] = self._metrics[service_name][-max_metrics:]

    async def _check_alerts(self, service_name: str, metrics: ServiceMetrics) -> None:
        """Check metrics against alert thresholds"""
        alerts = []
        
        if metrics.cpu_usage > self._alert_thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {metrics.cpu_usage}%")
            
        if metrics.memory_usage > self._alert_thresholds['memory_usage']:
            alerts.append(f"High memory usage: {metrics.memory_usage}%")
            
        error_rate = (metrics.error_count / metrics.request_count * 100 
                     if metrics.request_count > 0 else 0)
        if error_rate > self._alert_thresholds['error_rate']:
            alerts.append(f"High error rate: {error_rate}%")
            
        if metrics.average_response_time > self._alert_thresholds['response_time']:
            alerts.append(f"High response time: {metrics.average_response_time}s")
            
        if alerts:
            await self._send_alerts(service_name, alerts)

    async def _send_alerts(self, service_name: str, alerts: List[str]) -> None:
        """Send service alerts"""
        for alert in alerts:
            self.logger.warning(f"Service {service_name} alert: {alert}")
            # Implement alert notification system here 