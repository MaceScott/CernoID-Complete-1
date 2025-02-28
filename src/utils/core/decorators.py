from functools import wraps
from typing import Callable, Any
import time
import asyncio

def async_retry(retries: int = 3, delay: float = 1.0):
    """Retry decorator for async functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator

def measure_performance():
    """Measure execution time of functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start_time
            # Log performance metrics
            return result
        return wrapper
    return decorator 