from typing import Dict, Optional, Any, List, Union, Callable
import asyncio
from datetime import datetime, timedelta
import uuid
from ..base import BaseComponent
from ..utils.errors import handle_errors

class TaskManager(BaseComponent):
    """Advanced task management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._tasks: Dict[str, 'Task'] = {}
        self._workers: Dict[str, 'Worker'] = {}
        self._queue: asyncio.Queue = None
        self._results: Dict[str, Any] = {}
        self._max_workers = self.config.get('tasks.max_workers', 10)
        self._max_queue_size = self.config.get('tasks.max_queue_size', 1000)
        self._result_ttl = self.config.get('tasks.result_ttl', 3600)
        self._retry_limit = self.config.get('tasks.retry_limit', 3)
        self._retry_delay = self.config.get('tasks.retry_delay', 60)
        self._stats = {
            'queued': 0,
            'running': 0,
            'completed': 0,
            'failed': 0
        }

    async def initialize(self) -> None:
        """Initialize task manager"""
        # Create task queue
        self._queue = asyncio.Queue(maxsize=self._max_queue_size)
        
        # Start workers
        for i in range(self._max_workers):
            worker = Worker(
                f"worker-{i}",
                self._queue,
                self._results,
                self._retry_limit,
                self._retry_delay,
                self
            )
            self._workers[worker.id] = worker
            asyncio.create_task(worker.run())
            
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    async def cleanup(self) -> None:
        """Cleanup task resources"""
        # Stop all workers
        for worker in self._workers.values():
            await worker.stop()
            
        self._workers.clear()
        self._tasks.clear()
        self._results.clear()

    @handle_errors(logger=None)
    async def submit(self,
                    func: Union[Callable, str],
                    *args,
                    **kwargs) -> 'Task':
        """Submit task for execution"""
        try:
            # Create task
            task = Task(
                func=func,
                args=args,
                kwargs=kwargs,
                manager=self
            )
            
            # Store task
            self._tasks[task.id] = task
            
            # Add to queue
            await self._queue.put(task)
            self._stats['queued'] += 1
            
            # Emit event
            await self.app.events.emit(
                'tasks.submitted',
                {'task_id': task.id}
            )
            
            return task
            
        except Exception as e:
            self.logger.error(f"Task submission error: {str(e)}")
            raise

    async def get_result(self,
                        task_id: str,
                        timeout: Optional[float] = None) -> Any:
        """Get task result"""
        try:
            task = self._tasks.get(task_id)
            if not task:
                raise ValueError(f"Unknown task: {task_id}")
                
            return await task.get_result(timeout)
            
        except Exception as e:
            self.logger.error(f"Result retrieval error: {str(e)}")
            raise

    async def cancel(self, task_id: str) -> bool:
        """Cancel task"""
        try:
            task = self._tasks.get(task_id)
            if not task:
                return False
                
            return await task.cancel()
            
        except Exception as e:
            self.logger.error(f"Task cancellation error: {str(e)}")
            return False

    def get_task(self, task_id: str) -> Optional['Task']:
        """Get task by ID"""
        return self._tasks.get(task_id)

    async def list_tasks(self,
                        status: Optional[str] = None) -> List[Dict]:
        """List tasks"""
        tasks = []
        for task in self._tasks.values():
            if status and task.status != status:
                continue
            tasks.append(task.get_info())
        return tasks

    async def get_stats(self) -> Dict[str, Any]:
        """Get task statistics"""
        stats = self._stats.copy()
        stats['workers'] = len(self._workers)
        stats['queue_size'] = self._queue.qsize()
        return stats

    async def _cleanup_task(self) -> None:
        """Cleanup completed tasks"""
        while True:
            try:
                now = datetime.utcnow()
                
                # Find expired tasks
                expired = [
                    task_id for task_id, task in self._tasks.items()
                    if task.is_complete and
                    (now - task.completed_at) > timedelta(seconds=self._result_ttl)
                ]
                
                # Remove expired tasks
                for task_id in expired:
                    self._tasks.pop(task_id, None)
                    self._results.pop(task_id, None)
                    
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                self.logger.error(f"Task cleanup error: {str(e)}")
                await asyncio.sleep(60) 