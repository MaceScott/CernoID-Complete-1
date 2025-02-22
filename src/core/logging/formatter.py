from typing import Any, Dict, Optional
import json
import logging
import traceback
from datetime import datetime
import socket
import platform
from pythonjsonlogger import jsonlogger

class StructuredFormatter(jsonlogger.JsonFormatter):
    """Enhanced JSON formatter with additional context"""
    
    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.hostname = socket.gethostname()
        self.platform_info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }

    def add_fields(self,
                  log_record: Dict[str, Any],
                  record: logging.LogRecord,
                  message_dict: Dict[str, Any]) -> None:
        """Add additional fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        log_record['timestamp'] = now
        log_record['datetime'] = now
        
        # Add log level
        log_record['level'] = record.levelname
        log_record['severity'] = record.levelno
        
        # Add source information
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add system information
        log_record['hostname'] = self.hostname
        log_record['platform'] = self.platform_info
        
        # Add process information
        log_record['process'] = record.process
        log_record['process_name'] = record.processName
        log_record['thread'] = record.thread
        log_record['thread_name'] = record.threadName
        
        # Add exception information if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # Add custom fields
        if hasattr(record, 'extra_fields'):
            log_record.update(record.extra_fields)

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m', # Red background
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        # Get original formatted message
        message = super().format(record)
        
        # Add color if level has one
        if record.levelname in self.COLORS:
            message = (
                f"{self.COLORS[record.levelname]}"
                f"{message}"
                f"{self.RESET}"
            )
            
        return message 