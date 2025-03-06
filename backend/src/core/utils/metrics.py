"""Metrics and monitoring utilities."""
import time
import functools
from typing import Any, Callable, TypeVar
from src.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=Callable[..., Any])

def track_time(func: T) -> T:
    """Decorator to track function execution time."""
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            logger.info(
                f"{func.__name__} took {duration:.2f} seconds to execute"
            )
    return wrapper  # type: ignore

class MetricsCollector:
    """Class to collect and track various metrics."""
    
    def __init__(self):
        self.metrics: dict[str, list[float]] = {}
        self.counts: dict[str, int] = {}
        
    def record_time(self, metric_name: str, execution_time: float) -> None:
        """Record execution time for a metric."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(execution_time)
        
    def increment_count(self, metric_name: str) -> None:
        """Increment counter for a metric."""
        if metric_name not in self.counts:
            self.counts[metric_name] = 0
        self.counts[metric_name] += 1
        
    def get_average_time(self, metric_name: str) -> float:
        """Get average execution time for a metric."""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return 0.0
        return sum(self.metrics[metric_name]) / len(self.metrics[metric_name])
        
    def get_count(self, metric_name: str) -> int:
        """Get count for a metric."""
        return self.counts.get(metric_name, 0)
        
    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.counts.clear()

# Global metrics collector instance
metrics_collector = MetricsCollector() 