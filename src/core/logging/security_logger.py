from datetime import datetime
import logging
from typing import Dict, Any
import json
from pathlib import Path
from core.error_handling import handle_exceptions

class SecurityLogger:
    def __init__(self):
        self.log_dir = Path("logs/security")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_loggers()

    def _setup_loggers(self):
        # Main security logger
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.INFO)
        
        # Separate loggers for different security events
        self.access_logger = logging.getLogger('security.access')
        self.threat_logger = logging.getLogger('security.threats')
        self.face_logger = logging.getLogger('security.faces')

        # Setup handlers with rotation
        for logger in [self.security_logger, self.access_logger, 
                      self.threat_logger, self.face_logger]:
            handler = logging.handlers.RotatingFileHandler(
                self.log_dir / f"{logger.name}.log",
                maxBytes=10_000_000,  # 10MB
                backupCount=30        # Keep 30 days of logs
            )
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)

    @handle_exceptions(logger=logging.getLogger('system'))
    async def log_security_event(self, event_type: str, data: Dict[str, Any]):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'data': data
        }
        
        if event_type.startswith('face_'):
            self.face_logger.info(json.dumps(log_entry))
        elif event_type.startswith('threat_'):
            self.threat_logger.warning(json.dumps(log_entry))
        elif event_type.startswith('access_'):
            self.access_logger.info(json.dumps(log_entry)) 
