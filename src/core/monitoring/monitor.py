from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from datetime import datetime, timedelta
import asyncio
import psutil
import GPUtil
from dataclasses import dataclass
import json
import aiohttp
from collections import deque
import logging
import threading
from pathlib import Path

from ..base import BaseComponent
from ..utils.errors import MonitoringError

@dataclass
class SystemMetrics:
    """System monitoring metrics"""
    cpu_usage: float
    memory_usage: float
    gpu_usage: float
    gpu_memory: float
    disk_usage: float
    network_io: Tuple[float, float]  # upload, download
    processing_rate: float  # faces/second
    queue_sizes: Dict[str, int]
    error_rate: float
    latency: float
    timestamp: datetime

class SystemMonitor(BaseComponent):
    """Real-time system monitoring"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Monitoring settings
        self._interval = config.get('monitoring.interval', 1.0)  # seconds
        self._history_size = config.get('monitoring.history_size', 3600)  # 1 hour
        self._alert_threshold = config.get('monitoring.alert_threshold', 0.9)
        
        # Metrics storage
        self._metrics_history: deque = deque(maxlen=self._history_size)
        self._error_history: deque = deque(maxlen=1000)
        self._alert_history: deque = deque(maxlen=100)
        
        # Performance tracking
        self._face_count = 0
        self._error_count = 0
        self._last_check = datetime.utcnow()
        self._processing_times: deque = deque(maxlen=100)
        
        # Component status
        self._component_status: Dict[str, bool] = {
            'recognition': False,
            'camera': False,
            'database': False,
            'api': False
        }
        
        # Alert settings
        self._alert_webhooks = config.get('monitoring.webhooks', [])
        self._alert_enabled = config.get('monitoring.alerts_enabled', True)
        
        # Initialize monitoring
        self._initialize_monitoring()
        
        # Statistics
        self._stats = {
            'uptime': 0,
            'total_processed': 0,
            'total_errors': 0,
            'average_latency': 0.0,
            'peak_memory': 0.0,
            'peak_gpu': 0.0
        }

    def _initialize_monitoring(self) -> None:
        """Initialize monitoring system"""
        try:
            # Create metrics directory
            metrics_path = Path('data/metrics')
            metrics_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize logging
            self._setup_logging()
            
            # Start monitoring loop
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # Start component checker
            self._checker_task = asyncio.create_task(self._check_components())
            
        except Exception as e:
            raise MonitoringError(f"Monitor initialization failed: {str(e)}")

    def _setup_logging(self) -> None:
        """Setup monitoring logs"""
        try:
            # Configure logger
            log_path = Path('logs/monitoring.log')
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)
            
        except Exception as e:
            raise MonitoringError(f"Log setup failed: {str(e)}")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while True:
            try:
                # Collect metrics
                metrics = await self._collect_metrics()
                
                # Store metrics
                self._metrics_history.append(metrics)
                
                # Check thresholds
                await self._check_thresholds(metrics)
                
                # Update statistics
                self._update_stats(metrics)
                
                # Save metrics to disk periodically
                if len(self._metrics_history) % 60 == 0:
                    await self._save_metrics()
                
                # Wait for next interval
                await asyncio.sleep(self._interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(1.0)

    async def _collect_metrics(self) -> SystemMetrics:
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_usage = psutil.cpu_percent() / 100.0
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100.0
            
            # GPU metrics
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_usage = gpu.load
                gpu_memory = gpu.memoryUtil
            else:
                gpu_usage = 0.0
                gpu_memory = 0.0
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent / 100.0
            
            # Network metrics
            net = psutil.net_io_counters()
            network_io = (
                net.bytes_sent / 1024 / 1024,  # MB
                net.bytes_recv / 1024 / 1024   # MB
            )
            
            # Processing metrics
            now = datetime.utcnow()
            time_diff = (now - self._last_check).total_seconds()
            processing_rate = self._face_count / time_diff if time_diff > 0 else 0
            
            # Reset counters
            self._face_count = 0
            self._last_check = now
            
            # Queue sizes
            queue_sizes = await self._get_queue_sizes()
            
            # Error rate
            error_rate = self._error_count / max(1, self._face_count)
            self._error_count = 0
            
            # Latency
            latency = np.mean(self._processing_times) if self._processing_times else 0.0
            
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                gpu_usage=gpu_usage,
                gpu_memory=gpu_memory,
                disk_usage=disk_usage,
                network_io=network_io,
                processing_rate=processing_rate,
                queue_sizes=queue_sizes,
                error_rate=error_rate,
                latency=latency,
                timestamp=now
            )
            
        except Exception as e:
            raise MonitoringError(f"Metrics collection failed: {str(e)}")

    async def _check_components(self) -> None:
        """Check component status"""
        while True:
            try:
                # Check recognition service
                self._component_status['recognition'] = \
                    await self._check_service('recognition', 8000)
                
                # Check camera service
                self._component_status['camera'] = \
                    await self._check_service('camera', 8001)
                
                # Check database
                self._component_status['database'] = \
                    await self._check_database()
                
                # Check API
                self._component_status['api'] = \
                    await self._check_service('api', 8002)
                
                # Log status changes
                for component, status in self._component_status.items():
                    if not status:
                        self.logger.warning(f"{component} service is down")
                
                # Wait before next check
                await asyncio.sleep(5.0)
                
            except Exception as e:
                self.logger.error(f"Component check error: {str(e)}")
                await asyncio.sleep(1.0)

    async def _check_service(self, name: str, port: int) -> bool:
        """Check if service is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{port}/health") as response:
                    return response.status == 200
        except Exception:
            return False

    async def _check_database(self) -> bool:
        """Check database connection"""
        try:
            # Implement database check
            return True
        except Exception:
            return False

    async def _check_thresholds(self, metrics: SystemMetrics) -> None:
        """Check metric thresholds and send alerts"""
        try:
            alerts = []
            
            # Check CPU usage
            if metrics.cpu_usage > self._alert_threshold:
                alerts.append(f"High CPU usage: {metrics.cpu_usage*100:.1f}%")
            
            # Check memory usage
            if metrics.memory_usage > self._alert_threshold:
                alerts.append(f"High memory usage: {metrics.memory_usage*100:.1f}%")
            
            # Check GPU usage
            if metrics.gpu_usage > self._alert_threshold:
                alerts.append(f"High GPU usage: {metrics.gpu_usage*100:.1f}%")
            
            # Check error rate
            if metrics.error_rate > 0.1:  # 10% error rate
                alerts.append(f"High error rate: {metrics.error_rate*100:.1f}%")
            
            # Check processing rate
            if metrics.processing_rate < 1.0:  # Less than 1 face/second
                alerts.append(f"Low processing rate: {metrics.processing_rate:.1f} faces/s")
            
            # Send alerts if enabled
            if alerts and self._alert_enabled:
                await self._send_alerts(alerts)
            
        except Exception as e:
            self.logger.error(f"Threshold check failed: {str(e)}")

    async def _send_alerts(self, alerts: List[str]) -> None:
        """Send monitoring alerts"""
        try:
            # Create alert message
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'alerts': alerts,
                'metrics': self._get_current_metrics()
            }
            
            # Store alert
            self._alert_history.append(message)
            
            # Send to webhooks
            if self._alert_webhooks:
                async with aiohttp.ClientSession() as session:
                    for webhook in self._alert_webhooks:
                        try:
                            await session.post(
                                webhook,
                                json=message,
                                timeout=5.0
                            )
                        except Exception as e:
                            self.logger.error(f"Webhook alert failed: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Alert sending failed: {str(e)}")

    async def _save_metrics(self) -> None:
        """Save metrics to disk"""
        try:
            # Convert metrics to JSON
            metrics_data = [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'cpu_usage': m.cpu_usage,
                    'memory_usage': m.memory_usage,
                    'gpu_usage': m.gpu_usage,
                    'gpu_memory': m.gpu_memory,
                    'disk_usage': m.disk_usage,
                    'network_io': m.network_io,
                    'processing_rate': m.processing_rate,
                    'queue_sizes': m.queue_sizes,
                    'error_rate': m.error_rate,
                    'latency': m.latency
                }
                for m in self._metrics_history
            ]
            
            # Save to file
            metrics_file = Path('data/metrics/system_metrics.json')
            async with aiofiles.open(metrics_file, 'w') as f:
                await f.write(json.dumps(metrics_data, indent=2))
            
        except Exception as e:
            self.logger.error(f"Metrics save failed: {str(e)}")

    def _update_stats(self, metrics: SystemMetrics) -> None:
        """Update monitoring statistics"""
        try:
            # Update uptime
            self._stats['uptime'] = (
                datetime.utcnow() - self._start_time
            ).total_seconds()
            
            # Update processing stats
            self._stats['total_processed'] += metrics.processing_rate * self._interval
            
            # Update error stats
            if metrics.error_rate > 0:
                self._stats['total_errors'] += 1
            
            # Update latency
            n = len(self._processing_times)
            if n > 0:
                self._stats['average_latency'] = np.mean(self._processing_times)
            
            # Update peak usage
            self._stats['peak_memory'] = max(
                self._stats['peak_memory'],
                metrics.memory_usage
            )
            self._stats['peak_gpu'] = max(
                self._stats['peak_gpu'],
                metrics.gpu_usage
            )
            
        except Exception as e:
            self.logger.error(f"Stats update failed: {str(e)}")

    async def get_metrics(self,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[SystemMetrics]:
        """Get system metrics"""
        try:
            if start_time is None and end_time is None:
                return list(self._metrics_history)
            
            # Filter by time range
            metrics = [
                m for m in self._metrics_history
                if (start_time is None or m.timestamp >= start_time) and
                   (end_time is None or m.timestamp <= end_time)
            ]
            
            return metrics
            
        except Exception as e:
            raise MonitoringError(f"Failed to get metrics: {str(e)}")

    def _get_current_metrics(self) -> Dict:
        """Get current system metrics"""
        try:
            if not self._metrics_history:
                return {}
            
            metrics = self._metrics_history[-1]
            return {
                'cpu_usage': metrics.cpu_usage,
                'memory_usage': metrics.memory_usage,
                'gpu_usage': metrics.gpu_usage,
                'gpu_memory': metrics.gpu_memory,
                'processing_rate': metrics.processing_rate,
                'error_rate': metrics.error_rate,
                'latency': metrics.latency
            }
            
        except Exception:
            return {}

    async def get_component_status(self) -> Dict[str, bool]:
        """Get component status"""
        return self._component_status.copy()

    async def get_alerts(self,
                        start_time: Optional[datetime] = None) -> List[Dict]:
        """Get monitoring alerts"""
        try:
            if start_time is None:
                return list(self._alert_history)
            
            # Filter by time
            alerts = [
                a for a in self._alert_history
                if datetime.fromisoformat(a['timestamp']) >= start_time
            ]
            
            return alerts
            
        except Exception as e:
            raise MonitoringError(f"Failed to get alerts: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        return self._stats.copy() 