from typing import Dict, List, Optional, Union, Tuple
import psutil
import asyncio
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import json
from pathlib import Path
import logging
import GPUtil
from sklearn.linear_model import LinearRegression
from collections import deque

from ..base import BaseComponent
from ..utils.errors import MonitorError
from ..metrics.metrics_collector import UnifiedMetricsCollector

@dataclass
class ResourcePrediction:
    """Resource usage prediction"""
    resource_type: str
    current_value: float
    predicted_value: float
    confidence: float
    time_horizon: timedelta
    trend: str  # 'increasing', 'decreasing', 'stable'

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    thread_count: int
    open_files: int
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
    metrics: Dict[str, float]
    alerts: List[str]
    recovery_attempts: int
    last_recovery: Optional[datetime]
    dependencies: List[str]

@dataclass
class SystemHealth:
    """Overall system health status"""
    status: str  # 'healthy', 'degraded', 'failed'
    components: Dict[str, ComponentHealth]
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    disk_usage: float
    uptime: timedelta
    last_check: datetime
    predictions: List[ResourcePrediction]
    error_count: Dict[str, int]
    performance_score: float

class SystemManager(BaseComponent):
    """System monitoring and health checking"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Monitoring settings
        self._check_interval = config.get('monitor.check_interval', 5)
        self._alert_threshold = config.get('monitor.alert_threshold', 0.8)
        self._degraded_threshold = config.get('monitor.degraded_threshold', 0.1)
        self._failed_threshold = config.get('monitor.failed_threshold', 0.3)
        
        # Resource thresholds
        self._cpu_threshold = config.get('monitor.cpu_threshold', 80)
        self._memory_threshold = config.get('monitor.memory_threshold', 80)
        self._disk_threshold = config.get('monitor.disk_threshold', 80)
        
        # Prediction settings
        self._prediction_window = config.get('monitor.prediction_window', 60)  # 1 hour
        self._prediction_horizon = config.get('monitor.prediction_horizon', 30)  # 30 minutes
        self._resource_history = {
            'cpu': deque(maxlen=self._prediction_window),
            'memory': deque(maxlen=self._prediction_window),
            'disk': deque(maxlen=self._prediction_window)
        }
        
        # Error tracking
        self._error_history: Dict[str, deque] = {}
        self._recovery_attempts: Dict[str, int] = {}
        self._max_recovery_attempts = config.get('monitor.max_recovery_attempts', 3)
        
        # Component dependencies
        self._component_dependencies = {
            'recognition': ['camera', 'storage'],
            'api': ['database', 'cache'],
            'security': ['database'],
            'storage': ['database']
        }
        
        # Initialize other attributes
        self._component_health: Dict[str, ComponentHealth] = {}
        self._system_health: List[SystemHealth] = []
        self._metrics = UnifiedMetricsCollector(config)
        self._setup_logging()
        
        # Monitoring state
        self._monitoring = False
        self._last_check = None
        self._alert_handlers = []
        self._alert_cooldown = config.get('monitor.alert_cooldown', 300)
        self._last_alert: Dict[str, datetime] = {}

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
            
            # Start metrics collection
            await self._metrics.start_collection()
            
            # Start monitoring tasks
            asyncio.create_task(self._check_components())
            asyncio.create_task(self._process_alerts())
            
            self.logger.info("System monitoring started")
            
        except Exception as e:
            raise MonitorError(f"Failed to start monitoring: {str(e)}")

    async def stop_monitoring(self) -> None:
        """Stop system monitoring"""
        self._monitoring = False
        await self._metrics.stop_collection()
        self.logger.info("System monitoring stopped")

    async def _check_components(self) -> None:
        """Check health of system components"""
        while self._monitoring:
            try:
                components = [
                    'recognition',
                    'camera',
                    'security',
                    'storage',
                    'api',
                    'database',
                    'cache'
                ]
                
                for component in components:
                    health = await self._check_component_health(component)
                    self._component_health[component] = health
                    
                    # Update metrics
                    self._metrics.track_component_health(
                        component,
                        health.status,
                        health.latency,
                        health.error_rate
                    )
                
                # Check system health
                await self._check_system_health()
                
                # Wait for next check
                await asyncio.sleep(self._check_interval)
                
            except Exception as e:
                self.logger.error(f"Component health check failed: {str(e)}")
                await asyncio.sleep(1)

    async def _predict_resource_usage(self, resource_type: str) -> ResourcePrediction:
        """Predict future resource usage"""
        try:
            history = list(self._resource_history[resource_type])
            if len(history) < 10:  # Need minimum data points
                return None
                
            X = np.array(range(len(history))).reshape(-1, 1)
            y = np.array(history)
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict next value
            next_point = np.array([[len(history)]])
            predicted_value = model.predict(next_point)[0]
            
            # Calculate confidence and trend
            confidence = model.score(X, y)
            trend = 'stable'
            if model.coef_[0] > 0.1:
                trend = 'increasing'
            elif model.coef_[0] < -0.1:
                trend = 'decreasing'
                
            return ResourcePrediction(
                resource_type=resource_type,
                current_value=history[-1],
                predicted_value=predicted_value,
                confidence=confidence,
                time_horizon=timedelta(minutes=self._prediction_horizon),
                trend=trend
            )
            
        except Exception as e:
            self.logger.error(f"Resource prediction failed: {str(e)}")
            return None

    async def _check_component_health(self, component: str) -> ComponentHealth:
        """Check health of specific component"""
        try:
            start_time = datetime.utcnow()
            alerts = []
            
            # Get component stats
            comp = getattr(self.app, component, None)
            if not comp:
                return ComponentHealth(
                    name=component,
                    status='failed',
                    latency=0.0,
                    error_rate=1.0,
                    last_error=f"Component {component} not found",
                    last_check=datetime.utcnow(),
                    metrics={},
                    alerts=["Component not found"],
                    recovery_attempts=0,
                    last_recovery=None,
                    dependencies=self._component_dependencies.get(component, [])
                )
            
            # Check dependencies
            for dep in self._component_dependencies.get(component, []):
                dep_health = self._component_health.get(dep)
                if dep_health and dep_health.status == 'failed':
                    alerts.append(f"Dependency {dep} has failed")
            
            stats = await comp.get_stats()
            metrics = await comp.get_metrics()
            
            # Calculate latency and error rate
            latency = (datetime.utcnow() - start_time).total_seconds()
            error_rate = stats.get('error_rate', 0)
            
            # Track errors
            if component not in self._error_history:
                self._error_history[component] = deque(maxlen=100)
            if error_rate > self._alert_threshold:
                self._error_history[component].append({
                    'timestamp': datetime.utcnow(),
                    'error_rate': error_rate,
                    'latency': latency
                })
            
            # Check for recurring errors
            if len(self._error_history[component]) > 5:
                alerts.append("Recurring errors detected")
            
            # Resource checks
            if stats.get('memory_usage', 0) > self._alert_threshold:
                alerts.append("High memory usage")
            if stats.get('cpu_usage', 0) > self._alert_threshold:
                alerts.append("High CPU usage")
            
            # Determine status
            status = 'healthy'
            if error_rate > self._degraded_threshold or alerts:
                status = 'degraded'
            if error_rate > self._failed_threshold:
                status = 'failed'
            
            # Update recovery attempts
            recovery_attempts = self._recovery_attempts.get(component, 0)
            last_recovery = None
            if status == 'failed':
                if recovery_attempts < self._max_recovery_attempts:
                    try:
                        await comp.recover()
                        last_recovery = datetime.utcnow()
                        self._recovery_attempts[component] = recovery_attempts + 1
                    except Exception as e:
                        alerts.append(f"Recovery failed: {str(e)}")
            
            return ComponentHealth(
                name=component,
                status=status,
                latency=latency,
                error_rate=error_rate,
                last_error=stats.get('last_error'),
                last_check=datetime.utcnow(),
                metrics=metrics,
                alerts=alerts,
                recovery_attempts=recovery_attempts,
                last_recovery=last_recovery,
                dependencies=self._component_dependencies.get(component, [])
            )
            
        except Exception as e:
            return ComponentHealth(
                name=component,
                status='failed',
                latency=0.0,
                error_rate=1.0,
                last_error=str(e),
                last_check=datetime.utcnow(),
                metrics={},
                alerts=[str(e)],
                recovery_attempts=self._recovery_attempts.get(component, 0),
                last_recovery=None,
                dependencies=self._component_dependencies.get(component, [])
            )

    async def _check_system_health(self) -> None:
        """Check overall system health"""
        try:
            # Get metrics from collector
            metrics = await self._metrics.get_metrics()
            
            # Update resource history
            self._resource_history['cpu'].append(metrics.get('cpu_usage', {}).get('value', 0))
            self._resource_history['memory'].append(metrics.get('memory_usage', {}).get('value', 0))
            self._resource_history['disk'].append(metrics.get('disk_usage', {}).get('value', 0))
            
            # Get resource predictions
            predictions = []
            for resource in ['cpu', 'memory', 'disk']:
                pred = await self._predict_resource_usage(resource)
                if pred:
                    predictions.append(pred)
            
            # Calculate uptime
            uptime = datetime.utcnow() - self._last_check if self._last_check else timedelta()
            
            # Count errors by type
            error_count: Dict[str, int] = {}
            for component in self._component_health.values():
                if component.last_error:
                    error_type = type(component.last_error).__name__
                    error_count[error_type] = error_count.get(error_type, 0) + 1
            
            # Calculate performance score
            total_components = len(self._component_health)
            healthy_components = len([c for c in self._component_health.values() if c.status == 'healthy'])
            avg_latency = np.mean([c.latency for c in self._component_health.values()])
            avg_error_rate = np.mean([c.error_rate for c in self._component_health.values()])
            
            performance_score = (
                (healthy_components / total_components) * 0.4 +
                (1 - min(avg_latency, 1.0)) * 0.3 +
                (1 - avg_error_rate) * 0.3
            ) * 100
            
            # Determine system status
            status = 'healthy'
            failed_components = [c for c in self._component_health.values() if c.status == 'failed']
            degraded_components = [c for c in self._component_health.values() if c.status == 'degraded']
            
            if failed_components:
                status = 'failed'
            elif degraded_components:
                status = 'degraded'
            
            # Create health snapshot
            health = SystemHealth(
                status=status,
                components=self._component_health.copy(),
                cpu_usage=metrics.get('cpu_usage', {}).get('value', 0),
                memory_usage=metrics.get('memory_usage', {}).get('value', 0),
                gpu_usage=metrics.get('gpu_usage', {}).get('value', None),
                disk_usage=metrics.get('disk_usage', {}).get('value', 0),
                uptime=uptime,
                last_check=datetime.utcnow(),
                predictions=predictions,
                error_count=error_count,
                performance_score=performance_score
            )
            
            # Update history
            self._system_health.append(health)
            if len(self._system_health) > 1000:
                self._system_health.pop(0)
            
        except Exception as e:
            self.logger.error(f"System health check failed: {str(e)}")

    async def _process_alerts(self) -> None:
        """Process system alerts"""
        while self._monitoring:
            try:
                current_time = datetime.utcnow()
                
                # Check component alerts
                for component in self._component_health.values():
                    if component.alerts:
                        # Check alert cooldown
                        last_alert = self._last_alert.get(component.name)
                        if (not last_alert or 
                            (current_time - last_alert).total_seconds() > self._alert_cooldown):
                            # Process alerts
                            for alert in component.alerts:
                                await self._handle_alert(component.name, alert)
                            
                            # Update last alert time
                            self._last_alert[component.name] = current_time
                
                # Check system alerts
                if self._system_health:
                    latest = self._system_health[-1]
                    if latest.status != 'healthy':
                        alert = f"System status: {latest.status}"
                        if (not self._last_alert.get('system') or
                            (current_time - self._last_alert['system']).total_seconds() > self._alert_cooldown):
                            await self._handle_alert('system', alert)
                            self._last_alert['system'] = current_time
                
                await asyncio.sleep(self._check_interval)
                
            except Exception as e:
                self.logger.error(f"Alert processing failed: {str(e)}")
                await asyncio.sleep(1)

    async def _handle_alert(self, component: str, message: str) -> None:
        """Handle system alert"""
        try:
            # Log alert with context
            context = {
                'component': component,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'system_status': self._system_health[-1].status if self._system_health else 'unknown',
                'component_health': self._component_health.get(component, {})
            }
            
            self.logger.warning(f"Alert: {json.dumps(context, default=str)}")
            
            # Track in metrics
            self._metrics.track_error(
                error_type='alert',
                component=component
            )
            
            # Save to file with rotation
            alert_file = Path('logs/alerts.jsonl')
            alert_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Rotate files if too large
            if alert_file.exists() and alert_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
                backup = alert_file.with_suffix('.jsonl.1')
                if backup.exists():
                    backup.unlink()
                alert_file.rename(backup)
            
            with open(alert_file, 'a') as f:
                f.write(json.dumps(context, default=str) + '\n')
            
            # Notify alert handlers
            for handler in self._alert_handlers:
                try:
                    await handler(context)
                except Exception as e:
                    self.logger.error(f"Alert handler failed: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Alert handling failed: {str(e)}")

    async def get_component_status(self) -> Dict[str, ComponentHealth]:
        """Get status of all components"""
        return self._component_health.copy()

    async def get_health(self) -> Optional[SystemHealth]:
        """Get latest system health status"""
        if not self._system_health:
            return None
        return self._system_health[-1]

    async def get_health_history(self,
                               start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None,
                               include_predictions: bool = False) -> List[SystemHealth]:
        """Get system health history with optional predictions"""
        if not start_time:
            start_time = datetime.min
        if not end_time:
            end_time = datetime.max
            
        history = [
            h for h in self._system_health
            if start_time <= h.last_check <= end_time
        ]
        
        if include_predictions and history:
            # Add predictions for requested metrics
            latest = history[-1]
            predictions = []
            for resource in ['cpu', 'memory', 'disk']:
                pred = await self._predict_resource_usage(resource)
                if pred:
                    predictions.append(pred)
            latest.predictions = predictions
            
        return history

    def add_alert_handler(self, handler: callable) -> None:
        """Add custom alert handler"""
        self._alert_handlers.append(handler)

    def remove_alert_handler(self, handler: callable) -> None:
        """Remove custom alert handler"""
        if handler in self._alert_handlers:
            self._alert_handlers.remove(handler) 