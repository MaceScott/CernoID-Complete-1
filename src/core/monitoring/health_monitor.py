from typing import Dict, List, Optional
import asyncio
import time
from datetime import datetime
import psutil
import logging
from dataclasses import dataclass
import aiohttp

@dataclass
class HealthStatus:
    """System health status"""
    component: str
    status: str
    metrics: Dict
    last_check: datetime
    details: Optional[str] = None

class HealthMonitor:
    """System health monitoring and alerting"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('HealthMonitor')
        self._status_history: Dict[str, List[HealthStatus]] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_sent: Dict[str, datetime] = {}
        self._components = self._setup_components()

    async def start_monitoring(self) -> None:
        """Start health monitoring"""
        self._monitoring_task = asyncio.create_task(self._monitor_health())
        self.logger.info("Health monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop health monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Health monitoring stopped")

    async def get_health_status(self) -> Dict:
        """Get current system health status"""
        try:
            status = {
                "status": "healthy",
                "components": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for component in self._components:
                latest_status = await self._check_component(component)
                status["components"][component] = {
                    "status": latest_status.status,
                    "metrics": latest_status.metrics,
                    "last_check": latest_status.last_check.isoformat(),
                    "details": latest_status.details
                }
                
                if latest_status.status != "healthy":
                    status["status"] = "degraded"
                    
            return status
            
        except Exception as e:
            self.logger.error(f"Health status check failed: {str(e)}")
            raise

    def _setup_components(self) -> Dict:
        """Setup monitoring components"""
        return {
            "database": self._check_database,
            "redis": self._check_redis,
            "recognition_service": self._check_recognition_service,
            "api": self._check_api,
            "system": self._check_system_resources
        }

    async def _monitor_health(self) -> None:
        """Continuous health monitoring"""
        while True:
            try:
                for component, check_func in self._components.items():
                    status = await check_func()
                    
                    if component not in self._status_history:
                        self._status_history[component] = []
                        
                    self._status_history[component].append(status)
                    
                    # Keep last 24 hours of history
                    cutoff_time = datetime.utcnow().timestamp() - (24 * 3600)
                    self._status_history[component] = [
                        s for s in self._status_history[component]
                        if s.last_check.timestamp() > cutoff_time
                    ]
                    
                    # Check for alerts
                    await self._check_alerts(component, status)
                    
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring failed: {str(e)}")
                await asyncio.sleep(5)

    async def _check_database(self) -> HealthStatus:
        """Check database health"""
        try:
            # Implement database health check
            # Example: check connection and basic query
            start_time = time.time()
            # await db.execute("SELECT 1")
            response_time = time.time() - start_time
            
            return HealthStatus(
                component="database",
                status="healthy",
                metrics={
                    "response_time": response_time,
                    "connections": 10  # Example metric
                },
                last_check=datetime.utcnow()
            )
        except Exception as e:
            return HealthStatus(
                component="database",
                status="unhealthy",
                metrics={},
                last_check=datetime.utcnow(),
                details=str(e)
            )

    async def _check_system_resources(self) -> HealthStatus:
        """Check system resources"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                status = "warning"
            
            return HealthStatus(
                component="system",
                status=status,
                metrics={
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent,
                    "disk_usage": disk.percent
                },
                last_check=datetime.utcnow()
            )
        except Exception as e:
            return HealthStatus(
                component="system",
                status="unhealthy",
                metrics={},
                last_check=datetime.utcnow(),
                details=str(e)
            )

    async def _check_alerts(self, component: str, status: HealthStatus) -> None:
        """Check and send alerts if needed"""
        if status.status == "unhealthy":
            # Check if alert was recently sent
            last_alert = self._alert_sent.get(component)
            if not last_alert or \
               (datetime.utcnow() - last_alert).total_seconds() > 3600:
                await self._send_alert(component, status)
                self._alert_sent[component] = datetime.utcnow()

    async def _send_alert(self, component: str, status: HealthStatus) -> None:
        """Send health alert"""
        alert_message = (
            f"Health Alert: {component} is {status.status}\n"
            f"Time: {status.last_check.isoformat()}\n"
            f"Details: {status.details}\n"
            f"Metrics: {status.metrics}"
        )
        
        self.logger.warning(alert_message)
        # Implement alert notification system here 