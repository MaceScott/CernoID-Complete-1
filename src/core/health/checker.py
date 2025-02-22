from typing import Dict, List, Optional, Callable, Any
import asyncio
import psutil
import socket
from datetime import datetime
from ..base import BaseComponent
from ..utils.errors import handle_errors

class HealthChecker(BaseComponent):
    """System health and diagnostics checker"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._checks: Dict[str, Callable] = {}
        self._results: Dict[str, Dict] = {}
        self._check_interval = self.config.get('health.interval', 60)
        self._history_size = self.config.get('health.history_size', 100)
        self._thresholds = {
            'cpu': self.config.get('health.threshold.cpu', 80),
            'memory': self.config.get('health.threshold.memory', 80),
            'disk': self.config.get('health.threshold.disk', 80)
        }

    async def initialize(self) -> None:
        """Initialize health checker"""
        # Register default checks
        self.register_check('system', self._check_system)
        self.register_check('memory', self._check_memory)
        self.register_check('disk', self._check_disk)
        self.register_check('network', self._check_network)
        
        # Start check task
        self.add_cleanup_task(
            asyncio.create_task(self._run_checks())
        )

    async def cleanup(self) -> None:
        """Cleanup health checker resources"""
        self._checks.clear()
        self._results.clear()

    def register_check(self,
                      name: str,
                      check: Callable) -> None:
        """Register health check"""
        self._checks[name] = check

    def unregister_check(self, name: str) -> None:
        """Unregister health check"""
        self._checks.pop(name, None)
        self._results.pop(name, None)

    @handle_errors(logger=None)
    async def run_check(self, name: str) -> Dict:
        """Run specific health check"""
        if name not in self._checks:
            raise ValueError(f"Unknown check: {name}")
            
        check = self._checks[name]
        result = await check()
        
        # Store result
        if name not in self._results:
            self._results[name] = []
            
        self._results[name].append({
            'timestamp': datetime.utcnow().isoformat(),
            'status': result
        })
        
        # Trim history
        if len(self._results[name]) > self._history_size:
            self._results[name] = self._results[name][-self._history_size:]
            
        return result

    async def get_status(self,
                        check_name: Optional[str] = None) -> Dict:
        """Get health check status"""
        if check_name:
            if check_name not in self._results:
                raise ValueError(f"Unknown check: {check_name}")
            return {
                check_name: self._results[check_name][-1]
            }
            
        return {
            name: results[-1]
            for name, results in self._results.items()
        }

    async def get_history(self,
                         check_name: Optional[str] = None) -> Dict:
        """Get health check history"""
        if check_name:
            if check_name not in self._results:
                raise ValueError(f"Unknown check: {check_name}")
            return {
                check_name: self._results[check_name]
            }
            
        return self._results

    async def _run_checks(self) -> None:
        """Run all health checks periodically"""
        while True:
            try:
                await asyncio.sleep(self._check_interval)
                
                for name in self._checks:
                    try:
                        await self.run_check(name)
                    except Exception as e:
                        self.logger.error(
                            f"Health check failed: {name} - {str(e)}"
                        )
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health checker failed: {str(e)}")
                await asyncio.sleep(5)

    async def _check_system(self) -> Dict:
        """Check system health"""
        cpu_percent = psutil.cpu_percent(interval=1)
        return {
            'cpu_percent': cpu_percent,
            'status': 'warning' if cpu_percent > self._thresholds['cpu'] else 'ok',
            'load_average': psutil.getloadavg(),
            'boot_time': datetime.fromtimestamp(
                psutil.boot_time()
            ).isoformat()
        }

    async def _check_memory(self) -> Dict:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'status': 'warning' if memory.percent > self._thresholds['memory'] else 'ok'
        }

    async def _check_disk(self) -> Dict:
        """Check disk usage"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent,
            'status': 'warning' if disk.percent > self._thresholds['disk'] else 'ok'
        }

    async def _check_network(self) -> Dict:
        """Check network status"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'status': 'ok'
        } 