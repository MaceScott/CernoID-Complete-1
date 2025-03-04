from typing import Dict, Optional, Any, List, Union, Callable
import asyncio
import inspect
from datetime import datetime
import importlib

class CronJob:
    """Cron job class"""
    
    def __init__(self,
                 name: str,
                 schedule: str,
                 func: Union[Callable, str],
                 args: List,
                 kwargs: Dict,
                 enabled: bool,
                 manager: Any):
        self.name = name
        self.schedule = schedule
        self.args = args
        self.kwargs = kwargs
        self.enabled = enabled
        self.manager = manager
        self._func = self._resolve_func(func)
        self._retries = 0
        self._last_error = None

    async def run(self) -> None:
        """Run job"""
        try:
            # Reset retry counter
            self._retries = 0
            
            while True:
                try:
                    # Call function
                    if inspect.iscoroutinefunction(self._func):
                        await self._func(*self.args, **self.kwargs)
                    else:
                        self._func(*self.args, **self.kwargs)
                        
                    # Clear error
                    self._last_error = None
                    break
                    
                except Exception as e:
                    self._last_error = str(e)
                    self._retries += 1
                    
                    # Check max retries
                    if self._retries >= self.manager._max_retries:
                        raise
                        
                    # Wait before retry
                    await asyncio.sleep(
                        self.manager._retry_delay
                    )
                    
        except Exception as e:
            # Log error
            self.manager.logger.error(
                f"Job '{self.name}' failed: {str(e)}"
            )
            raise

    def get_info(self) -> Dict[str, Any]:
        """Get job information"""
        return {
            'name': self.name,
            'schedule': self.schedule,
            'enabled': self.enabled,
            'retries': self._retries,
            'last_error': self._last_error,
            'func': self._get_func_name()
        }

    def _resolve_func(self,
                     func: Union[Callable, str]) -> Callable:
        """Resolve function from string or callable"""
        if isinstance(func, str):
            # Import function from string
            module_path, func_name = func.rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, func_name)
        return func

    def _get_func_name(self) -> str:
        """Get function name"""
        if isinstance(self._func, str):
            return self._func
        return f"{self._func.__module__}.{self._func.__name__}" 