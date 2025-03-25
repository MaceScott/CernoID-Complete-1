from typing import Dict, Optional, Any, List
import asyncio
import psutil
from datetime import datetime
from collections import defaultdict
from ...base import BaseComponent
from ..utils.errors import handle_errors, MetricsError

class MemoryMetrics(BaseComponent):
    """Memory metrics collector"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._interval = self.config.get('metrics.memory.interval', 60)
        self._stats = {
            'collections': 0,
            'errors': 0
        }

    async def initialize(self) -> None:
        """Initialize memory metrics collector"""
        pass

    async def cleanup(self) -> None:
        """Cleanup collector resources"""
        pass

    @handle_errors()
    async def collect(self) -> Dict[str, Any]:
        """Collect memory metrics"""
        try:
            # Get memory info
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics = {
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'free': memory.free,
                    'percent': memory.percent,
                    'active': getattr(memory, 'active', None),
                    'inactive': getattr(memory, 'inactive', None),
                    'buffers': getattr(memory, 'buffers', None),
                    'cached': getattr(memory, 'cached', None),
                    'shared': getattr(memory, 'shared', None)
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent,
                    'sin': getattr(swap, 'sin', None),
                    'sout': getattr(swap, 'sout', None)
                }
            }
            
            # Update stats
            self._stats['collections'] += 1
            
            return metrics
            
        except Exception as e:
            self._stats['errors'] += 1
            raise MetricsError(f"Memory metrics collection failed: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return self._stats.copy()

class MemoryBackend(BaseComponent):
    """In-memory metrics backend"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._metrics: Dict[datetime, Dict] = {}
        self._max_points = self.config.get('metrics.max_points', 10000)
        self._stats = {
            'points': 0,
            'series': 0
        }

    async def initialize(self) -> None:
        """Initialize memory backend"""
        pass

    async def cleanup(self) -> None:
        """Cleanup backend resources"""
        self._metrics.clear()

    async def flush(self, metrics: Dict) -> None:
        """Flush metrics to storage"""
        try:
            timestamp = metrics['timestamp']
            self._metrics[timestamp] = metrics
            
            # Limit stored points
            if len(self._metrics) > self._max_points:
                oldest = min(self._metrics.keys())
                del self._metrics[oldest]
                
            # Update stats
            self._stats['points'] = len(self._metrics)
            self._stats['series'] = len(metrics['labels'])
            
        except Exception as e:
            self.logger.error(f"Memory flush error: {str(e)}")

    async def query(self,
                   query: str,
                   start: datetime,
                   end: datetime,
                   step: str) -> Dict:
        """Query metrics"""
        try:
            results = defaultdict(list)
            
            # Filter metrics by time range
            for timestamp, metrics in sorted(
                self._metrics.items()
            ):
                if start <= timestamp <= end:
                    # Process each metric type
                    for metric_type in [
                        'gauges',
                        'counters',
                        'histograms',
                        'summaries'
                    ]:
                        for key, value in metrics[metric_type].items():
                            if isinstance(value, (int, float)):
                                results[f"{metric_type}.{key}"].append({
                                    'timestamp': timestamp,
                                    'value': value
                                })
                            elif isinstance(value, list):
                                # Calculate summary statistics
                                if value:
                                    results[f"{metric_type}.{key}"].append({
                                        'timestamp': timestamp,
                                        'min': min(value),
                                        'max': max(value),
                                        'avg': sum(value) / len(value),
                                        'count': len(value)
                                    })
                                    
            return {
                'status': 'success',
                'data': dict(results)
            }
            
        except Exception as e:
            self.logger.error(f"Memory query error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def cleanup(self, threshold: datetime) -> None:
        """Cleanup old metrics"""
        try:
            # Remove old metrics
            for timestamp in list(self._metrics.keys()):
                if timestamp < threshold:
                    del self._metrics[timestamp]
                    
            # Update stats
            self._stats['points'] = len(self._metrics)
            
        except Exception as e:
            self.logger.error(f"Memory cleanup error: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        return self._stats.copy() 