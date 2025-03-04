from typing import Dict, Optional, Union
import logging
import logging.handlers
from datetime import datetime
import json
from pathlib import Path
import asyncio
from dataclasses import dataclass, asdict
import structlog
from pythonjsonlogger import jsonlogger

@dataclass
class LogConfig:
    """Logging configuration"""
    level: str
    format: str
    output_dir: Path
    max_size: int
    backup_count: int
    enable_console: bool
    enable_file: bool
    enable_json: bool
    enable_syslog: bool
    syslog_host: Optional[str] = None
    syslog_port: Optional[int] = None

class LogManager:
    """Advanced logging system"""
    
    def __init__(self, config: Dict):
        self.config = LogConfig(**config['logging'])
        self.log_dir = self.config.output_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._loggers: Dict[str, logging.Logger] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._setup_logging()
        self._processor_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start logging system"""
        self._processor_task = asyncio.create_task(self._process_log_queue())
        logging.info("Logging system started")

    async def stop(self) -> None:
        """Stop logging system"""
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logging.info("Logging system stopped")

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create logger"""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._setup_logger(logger)
            self._loggers[name] = logger
        return self._loggers[name]

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        # Set root logger level
        logging.root.setLevel(self.config.level)
        
        # Configure formatters
        formatters = self._setup_formatters()
        
        # Setup handlers
        if self.config.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatters['standard'])
            logging.root.addHandler(console_handler)
            
        if self.config.enable_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'application.log',
                maxBytes=self.config.max_size,
                backupCount=self.config.backup_count
            )
            file_handler.setFormatter(formatters['standard'])
            logging.root.addHandler(file_handler)
            
        if self.config.enable_json:
            json_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'application.json',
                maxBytes=self.config.max_size,
                backupCount=self.config.backup_count
            )
            json_handler.setFormatter(formatters['json'])
            logging.root.addHandler(json_handler)
            
        if self.config.enable_syslog and self.config.syslog_host:
            syslog_handler = logging.handlers.SysLogHandler(
                address=(self.config.syslog_host, self.config.syslog_port or 514)
            )
            syslog_handler.setFormatter(formatters['standard'])
            logging.root.addHandler(syslog_handler)

    def _setup_formatters(self) -> Dict:
        """Setup log formatters"""
        return {
            'standard': logging.Formatter(
                self.config.format,
                datefmt='%Y-%m-%d %H:%M:%S'
            ),
            'json': jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            ),
            'structured': structlog.PrintfRenderer()
        }

    def _setup_logger(self, logger: logging.Logger) -> None:
        """Setup individual logger"""
        logger.propagate = False
        
        # Add custom attributes
        logger = structlog.wrap_logger(
            logger,
            processor_chain=[
                structlog.processors.TimeStamper(fmt='iso'),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                self._add_extra_fields
            ]
        )
        
        # Add custom methods
        logger.audit = self._audit_log
        logger.metric = self._metric_log
        logger.trace = self._trace_log

    async def _process_log_queue(self) -> None:
        """Process logging queue"""
        while True:
            try:
                log_entry = await self._queue.get()
                
                # Process based on log type
                if log_entry['type'] == 'audit':
                    await self._write_audit_log(log_entry)
                elif log_entry['type'] == 'metric':
                    await self._write_metric_log(log_entry)
                elif log_entry['type'] == 'trace':
                    await self._write_trace_log(log_entry)
                    
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Log processing failed: {str(e)}")

    def _audit_log(self, 
                   logger: logging.Logger,
                   event: str,
                   **kwargs) -> None:
        """Log audit event"""
        log_entry = {
            'type': 'audit',
            'timestamp': datetime.utcnow().isoformat(),
            'logger': logger.name,
            'event': event,
            'data': kwargs
        }
        asyncio.create_task(self._queue.put(log_entry))

    def _metric_log(self,
                    logger: logging.Logger,
                    metric: str,
                    value: Union[int, float],
                    **kwargs) -> None:
        """Log metric"""
        log_entry = {
            'type': 'metric',
            'timestamp': datetime.utcnow().isoformat(),
            'logger': logger.name,
            'metric': metric,
            'value': value,
            'data': kwargs
        }
        asyncio.create_task(self._queue.put(log_entry))

    def _trace_log(self,
                   logger: logging.Logger,
                   operation: str,
                   **kwargs) -> None:
        """Log trace event"""
        log_entry = {
            'type': 'trace',
            'timestamp': datetime.utcnow().isoformat(),
            'logger': logger.name,
            'operation': operation,
            'data': kwargs
        }
        asyncio.create_task(self._queue.put(log_entry))

    async def _write_audit_log(self, entry: Dict) -> None:
        """Write audit log entry"""
        audit_file = self.log_dir / 'audit.json'
        async with aiofiles.open(audit_file, 'a') as f:
            await f.write(json.dumps(entry) + '\n')

    async def _write_metric_log(self, entry: Dict) -> None:
        """Write metric log entry"""
        metric_file = self.log_dir / 'metrics.json'
        async with aiofiles.open(metric_file, 'a') as f:
            await f.write(json.dumps(entry) + '\n')

    async def _write_trace_log(self, entry: Dict) -> None:
        """Write trace log entry"""
        trace_file = self.log_dir / 'trace.json'
        async with aiofiles.open(trace_file, 'a') as f:
            await f.write(json.dumps(entry) + '\n')

    @staticmethod
    def _add_extra_fields(logger: logging.Logger,
                         name: str,
                         event_dict: Dict) -> Dict:
        """Add extra fields to structured log"""
        event_dict['logger'] = name
        event_dict['host'] = platform.node()
        event_dict['process'] = os.getpid()
        return event_dict 