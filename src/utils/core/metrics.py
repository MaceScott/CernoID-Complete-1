from typing import Callable, TypeVar, Any
from functools import wraps
import time
from prometheus_client import Histogram, Counter

T = TypeVar('T')

# Define metrics
FUNCTION_TIME = Histogram(
    'function_execution_seconds',
    'Time spent in function execution',
    ['function_name', 'component']
)

FUNCTION_CALLS = Counter(
    'function_calls_total',
    'Number of function calls',
    ['function_name', 'component', 'status']
)

def track_time(component: str = 'unknown') -> Callable:
    """Track function execution time"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
                
            finally:
                duration = time.time() - start_time
                FUNCTION_TIME.labels(
                    function_name=func.__name__,
                    component=component
                ).observe(duration)
                
                FUNCTION_CALLS.labels(
                    function_name=func.__name__,
                    component=component,
                    status='success' if success else 'error'
                ).inc()
                
        return wrapper
    return decorator 