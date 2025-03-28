from typing import Dict, Optional, Any, List, Union, Callable
import asyncio
import importlib
import inspect
from datetime import datetime
import traceback
import uuid
from ..base import BaseComponent
from ..utils.decorators import handle_errors

class Worker:
    """Task worker"""
    
    def __init__(self,
                 worker_id: str,
                 queue: asyncio.Queue,
                 results: Dict,
                 retry_limit: int,
                 retry_delay: int,
                 manager: Any):
        self.id = worker_id
        self._queue = queue
        self._results = results
        self._retry_limit = retry_limit
        self._retry_delay = retry_delay
        self._manager = manager
        self._running = True
        self._current_task = None

    async def run(self) -> None:
        """Run worker"""
        while self._running:
            try:
                # Get task from queue
                task = await self._queue.get()
                self._current_task = task
                
                # Update stats
                self._manager._stats['queued'] -= 1
                self._manager._stats['running'] += 1
                
                # Execute task
                await self._execute_task(task)
                
                # Mark task as done
                self._queue.task_done()
                self._current_task = None
                
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                self._manager.logger.error(
                    f"Worker error: {str(e)}"
                )
                await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop worker"""
        self._running = False
        
        # Cancel current task
        if self._current_task:
            await self._current_task.cancel()

    async def _execute_task(self, task: 'Task') -> None:
        """Execute task with retries"""
        for attempt in range(self._retry_limit):
            try:
                # Resolve function
                if isinstance(task.func, str):
                    module_path, func_name = task.func.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    func = getattr(module, func_name)
                else:
                    func = task.func
                    
                # Execute function
                if inspect.iscoroutinefunction(func):
                    result = await func(*task.args, **task.kwargs)
                else:
                    result = func(*task.args, **task.kwargs)
                    
                # Store result
                self._results[task.id] = {
                    'status': 'completed',
                    'result': result,
                    'error': None,
                    'completed_at': datetime.utcnow()
                }
                
                # Update stats
                self._manager._stats['running'] -= 1
                self._manager._stats['completed'] += 1
                
                # Emit event
                await self._manager.app.events.emit(
                    'tasks.completed',
                    {
                        'task_id': task.id,
                        'worker_id': self.id
                    }
                )
                
                return
                
            except Exception as e:
                error = {
                    'type': type(e).__name__,
                    'message': str(e),
                    'traceback': traceback.format_exc()
                }
                
                # Check retry limit
                if attempt == self._retry_limit - 1:
                    # Store error
                    self._results[task.id] = {
                        'status': 'failed',
                        'result': None,
                        'error': error,
                        'completed_at': datetime.utcnow()
                    }
                    
                    # Update stats
                    self._manager._stats['running'] -= 1
                    self._manager._stats['failed'] += 1
                    
                    # Emit event
                    await self._manager.app.events.emit(
                        'tasks.failed',
                        {
                            'task_id': task.id,
                            'worker_id': self.id,
                            'error': error
                        }
                    )
                    
                else:
                    # Wait before retry
                    await asyncio.sleep(self._retry_delay)

class TaskWorker(BaseComponent):
    """Background task worker system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._queue: asyncio.Queue = asyncio.Queue()
        self._results: Dict[str, Any] = {}
        self._handlers: Dict[str, Callable] = {}
        self._running: Dict[str, asyncio.Task] = {}
        self._max_workers = self.config.get('worker.max_workers', 10)
        self._result_ttl = self.config.get('worker.result_ttl', 3600)

    async def initialize(self) -> None:
        """Initialize task worker"""
        # Start worker pool
        for _ in range(self._max_workers):
            self.add_cleanup_task(
                asyncio.create_task(self._run_worker())
            )
            
        # Start result cleanup
        self.add_cleanup_task(
            asyncio.create_task(self._cleanup_results())
        )

    async def cleanup(self) -> None:
        """Cleanup worker resources"""
        # Cancel all running tasks
        for task in self._running.values():
            task.cancel()
            
        await asyncio.gather(
            *self._running.values(),
            return_exceptions=True
        )
        
        self._results.clear()
        self._handlers.clear()
        self._running.clear()

    def register_handler(self,
                        name: str,
                        handler: Callable) -> None:
        """Register task handler"""
        self._handlers[name] = handler

    @handle_errors(logger=None)
    async def submit_task(self,
                         handler: str,
                         data: Optional[Dict] = None,
                         metadata: Optional[Dict] = None) -> str:
        """Submit task for execution"""
        # Validate handler
        if handler not in self._handlers:
            raise ValueError(f"Unknown handler: {handler}")
            
        # Create task
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'handler': handler,
            'data': data or {},
            'metadata': metadata or {},
            'submitted': datetime.utcnow().isoformat()
        }
        
        # Add to queue
        await self._queue.put(task)
        
        return task_id

    async def get_result(self,
                        task_id: str,
                        wait: bool = False) -> Optional[Dict]:
        """Get task result"""
        if wait:
            while task_id not in self._results:
                await asyncio.sleep(0.1)
                
        return self._results.get(task_id)

    async def cancel_task(self, task_id: str) -> None:
        """Cancel running task"""
        if task_id in self._running:
            self._running[task_id].cancel()
            try:
                await self._running[task_id]
            except asyncio.CancelledError:
                pass
            del self._running[task_id]

    async def _run_worker(self) -> None:
        """Worker process loop"""
        while True:
            try:
                # Get task from queue
                task = await self._queue.get()
                
                # Start task
                self._running[task['id']] = asyncio.create_task(
                    self._execute_task(task)
                )
                
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker failed: {str(e)}")
                await asyncio.sleep(1)

    async def _execute_task(self, task: Dict) -> None:
        """Execute background task"""
        handler = self._handlers[task['handler']]
        
        try:
            # Execute handler
            result = await handler(task['data'])
            
            # Store result
            self._results[task['id']] = {
                'status': 'success',
                'result': result,
                'completed': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Store error
            self._results[task['id']] = {
                'status': 'error',
                'error': str(e),
                'completed': datetime.utcnow().isoformat()
            }
            
        finally:
            # Cleanup
            if task['id'] in self._running:
                del self._running[task['id']]

    async def _cleanup_results(self) -> None:
        """Cleanup expired results"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.utcnow()
                expired = []
                
                for task_id, result in self._results.items():
                    completed = datetime.fromisoformat(
                        result['completed']
                    )
                    if (now - completed).total_seconds() > self._result_ttl:
                        expired.append(task_id)
                        
                for task_id in expired:
                    del self._results[task_id]
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Result cleanup failed: {str(e)}")
                await asyncio.sleep(5) 