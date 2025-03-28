import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, TextIO
import json
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
import sys
import traceback
import threading
import queue
import socket
import aiofiles
import aioredis
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import structlog
from pythonjsonlogger import jsonlogger
from ..utils.decorators import handle_errors

@dataclass
class LogConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "json"  # json, text
    output: List[str] = None  # file, console, redis
    file_path: str = "logs/app.log"
    max_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    rotation_interval: str = "D"  # S, M, H, D, W0-W6
    redis_key: str = "application_logs"
    redis_max_logs: int = 10000
    include_trace: bool = True
    include_context: bool = True
    async_mode: bool = True

class AsyncLogHandler(logging.Handler):
    """Asynchronous log handler"""
    
    def __init__(self, queue_size: int = 1000):
        super().__init__()
        self.queue = queue.Queue(maxsize=queue_size)
        self.worker = threading.Thread(target=self._process_logs)
        self.worker.daemon = True
        self.running = True
        self.worker.start()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record"""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            sys.stderr.write("Log queue is full, dropping log record\n")

    def _process_logs(self) -> None:
        """Process queued log records"""
        while self.running:
            try:
                record = self.queue.get(timeout=1)
                self.handle_log(record)
            except queue.Empty:
                continue
            except Exception as e:
                sys.stderr.write(f"Log processing failed: {str(e)}\n")

    def handle_log(self, record: logging.LogRecord) -> None:
        """Handle log record - to be implemented by subclasses"""
        pass

    def close(self) -> None:
        """Close handler"""
        self.running = False
        self.worker.join()
        super().close()

class RedisLogHandler(AsyncLogHandler):
    """Redis log handler"""
    
    def __init__(self, redis_url: str, redis_key: str, max_logs: int):
        super().__init__()
        self.redis_url = redis_url
        self.redis_key = redis_key
        self.max_logs = max_logs
        self._redis: Optional[aioredis.Redis] = None
        self._connect_redis()

    def _connect_redis(self) -> None:
        """Connect to Redis"""
        try:
            loop = asyncio.new_event_loop()
            self._redis = loop.run_until_complete(
                aioredis.create_redis_pool(self.redis_url)
            )
        except Exception as e:
            sys.stderr.write(f"Redis connection failed: {str(e)}\n")

    def handle_log(self, record: logging.LogRecord) -> None:
        """Handle log record"""
        if not self._redis:
            return
            
        try:
            # Format log record
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "path": record.pathname,
                "line": record.lineno
            }
            
            if hasattr(record, "context"):
                log_entry["context"] = record.context
                
            if record.exc_info:
                log_entry["exception"] = "".join(
                    traceback.format_exception(*record.exc_info)
                )
                
            # Add log to Redis
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._add_log_to_redis(log_entry))
            
        except Exception as e:
            sys.stderr.write(f"Redis log handling failed: {str(e)}\n")

    async def _add_log_to_redis(self, log_entry: Dict) -> None:
        """Add log entry to Redis"""
        try:
            # Add log entry
            await self._redis.lpush(
                self.redis_key,
                json.dumps(log_entry)
            )
            
            # Trim log list if needed
            await self._redis.ltrim(
                self.redis_key,
                0,
                self.max_logs - 1
            )
            
        except Exception as e:
            sys.stderr.write(f"Redis log addition failed: {str(e)}\n")

class LogManager:
    """Advanced logging management system"""
    
    def __init__(self, config: dict):
        self.config = config
        self._handlers: Dict[str, logging.Handler] = {}
        self._formatters: Dict[str, logging.Formatter] = {}
        self._filters: Dict[str, logging.Filter] = {}
        self._loggers: Dict[str, logging.Logger] = {}
        self._default_level = config.get('logging.level', 'INFO')
        self._default_format = config.get(
            'logging.format',
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        self._rotation_interval = config.get(
            'logging.rotation_interval',
            'D'
        )
        self._retention_days = config.get('logging.retention_days', 30)
        self._async_mode = config.get('logging.async', True)
        self._queue_size = config.get('logging.queue_size', 1000)
        self._stats = {
            'messages': 0,
            'errors': 0,
            'warnings': 0
        }

    @handle_errors
    async def initialize(self) -> None:
        """Initialize logging manager"""
        # Configure root logger
        root = logging.getLogger()
        root.setLevel(self._default_level)
        
        # Clear existing handlers
        root.handlers.clear()
        
        # Setup handlers
        handlers = self.config.get('logging.handlers', {})
        for name, config in handlers.items():
            handler = self._create_handler(name, config)
            if handler:
                root.addHandler(handler)
                self._handlers[name] = handler
                
        # Setup formatters
        formatters = self.config.get('logging.formatters', {})
        for name, config in formatters.items():
            formatter = self._create_formatter(config)
            self._formatters[name] = formatter
            
        # Setup filters
        filters = self.config.get('logging.filters', {})
        for name, config in filters.items():
            filter_ = self._create_filter(config)
            self._filters[name] = filter_
            
        # Start cleanup task
        if any(isinstance(h, logging.FileHandler)
               for h in self._handlers.values()):
            asyncio.create_task(self._cleanup_task())

    @handle_errors
    async def cleanup(self) -> None:
        """Cleanup logging resources"""
        # Close handlers
        for handler in self._handlers.values():
            handler.close()
            
        self._handlers.clear()
        self._formatters.clear()
        self._filters.clear()
        self._loggers.clear()

    @handle_errors
    def get_logger(self,
                  name: str,
                  level: Optional[str] = None) -> logging.Logger:
        """Get logger instance"""
        if name in self._loggers:
            return self._loggers[name]
            
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(level or self._default_level)
        
        # Store logger
        self._loggers[name] = logger
        return logger

    @handle_errors
    def set_level(self,
                 level: str,
                 logger_name: Optional[str] = None) -> None:
        """Set logging level"""
        if logger_name:
            # Set level for specific logger
            logger = self.get_logger(logger_name)
            logger.setLevel(level)
        else:
            # Set level for all loggers
            logging.getLogger().setLevel(level)
            for logger in self._loggers.values():
                logger.setLevel(level)

    def add_handler(self,
                   name: str,
                   handler: logging.Handler) -> None:
        """Add logging handler"""
        self._handlers[name] = handler
        logging.getLogger().addHandler(handler)

    def remove_handler(self, name: str) -> None:
        """Remove logging handler"""
        if name in self._handlers:
            handler = self._handlers.pop(name)
            logging.getLogger().removeHandler(handler)
            handler.close()

    def add_filter(self,
                  name: str,
                  filter_: logging.Filter) -> None:
        """Add logging filter"""
        self._filters[name] = filter_
        for handler in self._handlers.values():
            handler.addFilter(filter_)

    def remove_filter(self, name: str) -> None:
        """Remove logging filter"""
        if name in self._filters:
            filter_ = self._filters.pop(name)
            for handler in self._handlers.values():
                handler.removeFilter(filter_)

    async def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        return self._stats.copy()

    def _create_handler(self,
                       name: str,
                       config: Dict) -> Optional[logging.Handler]:
        """Create logging handler"""
        try:
            handler_type = config.get('type', 'stream')
            
            if handler_type == 'stream':
                stream = sys.stdout if config.get('stream') == 'stdout' else sys.stderr
                handler = logging.StreamHandler(stream)
                
            elif handler_type == 'file':
                path = Path(config['filename'])
                path.parent.mkdir(parents=True, exist_ok=True)
                handler = logging.FileHandler(
                    path,
                    mode=config.get('mode', 'a'),
                    encoding=config.get('encoding', 'utf8')
                )
                
            elif handler_type == 'rotating_file':
                path = Path(config['filename'])
                path.parent.mkdir(parents=True, exist_ok=True)
                handler = logging.handlers.TimedRotatingFileHandler(
                    path,
                    when=self._rotation_interval,
                    backupCount=config.get('backup_count', 7),
                    encoding=config.get('encoding', 'utf8')
                )
                
            else:
                self.logger.error(f"Unknown handler type: {handler_type}")
                return None
                
            # Set formatter
            formatter = config.get('formatter')
            if formatter in self._formatters:
                handler.setFormatter(self._formatters[formatter])
            else:
                handler.setFormatter(
                    logging.Formatter(self._default_format)
                )
                
            # Set level
            handler.setLevel(config.get('level', self._default_level))
            
            # Add filters
            for filter_ in config.get('filters', []):
                if filter_ in self._filters:
                    handler.addFilter(self._filters[filter_])
                    
            return handler
            
        except Exception as e:
            self.logger.error(f"Handler creation error: {str(e)}")
            return None

    def _create_formatter(self, config: Dict) -> logging.Formatter:
        """Create logging formatter"""
        return logging.Formatter(
            fmt=config.get('format', self._default_format),
            datefmt=config.get('date_format', '%Y-%m-%d %H:%M:%S')
        )

    def _create_filter(self, config: Dict) -> logging.Filter:
        """Create logging filter"""
        class CustomFilter(logging.Filter):
            def filter(self, record):
                return eval(config['expression'], {'record': record})
                
        return CustomFilter()

    async def _cleanup_task(self) -> None:
        """Cleanup old log files"""
        while True:
            try:
                threshold = datetime.utcnow() - timedelta(
                    days=self._retention_days
                )
                
                # Find log files
                for handler in self._handlers.values():
                    if isinstance(
                        handler,
                        (logging.FileHandler, logging.handlers.TimedRotatingFileHandler)
                    ):
                        path = Path(handler.baseFilename)
                        directory = path.parent
                        
                        # Remove old files
                        for file in directory.glob('*.log*'):
                            if file.stat().st_mtime < threshold.timestamp():
                                try:
                                    file.unlink()
                                except Exception as e:
                                    self.logger.error(
                                        f"Log cleanup error: {str(e)}"
                                    )
                                    
                await asyncio.sleep(3600)  # Run hourly
                
            except Exception as e:
                self.logger.error(f"Cleanup task error: {str(e)}")
                await asyncio.sleep(3600) 