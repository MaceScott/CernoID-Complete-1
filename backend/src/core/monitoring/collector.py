"""Metrics collection and tracking."""
import time
from typing import Dict, List
from ..utils.logging import get_logger

logger = get_logger(__name__)

class MetricsCollector:
    """Class to collect and track various metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counts: Dict[str, int] = {}
        self._start_times: Dict[str, float] = {}
        
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
        self._start_times.clear()
        
    def start_tracking(self, metric_name: str) -> None:
        """Start tracking time for a metric."""
        self._start_times[metric_name] = time.time()
        
    def stop_tracking(self, metric_name: str) -> float:
        """Stop tracking time for a metric and return duration."""
        if metric_name not in self._start_times:
            return 0.0
            
        duration = time.time() - self._start_times[metric_name]
        self.record_time(metric_name, duration)
        del self._start_times[metric_name]
        return duration

# Global metrics collector instance
metrics_collector = MetricsCollector() 