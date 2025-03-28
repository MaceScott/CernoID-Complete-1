from typing import Dict, Optional, Any, List, Union, Callable
import asyncio
from datetime import datetime, timedelta
import croniter
from ..base import BaseComponent
from ..utils.decorators import handle_errors

class CronManager(BaseComponent):
    """Advanced cron job management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._jobs: Dict[str, 'CronJob'] = {}
        self._running: Dict[str, asyncio.Task] = {}
        self._last_run: Dict[str, datetime] = {}
        self._timezone = self.config.get('cron.timezone', 'UTC')
        self._max_instances = self.config.get('cron.max_instances', 1)
        self._max_retries = self.config.get('cron.max_retries', 3)
        self._retry_delay = self.config.get('cron.retry_delay', 60)
        self._overlap = self.config.get('cron.allow_overlap', False)
        self._stats = {
            'total': 0,
            'running': 0,
            'completed': 0,
            'failed': 0
        }

    async def initialize(self) -> None:
        """Initialize cron manager"""
        # Load jobs from config
        jobs = self.config.get('cron.jobs', {})
        for name, config in jobs.items():
            await self.add_job(
                name,
                config['schedule'],
                config.get('func'),
                config.get('args', []),
                config.get('kwargs', {}),
                config.get('enabled', True)
            )
            
        # Start scheduler
        asyncio.create_task(self._scheduler_task())

    async def cleanup(self) -> None:
        """Cleanup cron resources"""
        # Stop all jobs
        for name in list(self._jobs.keys()):
            await self.remove_job(name)
            
        self._jobs.clear()
        self._running.clear()
        self._last_run.clear()

    @handle_errors(logger=None)
    async def add_job(self,
                     name: str,
                     schedule: str,
                     func: Union[Callable, str],
                     args: Optional[List] = None,
                     kwargs: Optional[Dict] = None,
                     enabled: bool = True) -> bool:
        """Add cron job"""
        try:
            # Validate schedule
            if not croniter.is_valid(schedule):
                raise ValueError(f"Invalid cron schedule: {schedule}")
                
            # Create job
            job = CronJob(
                name=name,
                schedule=schedule,
                func=func,
                args=args or [],
                kwargs=kwargs or {},
                enabled=enabled,
                manager=self
            )
            
            # Store job
            self._jobs[name] = job
            self._stats['total'] += 1
            
            # Emit event
            await self.app.events.emit(
                'cron.job_added',
                {'name': name, 'schedule': schedule}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Job addition error: {str(e)}")
            return False

    @handle_errors(logger=None)
    async def remove_job(self, name: str) -> bool:
        """Remove cron job"""
        try:
            if name not in self._jobs:
                return False
                
            # Cancel running task
            if name in self._running:
                self._running[name].cancel()
                del self._running[name]
                
            # Remove job
            del self._jobs[name]
            self._last_run.pop(name, None)
            self._stats['total'] -= 1
            
            # Emit event
            await self.app.events.emit(
                'cron.job_removed',
                {'name': name}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Job removal error: {str(e)}")
            return False

    def get_job(self, name: str) -> Optional['CronJob']:
        """Get cron job"""
        return self._jobs.get(name)

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs"""
        return [
            {
                'name': name,
                'schedule': job.schedule,
                'enabled': job.enabled,
                'last_run': self._last_run.get(name),
                'running': name in self._running
            }
            for name, job in self._jobs.items()
        ]

    async def run_job(self, name: str) -> bool:
        """Run job manually"""
        try:
            job = self._jobs.get(name)
            if not job:
                return False
                
            # Run job
            await self._run_job(job)
            return True
            
        except Exception as e:
            self.logger.error(f"Manual job run error: {str(e)}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cron statistics"""
        stats = self._stats.copy()
        stats['running'] = len(self._running)
        return stats

    async def _scheduler_task(self) -> None:
        """Main scheduler task"""
        while True:
            try:
                now = datetime.utcnow()
                
                # Check each job
                for job in self._jobs.values():
                    if not job.enabled:
                        continue
                        
                    # Get last run time
                    last_run = self._last_run.get(job.name)
                    
                    # Create cron iterator
                    cron = croniter.croniter(job.schedule, last_run or now)
                    next_run = cron.get_next(datetime)
                    
                    # Check if job should run
                    if now >= next_run:
                        # Check overlap
                        if job.name in self._running:
                            if not self._overlap:
                                continue
                                
                        # Run job
                        task = asyncio.create_task(
                            self._run_job(job)
                        )
                        self._running[job.name] = task
                        
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(1)

    async def _run_job(self, job: 'CronJob') -> None:
        """Run cron job"""
        try:
            # Update last run time
            self._last_run[job.name] = datetime.utcnow()
            
            # Emit event
            await self.app.events.emit(
                'cron.job_started',
                {'name': job.name}
            )
            
            # Run job
            await job.run()
            
            self._stats['completed'] += 1
            
            # Emit event
            await self.app.events.emit(
                'cron.job_completed',
                {'name': job.name}
            )
            
        except Exception as e:
            self.logger.error(f"Job run error: {str(e)}")
            self._stats['failed'] += 1
            
            # Emit event
            await self.app.events.emit(
                'cron.job_failed',
                {
                    'name': job.name,
                    'error': str(e)
                }
            )
            
        finally:
            # Cleanup
            self._running.pop(job.name, None) 