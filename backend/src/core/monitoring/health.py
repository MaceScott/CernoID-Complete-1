from typing import Dict, Optional, Any, List, Callable
import asyncio
from datetime import datetime
import json
from enum import Enum
from ..base import BaseComponent
from ..utils.errors import handle_errors
import os
import psutil
import platform
from ..logging import get_logger
from fastapi import APIRouter, Depends
from core.system.bootstrap import SystemBootstrap
from core.monitoring.system.manager import SystemManager

logger = get_logger(__name__)

class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = 'healthy'
    UNHEALTHY = 'unhealthy'
    DEGRADED = 'degraded'
    STARTING = 'starting'
    STOPPED = 'stopped'

class HealthCheck(BaseComponent):
    """Health check component."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._checks: Dict[str, Dict] = {}
        self._results: Dict[str, Dict] = {}
        self._history: List[Dict] = []
        self._history_size = self.config.get('health.history_size', 100)
        self._check_interval = self.config.get('health.check_interval', 30)
        self._timeout = self.config.get('health.timeout', 5)
        self._status = HealthStatus.STARTING
        self._dependencies: Dict[str, List[str]] = {}

    @handle_errors
    async def initialize(self) -> None:
        """Initialize health check."""
        # Register default checks
        self._register_default_checks()
        
        # Start health check task
        self.add_cleanup_task(
            asyncio.create_task(self._run_checks())
        )

    @handle_errors
    async def cleanup(self) -> None:
        """Clean up health check resources."""
        self._status = HealthStatus.STOPPED
        self._checks.clear()
        self._results.clear()
        self._history.clear()
        self._dependencies.clear()

    def register_check(self,
                      name: str,
                      check: Callable,
                      interval: Optional[int] = None,
                      timeout: Optional[int] = None,
                      dependencies: Optional[List[str]] = None) -> None:
        """Register health check"""
        self._checks[name] = {
            'name': name,
            'check': check,
            'interval': interval or self._check_interval,
            'timeout': timeout or self._timeout,
            'last_check': None,
            'dependencies': dependencies or []
        }
        
        # Update dependencies
        for dep in (dependencies or []):
            if dep not in self._dependencies:
                self._dependencies[dep] = []
            self._dependencies[dep].append(name)

    def remove_check(self, name: str) -> None:
        """Remove health check"""
        if name in self._checks:
            del self._checks[name]
            
        if name in self._results:
            del self._results[name]
            
        # Remove from dependencies
        for deps in self._dependencies.values():
            if name in deps:
                deps.remove(name)

    @handle_errors
    async def check_health(self,
                         name: Optional[str] = None) -> Dict:
        """Run health check(s)"""
        if name:
            if name not in self._checks:
                raise ValueError(f"Check not found: {name}")
                
            # Run single check
            result = await self._run_check(name)
            return {name: result}
            
        # Run all checks
        results = {}
        for check_name in self._checks:
            results[check_name] = await self._run_check(
                check_name
            )
            
        return results

    async def get_status(self) -> Dict:
        """Get overall health status"""
        return {
            'status': self._status,
            'checks': self._results,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def get_history(self,
                         name: Optional[str] = None,
                         limit: Optional[int] = None) -> List[Dict]:
        """Get health check history"""
        history = self._history
        
        if name:
            history = [
                h for h in history
                if h['check'] == name
            ]
            
        if limit:
            history = history[-limit:]
            
        return history

    def _register_default_checks(self) -> None:
        """Register default health checks"""
        # Database check
        self.register_check(
            'database',
            self._check_database,
            interval=30
        )
        
        # Cache check
        self.register_check(
            'cache',
            self._check_cache,
            interval=30,
            dependencies=['database']
        )
        
        # Queue check
        self.register_check(
            'queue',
            self._check_queue,
            interval=30
        )

    async def _run_checks(self) -> None:
        """Run health checks periodically"""
        while True:
            try:
                await asyncio.sleep(1)  # Check every second
                
                now = datetime.utcnow()
                
                for name, check in self._checks.items():
                    # Check if it's time to run
                    if check['last_check']:
                        last_check = datetime.fromisoformat(
                            check['last_check']
                        )
                        if (now - last_check).total_seconds() < check['interval']:
                            continue
                            
                    # Run check
                    await self._run_check(name)
                    
                # Update overall status
                self._update_status()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check failed: {str(e)}")
                await asyncio.sleep(5)

    async def _run_check(self, name: str) -> Dict:
        """Run single health check"""
        check = self._checks[name]
        
        # Check dependencies
        for dep in check['dependencies']:
            if dep not in self._results:
                continue
                
            if self._results[dep]['status'] != HealthStatus.HEALTHY:
                result = {
                    'status': HealthStatus.DEGRADED,
                    'message': f"Dependency {dep} is unhealthy",
                    'timestamp': datetime.utcnow().isoformat()
                }
                self._update_result(name, result)
                return result
                
        # Run check with timeout
        try:
            async with asyncio.timeout(check['timeout']):
                result = await check['check']()
                
        except asyncio.TimeoutError:
            result = {
                'status': HealthStatus.UNHEALTHY,
                'message': 'Check timed out',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            result = {
                'status': HealthStatus.UNHEALTHY,
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        self._update_result(name, result)
        return result

    def _update_result(self,
                      name: str,
                      result: Dict) -> None:
        """Update check result"""
        check = self._checks[name]
        check['last_check'] = result['timestamp']
        
        self._results[name] = result
        
        # Add to history
        self._history.append({
            'check': name,
            **result
        })
        
        # Trim history
        if len(self._history) > self._history_size:
            self._history = self._history[-self._history_size:]
            
        # Update dependent checks
        if name in self._dependencies:
            for dep in self._dependencies[name]:
                if dep in self._checks:
                    asyncio.create_task(
                        self._run_check(dep)
                    )

    def _update_status(self) -> None:
        """Update overall health status"""
        if not self._results:
            self._status = HealthStatus.STARTING
            return
            
        # Check all results
        statuses = [r['status'] for r in self._results.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            self._status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            self._status = HealthStatus.UNHEALTHY
        else:
            self._status = HealthStatus.DEGRADED

    async def _check_database(self) -> Dict:
        """Check database health"""
        try:
            db = self.app.get_component('database')
            await db.execute('SELECT 1')
            
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'Database is healthy',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f"Database error: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_cache(self) -> Dict:
        """Check cache health"""
        try:
            cache = self.app.get_component('cache_manager')
            await cache.set('health_check', 1)
            await cache.get('health_check')
            await cache.delete('health_check')
            
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'Cache is healthy',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f"Cache error: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_queue(self) -> Dict:
        """Check message queue health"""
        try:
            queue = self.app.get_component('message_queue')
            await queue.publish('health_check', {'test': True})
            
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'Queue is healthy',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f"Queue error: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }

    @handle_errors
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'system': {
                    'platform': platform.system(),
                    'version': platform.version(),
                    'processor': platform.processor(),
                    'python_version': platform.python_version(),
                },
                'metrics': {
                    'cpu': {
                        'usage_percent': cpu_percent,
                        'cores': psutil.cpu_count(),
                    },
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'used': memory.used,
                        'percent': memory.percent,
                    },
                    'disk': {
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                        'percent': disk.percent,
                    },
                    'process': {
                        'pid': os.getpid(),
                        'memory_usage': psutil.Process().memory_info().rss,
                        'threads': psutil.Process().num_threads(),
                    }
                }
            }
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    @handle_errors
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        # TODO: Implement database health check
        return {
            'status': 'not_implemented',
            'message': 'Database health check not implemented'
        }

    @handle_errors
    async def check_services_health(self) -> Dict[str, Any]:
        """Check services health."""
        # TODO: Implement services health check
        return {
            'status': 'not_implemented',
            'message': 'Services health check not implemented'
        }

    @handle_errors
    async def get_full_health_report(self) -> Dict[str, Any]:
        """Get full health report."""
        system_health = await self.get_system_health()
        db_health = await self.check_database_health()
        services_health = await self.check_services_health()
        
        return {
            'system': system_health,
            'database': db_health,
            'services': services_health,
            'timestamp': datetime.utcnow().isoformat()
        }

router = APIRouter()

@router.get("/health")
async def health_check(
    system: SystemBootstrap = Depends(),
    system_manager: SystemManager = Depends()
) -> Dict[str, Any]:
    """Health check endpoint"""
    try:
        # Get system health status
        health_status = await system.check_health()
        
        # Get component health
        component_health = await system_manager.get_component_health()
        
        return {
            "status": "healthy" if health_status["healthy"] else "unhealthy",
            "components": component_health,
            "details": health_status["details"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/ready")
async def readiness_check(
    system: SystemBootstrap = Depends(),
    system_manager: SystemManager = Depends()
) -> Dict[str, Any]:
    """Readiness check endpoint"""
    try:
        # Check if system is ready to accept traffic
        health_status = await system.check_health()
        component_health = await system_manager.get_component_health()
        
        # System is ready if all critical components are healthy
        is_ready = all(
            status == "healthy" 
            for status in component_health.values()
        )
        
        return {
            "status": "ready" if is_ready else "not_ready",
            "components": component_health
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e)
        } 