from functools import wraps
from typing import Callable, Any, Optional
import time
from core.logging import get_logger
from core.monitoring.service import monitoring_service

logger = get_logger(__name__)

def measure_performance(metric_name: Optional[str] = None) -> Callable:
    """
    Decorator to measure function performance and record metrics.
    
    Args:
        metric_name: Optional name for the metric. If not provided, uses function name.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record metric
                metric = metric_name or func.__name__
                monitoring_service._metrics[f"{metric}_time"] = execution_time
                
                # Log performance
                logger.debug(f"{func.__name__} executed in {execution_time:.2f} seconds")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {e}")
                raise
        return wrapper
    return decorator

def track_memory(metric_name: Optional[str] = None) -> Callable:
    """
    Decorator to track memory usage of functions.
    
    Args:
        metric_name: Optional name for the metric. If not provided, uses function name.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            import psutil
            process = psutil.Process()
            
            # Record initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            try:
                result = await func(*args, **kwargs)
                
                # Record final memory
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_used = final_memory - initial_memory
                
                # Record metric
                metric = metric_name or func.__name__
                monitoring_service._metrics[f"{metric}_memory"] = memory_used
                
                # Log memory usage
                logger.debug(f"{func.__name__} used {memory_used:.2f} MB of memory")
                
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}")
                raise
        return wrapper
    return decorator

def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    Decorator to retry functions on failure.
    
    Args:
        max_retries: Maximum number of retry attempts.
        delay: Delay between retries in seconds.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {delay} seconds..."
                        )
                        await asyncio.sleep(delay)
                        
            logger.error(f"All {max_retries} attempts failed. Last error: {last_exception}")
            raise last_exception
        return wrapper
    return decorator

def cache_result(ttl: int = 3600) -> Callable:
    """
    Decorator to cache function results with TTL.
    
    Args:
        ttl: Time to live in seconds.
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    return result
                    
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache[key] = (result, time.time())
            
            return result
        return wrapper
    return decorator 