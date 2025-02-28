from typing import Dict, List, Optional, Union
import psutil
import asyncio
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import json
from pathlib import Path
import logging

from ..base import BaseComponent
from ..utils.errors import MonitorError

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    disk_usage: float
    network_io: Dict[str, float]
    timestamp: datetime

@dataclass
class ComponentHealth:
    """Component health status"""
    name: str
    status: str  # 'healthy', 'degraded', 'failed'
    latency: float
    error_rate: float
    last_error: Optional[str]
    last_check: datetime

class SystemMonitor(BaseComponent):
    """System monitoring and health checking"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Monitoring settings
        self._check_interval = config.get('monitor.check_interval', 5)
        self._history_size = config.get('monitor.history_size', 1000)
        self._alert_threshold = config.get('monitor.alert_threshold', 0.8)
        
        # Performance history
        self._metrics_history: List[SystemMetrics] = []
        self._component_health: Dict[str, ComponentHealth] = {}
        
        # Resource thresholds
        self._cpu_threshold = config.get('monitor.cpu_threshold', 80)
        self._memory_threshold = config.get('monitor.memory_threshold', 80)
        self._disk_threshold = config.get('monitor.disk_threshold', 80)
        
        # Initialize GPU monitoring if available
        self._gpu_available = self._init_gpu_monitoring()
        
        # Performance logging
        self._setup_logging()
        
        # Monitoring state
        self._monitoring = False
        self._last_check = None
        
        # Statistics
        self._stats = {
            'checks_performed': 0,
            'alerts_generated': 0,
            'components_monitored': 0,
            'average_latency': 0.0
        }

    def _init_gpu_monitoring(self) -> bool:
        """Initialize GPU monitoring if available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _setup_logging(self) -> None:
        """Setup performance logging"""
        log_path = Path('logs/performance.log')
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    async def start_monitoring(self) -> None:
        """Start system monitoring"""
        try:
            if self._monitoring:
                return
                
            self._monitoring = True
            self._last_check = datetime.utcnow()
            
            # Start monitoring tasks
            asyncio.create_task(self._monitor_system())
            asyncio.create_task(self._check_components())
            
            self.logger.info("System monitoring started")
            
        except Exception as e:
            raise MonitorError(f"Failed to start monitoring: {str(e)}")

    async def stop_monitoring(self) -> None:
        """Stop system monitoring"""
        self._monitoring = False
        self.logger.info("System monitoring stopped")

    async def _monitor_system(self) -> None:
        """Monitor system resources"""
        while self._monitoring:
            try:
                # Collect system metrics
                metrics = await self._collect_metrics()
                
                # Store metrics
                self._metrics_history.append(metrics)
                if len(self._metrics_history) > self._history_size:
                    self._metrics_history.pop(0)
                
                # Check thresholds
                await self._check_thresholds(metrics)
                
                # Update statistics
                self._stats['checks_performed'] += 1
                
                # Log metrics
                self._log_metrics(metrics)
                
                # Wait for next check
                await asyncio.sleep(self._check_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {str(e)}")
                await asyncio.sleep(1)

    async def _collect_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # GPU usage if available
            gpu_usage = None
            if self._gpu_available:
                gpu_usage = self._get_gpu_usage()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv
            }
            
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                gpu_usage=gpu_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            raise MonitorError(f"Failed to collect metrics: {str(e)}")

    def _get_gpu_usage(self) -> Optional[float]:
        """Get GPU usage if available"""
        try:
            import torch
            if torch.cuda.is_available():
                # This is a simplified version - implement proper GPU monitoring
                return torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()
            return None
        except Exception:
            return None

    async def _check_thresholds(self, metrics: SystemMetrics) -> None:
        """Check resource thresholds and generate alerts"""
        try:
            alerts = []
            
            # Check CPU usage
            if metrics.cpu_usage > self._cpu_threshold:
                alerts.append({
                    'type': 'high_cpu',
                    'value': metrics.cpu_usage,
                    'threshold': self._cpu_threshold
                })
            
            # Check memory usage
            if metrics.memory_usage > self._memory_threshold:
                alerts.append({
                    'type': 'high_memory',
                    'value': metrics.memory_usage,
                    'threshold': self._memory_threshold
                })
            
            # Check disk usage
            if metrics.disk_usage > self._disk_threshold:
                alerts.append({
                    'type': 'high_disk',
                    'value': metrics.disk_usage,
                    'threshold': self._disk_threshold
                })
            
            # Generate alerts
            for alert in alerts:
                await self._generate_alert(alert)
                self._stats['alerts_generated'] += 1
                
        except Exception as e:
            self.logger.error(f"Threshold check failed: {str(e)}")

    async def _check_components(self) -> None:
        """Check health of system components"""
        while self._monitoring:
            try:
                components = [
                    'recognition',
                    'camera',
                    'security',
                    'storage',
                    'api'
                ]
                
                for component in components:
                    health = await self._check_component_health(component)
                    self._component_health[component] = health
                
                self._stats['components_monitored'] = len(components)
                
                # Wait for next check
                await asyncio.sleep(self._check_interval * 2)
                
            except Exception as e:
                self.logger.error(f"Component health check failed: {str(e)}")
                await asyncio.sleep(1)

    async def _check_component_health(self, component: str) -> ComponentHealth:
        """Check health of specific component"""
        try:
            start_time = datetime.utcnow()
            
            # Get component stats
            stats = await getattr(self.app, component).get_stats()
            
            # Calculate latency
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            # Determine status
            status = 'healthy'
            error_rate = stats.get('error_rate', 0)
            last_error = stats.get('last_error')
            
            if error_rate > 0.1:  # 10% error rate threshold
                status = 'degraded'
            if error_rate > 0.3:  # 30% error rate threshold
                status = 'failed'
            
            return ComponentHealth(
                name=component,
                status=status,
                latency=latency,
                error_rate=error_rate,
                last_error=last_error,
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            return ComponentHealth(
                name=component,
                status='failed',
                latency=0.0,
                error_rate=1.0,
                last_error=str(e),
                last_check=datetime.utcnow()
            )

    async def _generate_alert(self, alert_data: Dict) -> None:
        """Generate system alert"""
        try:
            alert = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': f"system_{alert_data['type']}",
                'value': alert_data['value'],
                'threshold': alert_data['threshold'],
                'severity': 'warning'
            }
            
            # Log alert
            self.logger.warning(f"System alert: {json.dumps(alert)}")
            
            # Send to alert system
            await self.app.alerts.send_alert(alert)
            
        except Exception as e:
            self.logger.error(f"Failed to generate alert: {str(e)}")

    def _log_metrics(self, metrics: SystemMetrics) -> None:
        """Log system metrics"""
        try:
            log_data = {
                'timestamp': metrics.timestamp.isoformat(),
                'cpu': metrics.cpu_usage,
                'memory': metrics.memory_usage,
                'disk': metrics.disk_usage,
                'network': metrics.network_io
            }
            if metrics.gpu_usage is not None:
                log_data['gpu'] = metrics.gpu_usage
                
            self.logger.info(f"System metrics: {json.dumps(log_data)}")
            
        except Exception as e:
            self.logger.error(f"Failed to log metrics: {str(e)}")

    async def get_metrics(self,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[SystemMetrics]:
        """Get historical metrics"""
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=1)
            if not end_time:
                end_time = datetime.utcnow()
                
            metrics = [
                m for m in self._metrics_history
                if start_time <= m.timestamp <= end_time
            ]
            
            return metrics
            
        except Exception as e:
            raise MonitorError(f"Failed to get metrics: {str(e)}")

    async def get_component_status(self) -> Dict[str, ComponentHealth]:
        """Get status of all components"""
        return self._component_health.copy()

    async def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        return self._stats.copy() 