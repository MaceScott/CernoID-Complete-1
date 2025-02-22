from typing import Dict, Optional, List
import asyncio
from datetime import datetime
import json
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum

class AuditEventType(Enum):
    """Audit event types"""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    CONFIG_CHANGE = "config_change"
    MODEL_CHANGE = "model_change"
    SYSTEM_ERROR = "system_error"
    SECURITY_ALERT = "security_alert"

@dataclass
class AuditEvent:
    """Security audit event"""
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    ip_address: Optional[str]
    details: Dict
    severity: str

class SecurityAuditor:
    """Security audit logging and analysis"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.audit_dir = Path(config['audit_dir'])
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('SecurityAuditor')
        self._current_log_file: Optional[Path] = None
        self._rotate_size = config.get('rotate_size', 10 * 1024 * 1024)  # 10MB
        self._retention_days = config.get('retention_days', 90)
        self._initialize_log_file()

    async def log_event(self, 
                       event_type: AuditEventType,
                       user_id: Optional[str] = None,
                       ip_address: Optional[str] = None,
                       details: Dict = None,
                       severity: str = "INFO") -> None:
        """Log security audit event"""
        try:
            event = AuditEvent(
                event_type=event_type,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                ip_address=ip_address,
                details=details or {},
                severity=severity
            )
            
            await self._write_event(event)
            
            # Check for security alerts
            if severity in ["WARNING", "ERROR"]:
                await self._process_security_alert(event)
                
        except Exception as e:
            self.logger.error(f"Audit logging failed: {str(e)}")
            raise

    async def get_events(self, 
                        event_type: Optional[AuditEventType] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        user_id: Optional[str] = None) -> List[AuditEvent]:
        """Retrieve audit events with filtering"""
        events = []
        
        for log_file in sorted(self.audit_dir.glob("*.audit.json")):
            events.extend(await self._read_events(log_file))
            
        # Apply filters
        filtered_events = events
        if event_type:
            filtered_events = [e for e in filtered_events 
                             if e.event_type == event_type]
        if start_time:
            filtered_events = [e for e in filtered_events 
                             if e.timestamp >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events 
                             if e.timestamp <= end_time]
        if user_id:
            filtered_events = [e for e in filtered_events 
                             if e.user_id == user_id]
            
        return filtered_events

    async def analyze_security_patterns(self) -> Dict:
        """Analyze security patterns and anomalies"""
        events = await self.get_events()
        
        analysis = {
            'auth_failures': self._analyze_auth_failures(events),
            'access_patterns': self._analyze_access_patterns(events),
            'security_alerts': self._analyze_security_alerts(events),
            'timestamp': datetime.utcnow()
        }
        
        return analysis

    async def _write_event(self, event: AuditEvent) -> None:
        """Write audit event to log file"""
        if self._should_rotate_log():
            await self._rotate_log_file()
            
        event_data = {
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat(),
            'user_id': event.user_id,
            'ip_address': event.ip_address,
            'details': event.details,
            'severity': event.severity
        }
        
        with open(self._current_log_file, 'a') as f:
            f.write(json.dumps(event_data) + '\n')

    async def _process_security_alert(self, event: AuditEvent) -> None:
        """Process and notify security alerts"""
        alert_message = (
            f"Security Alert: {event.event_type.value}\n"
            f"Severity: {event.severity}\n"
            f"User: {event.user_id}\n"
            f"IP: {event.ip_address}\n"
            f"Details: {json.dumps(event.details)}"
        )
        
        self.logger.warning(alert_message)
        # Implement alert notification system here

    def _should_rotate_log(self) -> bool:
        """Check if log file should be rotated"""
        if not self._current_log_file.exists():
            return True
        return self._current_log_file.stat().st_size >= self._rotate_size

    async def _rotate_log_file(self) -> None:
        """Rotate audit log file"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        self._current_log_file = self.audit_dir / f"audit_{timestamp}.audit.json"
        await self._cleanup_old_logs()

    async def _cleanup_old_logs(self) -> None:
        """Clean up old audit logs"""
        cutoff_time = datetime.utcnow().timestamp() - (self._retention_days * 86400)
        
        for log_file in self.audit_dir.glob("*.audit.json"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                self.logger.info(f"Removed old audit log: {log_file}")

    def _initialize_log_file(self) -> None:
        """Initialize current log file"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        self._current_log_file = self.audit_dir / f"audit_{timestamp}.audit.json" 