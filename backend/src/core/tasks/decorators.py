from typing import Optional, Any, Callable
from datetime import datetime, timedelta
import functools
from ..base import BaseComponent

def task(name: Optional[str] = None,
         timeout: Optional[int] = None):
    """Task decorator"""
    
    def decorator(func: Callable) -> Callable:
        # Get task name
        task_name = name or func.__name__
        
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            # Get task manager
            tasks = self.app.get_component('task_manager')
            if not tasks:
                raise RuntimeError("Task manager not available")
                
            # Submit task
            task_id = await tasks.submit(
                func,
                *args,
                **kwargs
            )
            
            # Wait for result
            return await tasks.get_result(task_id, timeout)
            
        # Store original function
        wrapper.original_func = func
        wrapper.task_name = task_name
        
        return wrapper
        
    return decorator

def scheduled(when: Any,
             name: Optional[str] = None):
    """Scheduled task decorator"""
    
    def decorator(func: Callable) -> Callable:
        # Get task name
        task_name = name or func.__name__
        
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> None:
            # Get task manager
            tasks = self.app.get_component('task_manager')
            if not tasks:
                raise RuntimeError("Task manager not available")
                
            # Calculate next run time
            if isinstance(when, (int, float)):
                next_run = datetime.utcnow() + timedelta(seconds=when)
            elif isinstance(when, timedelta):
                next_run = datetime.utcnow() + when
            elif isinstance(when, datetime):
                next_run = when
            else:
                raise ValueError("Invalid schedule time")
                
            # Schedule task
            await tasks.schedule(
                func,
                next_run,
                *args,
                **kwargs
            )
            
        # Store original function
        wrapper.original_func = func
        wrapper.task_name = task_name
        
        return wrapper
        
    return decorator

def periodic(interval: int,
            name: Optional[str] = None):
    """Periodic task decorator"""
    
    def decorator(func: Callable) -> Callable:
        # Get task name
        task_name = name or func.__name__
        
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> None:
            # Get task manager
            tasks = self.app.get_component('task_manager')
            if not tasks:
                raise RuntimeError("Task manager not available")
                
            async def periodic_task():
                while True:
                    try:
                        # Run task
                        await func(self, *args, **kwargs)
                        
                        # Wait for next interval
                        await asyncio.sleep(interval)
                        
                    except Exception as e:
                        self.logger.error(
                            f"Periodic task error: {str(e)}"
                        )
                        await asyncio.sleep(interval)
                        
            # Start periodic task
            asyncio.create_task(periodic_task())
            
        # Store original function
        wrapper.original_func = func
        wrapper.task_name = task_name
        
        return wrapper
        
    return decorator 