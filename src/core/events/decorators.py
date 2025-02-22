from typing import Optional, Any, Callable, Union
import functools
from datetime import datetime

def event_handler(event: str,
                 priority: int = 0):
    """Event handler decorator"""
    
    def decorator(func: Callable) -> Callable:
        # Store handler metadata
        func._event_handler = True
        func._event_name = event
        func._event_priority = priority
        
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            return await func(self, *args, **kwargs)
            
        return wrapper
        
    return decorator

def event_middleware(func: Callable) -> Callable:
    """Event middleware decorator"""
    
    @functools.wraps(func)
    async def wrapper(event: Any) -> Optional[Any]:
        # Skip if propagation stopped
        if event.propagation_stopped:
            return None
            
        return await func(event)
        
    wrapper._event_middleware = True
    return wrapper

def emit_after(event: str,
               include_result: bool = False):
    """Emit event after method execution"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            # Execute method
            result = await func(self, *args, **kwargs)
            
            # Prepare event data
            data = {
                'args': args,
                'kwargs': kwargs,
                'timestamp': datetime.utcnow()
            }
            
            if include_result:
                data['result'] = result
                
            # Emit event
            await self.app.events.emit(event, data)
            
            return result
            
        return wrapper
        
    return decorator

def emit_before(event: str):
    """Emit event before method execution"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            # Prepare event data
            data = {
                'args': args,
                'kwargs': kwargs,
                'timestamp': datetime.utcnow()
            }
            
            # Emit event
            await self.app.events.emit(event, data)
            
            # Execute method
            return await func(self, *args, **kwargs)
            
        return wrapper
        
    return decorator

def emit_on_error(event: str):
    """Emit event on method error"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            try:
                # Execute method
                return await func(self, *args, **kwargs)
                
            except Exception as e:
                # Prepare event data
                data = {
                    'args': args,
                    'kwargs': kwargs,
                    'error': str(e),
                    'timestamp': datetime.utcnow()
                }
                
                # Emit event
                await self.app.events.emit(event, data)
                
                # Re-raise exception
                raise
                
        return wrapper
        
    return decorator 