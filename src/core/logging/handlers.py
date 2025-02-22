from typing import Dict, Optional, Any, List, Union
import logging
import logging.handlers
import asyncio
from queue import Queue
from threading import Thread, Lock
from datetime import datetime
import json
from ..base import BaseComponent

class AsyncHandler(logging.Handler):
    """Asynchronous logging handler"""
    
    def __init__(self,
                 handler: logging.Handler,
                 queue_size: int = 1000):
        super().__init__()
        self._handler = handler
        self._queue: Queue = Queue(maxsize=queue_size)
        self._thread: Optional[Thread] = None
        self._lock = Lock()
        self._running = True
        self._start_worker()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record"""
        try:
            self._queue.put_nowait(record)
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """Close handler"""
        with self._lock:
            self._running = False
            
        if self._thread:
            self._thread.join()
            
        self._handler.close()
        super().close()

    def _start_worker(self) -> None:
        """Start worker thread"""
        def worker():
            while True:
                with self._lock:
                    if not self._running and self._queue.empty():
                        break
                        
                try:
                    record = self._queue.get(timeout=1)
                    self._handler.emit(record)
                    self._queue.task_done()
                except Exception:
                    pass
                    
        self._thread = Thread(target=worker, daemon=True)
        self._thread.start()


class JSONHandler(logging.Handler):
    """JSON logging handler"""
    
    def __init__(self,
                 stream,
                 additional_fields: Optional[Dict] = None):
        super().__init__()
        self.stream = stream
        self.additional_fields = additional_fields or {}

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record"""
        try:
            message = self.format(record)
            
            # Create JSON log entry
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': message,
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Add exception info
            if record.exc_info:
                log_entry['exception'] = self.formatException(
                    record.exc_info
                )
                
            # Add additional fields
            log_entry.update(self.additional_fields)
            
            # Write JSON
            self.stream.write(json.dumps(log_entry) + '\n')
            self.stream.flush()
            
        except Exception:
            self.handleError(record)


class MetricsHandler(logging.Handler):
    """Metrics logging handler"""
    
    def __init__(self, metrics_manager: Any):
        super().__init__()
        self.metrics = metrics_manager

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record"""
        try:
            # Update log message counter
            self.metrics.counter(
                'log_messages_total',
                1,
                {
                    'level': record.levelname,
                    'logger': record.name
                }
            )
            
            # Update level-specific counters
            if record.levelno >= logging.ERROR:
                self.metrics.counter('log_errors_total', 1)
            elif record.levelno >= logging.WARNING:
                self.metrics.counter('log_warnings_total', 1)
                
        except Exception:
            self.handleError(record)


class BufferedHandler(logging.Handler):
    """Buffered logging handler"""
    
    def __init__(self,
                 handler: logging.Handler,
                 buffer_size: int = 100,
                 flush_interval: float = 5.0):
        super().__init__()
        self._handler = handler
        self._buffer: List[logging.LogRecord] = []
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval
        self._lock = Lock()
        self._last_flush = datetime.utcnow()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record"""
        try:
            with self._lock:
                self._buffer.append(record)
                
                # Check if buffer should be flushed
                should_flush = (
                    len(self._buffer) >= self._buffer_size or
                    (datetime.utcnow() - self._last_flush).total_seconds() >= self._flush_interval
                )
                
                if should_flush:
                    self.flush()
                    
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        """Flush buffered records"""
        with self._lock:
            if not self._buffer:
                return
                
            # Emit all records
            for record in self._buffer:
                self._handler.emit(record)
                
            # Clear buffer
            self._buffer.clear()
            self._last_flush = datetime.utcnow()

    def close(self) -> None:
        """Close handler"""
        self.flush()
        self._handler.close()
        super().close() 