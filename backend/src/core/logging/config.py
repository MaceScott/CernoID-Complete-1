import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

class LogConfig:
    """Logging configuration"""
    
    def __init__(
        self,
        log_dir: str = "logs",
        log_level: str = "INFO",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        format: Optional[str] = None
    ):
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.format = format or (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def setup(self) -> None:
        """Set up logging configuration"""
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers = []
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(
            logging.Formatter(self.format)
        )
        root_logger.addHandler(console_handler)
        
        # Add file handler
        log_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(
            logging.Formatter(self.format)
        )
        root_logger.addHandler(file_handler)
        
        # Add error file handler
        error_file = self.log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(self.format)
        )
        root_logger.addHandler(error_handler)
        
        # Add security file handler
        security_file = self.log_dir / f"security_{datetime.now().strftime('%Y%m%d')}.log"
        security_handler = logging.handlers.RotatingFileHandler(
            security_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(
            logging.Formatter(self.format)
        )
        root_logger.addHandler(security_handler)
        
        # Log configuration
        logging.info("Logging configuration initialized")
        
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance with the specified name.
        
        Args:
            name: Logger name
            
        Returns:
            logging.Logger: Logger instance
        """
        return logging.getLogger(name)
        
    def log_security_event(
        self,
        event_type: str,
        details: dict,
        severity: str = "INFO"
    ) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity
        """
        logger = self.get_logger("security")
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "details": details
        }
        
        if severity.upper() == "ERROR":
            logger.error(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
            
    def log_audit_event(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Optional[dict] = None
    ) -> None:
        """
        Log an audit event.
        
        Args:
            user_id: ID of the user performing the action
            action: Action performed
            resource: Resource affected
            details: Additional details
        """
        logger = self.get_logger("audit")
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {}
        }
        logger.info(json.dumps(log_data)) 