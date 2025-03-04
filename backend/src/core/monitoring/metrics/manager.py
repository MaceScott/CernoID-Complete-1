from typing import Dict, Optional, Any, List, Union, Callable
import asyncio
from datetime import datetime, timedelta
import time
from collections import defaultdict
from ..base import BaseComponent
from ..utils.errors import handle_errors, MetricsError
import importlib

class MetricsManager(BaseComponent):
    """Advanced metrics management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._collectors: Dict[str, 'Collector'] = {}
        self._storage: Dict[str, Any] = {}
        self._handlers: Dict[str, Callable] = {}
        self._buffer_size = self.config.get('metrics.buffer_size', 1000)
        self._flush_interval = self.config.get('metrics.flush_interval', 60)
        self._retention_days = self.config.get('metrics.retention_days', 30)
        self._buffer: Dict[str, List] = defaultdict(list)
        self._last_flush = time.time()
        self._stats = {
            'collected': 0,
            'flushed': 0,
            'errors': 0
        }

    async def initialize(self) -> None:
        """Initialize metrics manager"""
        try:
            # Initialize storage backend
            storage_type = self.config.get('metrics.storage', 'memory')
            storage_config = self.config.get('metrics.storage_config', {})
            
            module = importlib.import_module(
                f".storage.{storage_type}",
                package="core.metrics"
            )
            
            self._storage = await module.create_storage(storage_config)
            
            # Register default collectors
            await self._register_default_collectors()
            
            # Start background tasks
            self._start_background_tasks()
            
        except Exception as e:
            raise MetricsError(f"Metrics initialization failed: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup metrics resources"""
        try:
            # Flush remaining metrics
            await self._flush_metrics()
            
            # Cleanup storage
            if self._storage:
                await self._storage.cleanup()
                
            self._collectors.clear()
            self._handlers.clear()
            self._buffer.clear()
            
        except Exception as e:
            self.logger.error(f"Metrics cleanup error: {str(e)}")

    @handle_errors(logger=None)
    async def collect(self,
                     name: str,
                     value: Union[int, float],
                     tags: Optional[Dict] = None,
                     timestamp: Optional[float] = None) -> None:
        """Collect metric"""
        try:
            # Validate inputs
            if not isinstance(value, (int, float)):
                raise ValueError("Metric value must be numeric")
                
            # Create metric entry
            metric = {
                'name': name,
                'value': value,
                'tags': tags or {},
                'timestamp': timestamp or time.time()
            }
            
            # Add to buffer
            self._buffer[name].append(metric)
            self._stats['collected'] += 1
            
            # Check buffer size
            if len(self._buffer[name]) >= self._buffer_size:
                await self._flush_metrics(names=[name])
                
        except Exception as e:
            self._stats['errors'] += 1
            raise MetricsError(f"Metric collection failed: {str(e)}")

    @handle_errors(logger=None)
    async def query(self,
                   name: str,
                   start: datetime,
                   end: Optional[datetime] = None,
                   tags: Optional[Dict] = None,
                   aggregation: Optional[str] = None) -> List[Dict]:
        """Query metrics"""
        try:
            # Validate inputs
            if end is None:
                end = datetime.utcnow()
                
            if start >= end:
                raise ValueError("Start time must be before end time")
                
            # Query storage
            results = await self._storage.query(
                name,
                start.timestamp(),
                end.timestamp(),
                tags,
                aggregation
            )
            
            return results
            
        except Exception as e:
            raise MetricsError(f"Metrics query failed: {str(e)}")

    async def register_collector(self,
                               name: str,
                               collector: 'Collector') -> None:
        """Register metric collector"""
        self._collectors[name] = collector
        await collector.initialize()

    async def register_handler(self,
                             name: str,
                             handler: Callable) -> None:
        """Register metric handler"""
        self._handlers[name] = handler

    async def get_stats(self) -> Dict[str, Any]:
        """Get metrics statistics"""
        stats = self._stats.copy()
        
        # Add collector stats
        stats['collectors'] = {
            name: await collector.get_stats()
            for name, collector in self._collectors.items()
        }
        
        # Add storage stats
        if self._storage:
            stats['storage'] = await self._storage.get_stats()
            
        return stats

    def _start_background_tasks(self) -> None:
        """Start background tasks"""
        asyncio.create_task(self._flush_task())
        asyncio.create_task(self._cleanup_task())
        asyncio.create_task(self._collect_task())

    async def _flush_metrics(self,
                           names: Optional[List[str]] = None) -> None:
        """Flush metrics to storage"""
        try:
            flush_time = time.time()
            metrics_to_flush = {}
            
            # Get metrics to flush
            if names:
                for name in names:
                    if name in self._buffer:
                        metrics_to_flush[name] = self._buffer[name]
                        self._buffer[name] = []
            else:
                metrics_to_flush = self._buffer.copy()
                self._buffer.clear()
            
            # Store metrics
            for name, metrics in metrics_to_flush.items():
                if metrics:
                    await self._storage.store(name, metrics)
                    self._stats['flushed'] += len(metrics)
                    
                    # Call handlers
                    handler = self._handlers.get(name)
                    if handler:
                        await handler(metrics)
            
            self._last_flush = flush_time
            
        except Exception as e:
            self._stats['errors'] += 1
            self.logger.error(f"Metrics flush error: {str(e)}")

    async def _flush_task(self) -> None:
        """Periodic metrics flush task"""
        while True:
            try:
                if time.time() - self._last_flush >= self._flush_interval:
                    await self._flush_metrics()
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Flush task error: {str(e)}")
                await asyncio.sleep(1)

    async def _cleanup_task(self) -> None:
        """Cleanup old metrics task"""
        while True:
            try:
                # Calculate retention threshold
                threshold = datetime.utcnow() - timedelta(
                    days=self._retention_days
                )
                
                # Cleanup old metrics
                await self._storage.cleanup(threshold.timestamp())
                await asyncio.sleep(3600)  # Run hourly
                
            except Exception as e:
                self.logger.error(f"Cleanup task error: {str(e)}")
                await asyncio.sleep(3600)

    async def _collect_task(self) -> None:
        """Run collectors task"""
        while True:
            try:
                # Run collectors
                for collector in self._collectors.values():
                    metrics = await collector.collect()
                    for metric in metrics:
                        await self.collect(**metric)
                        
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                self.logger.error(f"Collect task error: {str(e)}")
                await asyncio.sleep(60)

    async def _register_default_collectors(self) -> None:
        """Register default metric collectors"""
        from .collectors.system import SystemCollector
        from .collectors.process import ProcessCollector
        
        await self.register_collector(
            'system',
            SystemCollector(self.config)
        )
        await self.register_collector(
            'process',
            ProcessCollector(self.config)
        ) 