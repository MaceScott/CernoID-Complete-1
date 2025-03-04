from typing import Dict, Optional, Any, Callable, List, Union
import asyncio
from datetime import datetime, timedelta
import uuid
import json
from croniter import croniter
from ..base import BaseComponent
from ..utils.errors import handle_errors

class TaskScheduler(BaseComponent):
    """Advanced task scheduling system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._tasks: Dict[str, Dict] = {}
        self._running: Dict[str, asyncio.Task] = {}
        self._history: List[Dict] = []
        self._max_history = self.config.get('tasks.max_history', 1000)
        self._max_retries = self.config.get('tasks.max_retries', 3)
        self._retry_delay = self.config.get('tasks.retry_delay', 60)
        self._handlers: Dict[str, Callable] = {}

    async def initialize(self) -> None:
        """Initialize task scheduler"""
        # Load saved tasks
        await self._load_tasks()
        
        # Start scheduler
        self.add_cleanup_task(
            asyncio.create_task(self._run_scheduler())
        )

    async def cleanup(self) -> None:
        """Cleanup scheduler resources"""
        # Cancel all running tasks
        for task in self._running.values():
            task.cancel()
            
        await asyncio.gather(
            *self._running.values(),
            return_exceptions=True
        )
        
        self._tasks.clear()
        self._running.clear()
        self._history.clear()
        self._handlers.clear()

    def register_handler(self,
                        name: str,
                        handler: Callable) -> None:
        """Register task handler"""
        self._handlers[name] = handler

    @handle_errors(logger=None)
    async def schedule_task(self,
                          name: str,
                          handler: str,
                          schedule: str,
                          data: Optional[Dict] = None,
                          metadata: Optional[Dict] = None) -> str:
        """Schedule new task"""
        # Validate handler
        if handler not in self._handlers:
            raise ValueError(f"Unknown handler: {handler}")
            
        # Validate cron schedule
        if not croniter.is_valid(schedule):
            raise ValueError(f"Invalid schedule: {schedule}")
            
        # Create task
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'name': name,
            'handler': handler,
            'schedule': schedule,
            'data': data or {},
            'metadata': metadata or {},
            'status': 'scheduled',
            'created': datetime.utcnow().isoformat(),
            'last_run': None,
            'next_run': None,
            'retries': 0
        }
        
        # Calculate next run
        task['next_run'] = self._get_next_run(schedule)
        
        # Store task
        self._tasks[task_id] = task
        await self._save_tasks()
        
        return task_id

    async def cancel_task(self, task_id: str) -> None:
        """Cancel scheduled task"""
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")
            
        # Cancel running task
        if task_id in self._running:
            self._running[task_id].cancel()
            try:
                await self._running[task_id]
            except asyncio.CancelledError:
                pass
            del self._running[task_id]
            
        # Remove task
        del self._tasks[task_id]
        await self._save_tasks()

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task information"""
        return self._tasks.get(task_id)

    async def get_tasks(self,
                       status: Optional[str] = None) -> List[Dict]:
        """Get all tasks"""
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t['status'] == status]
            
        return tasks

    async def get_history(self,
                         task_id: Optional[str] = None,
                         limit: Optional[int] = None) -> List[Dict]:
        """Get task execution history"""
        history = self._history
        
        if task_id:
            history = [h for h in history if h['task_id'] == task_id]
            
        if limit:
            history = history[-limit:]
            
        return history

    def _get_next_run(self, schedule: str) -> str:
        """Calculate next run time"""
        cron = croniter(schedule, datetime.utcnow())
        return cron.get_next(datetime).isoformat()

    async def _run_scheduler(self) -> None:
        """Main scheduler loop"""
        while True:
            try:
                now = datetime.utcnow()
                
                # Find tasks to run
                for task_id, task in self._tasks.items():
                    if (task['status'] != 'running' and
                        datetime.fromisoformat(task['next_run']) <= now):
                        # Start task
                        self._running[task_id] = asyncio.create_task(
                            self._execute_task(task_id)
                        )
                        
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Scheduler failed: {str(e)}")
                await asyncio.sleep(5)

    async def _execute_task(self, task_id: str) -> None:
        """Execute scheduled task"""
        task = self._tasks[task_id]
        handler = self._handlers[task['handler']]
        
        # Update task status
        task['status'] = 'running'
        task['last_run'] = datetime.utcnow().isoformat()
        
        try:
            # Execute handler
            result = await handler(task['data'])
            
            # Update task
            task['status'] = 'scheduled'
            task['retries'] = 0
            task['next_run'] = self._get_next_run(task['schedule'])
            
            # Add to history
            self._add_to_history({
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'success',
                'result': result
            })
            
        except Exception as e:
            # Handle failure
            task['retries'] += 1
            
            if task['retries'] >= self._max_retries:
                task['status'] = 'failed'
            else:
                task['status'] = 'scheduled'
                task['next_run'] = (
                    datetime.utcnow() +
                    timedelta(seconds=self._retry_delay)
                ).isoformat()
                
            # Add to history
            self._add_to_history({
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'error',
                'error': str(e)
            })
            
        finally:
            # Cleanup
            if task_id in self._running:
                del self._running[task_id]
                
            await self._save_tasks()

    def _add_to_history(self, entry: Dict) -> None:
        """Add entry to task history"""
        self._history.append(entry)
        
        # Trim history if needed
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    async def _load_tasks(self) -> None:
        """Load tasks from storage"""
        try:
            db = self.app.get_component('database')
            records = await db.fetch_all(
                "SELECT * FROM scheduled_tasks"
            )
            
            for record in records:
                self._tasks[record['id']] = json.loads(
                    record['data']
                )
                
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {str(e)}")

    async def _save_tasks(self) -> None:
        """Save tasks to storage"""
        try:
            db = self.app.get_component('database')
            
            # Clear existing tasks
            await db.execute(
                "DELETE FROM scheduled_tasks"
            )
            
            # Insert updated tasks
            if self._tasks:
                await db.execute_many(
                    """
                    INSERT INTO scheduled_tasks (id, data)
                    VALUES ($1, $2)
                    """,
                    [
                        (task_id, json.dumps(task))
                        for task_id, task in self._tasks.items()
                    ]
                )
                
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {str(e)}") 