from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import json
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import uuid
from elasticsearch import AsyncElasticsearch
import aiofiles
import structlog

from ..utils.config import get_settings
from ..utils.logging import get_logger
from ..database.service import DatabaseService
from ..interfaces.security import DatabaseInterface, EncryptionInterface

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
        try:
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

            self.logger.info(f"Audit event '{event.event_type.value}' logged successfully")

        except Exception as e:
            self.logger.error(f"Failed to write audit event '{event.event_type.value}': {str(e)}")
            raise

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

class AuditLogger:
    """
    Secure audit logging system with tamper detection
    """
    
    def __init__(self,
                 database: DatabaseInterface,
                 encryption: EncryptionInterface):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.db = database
        self.encryption = encryption
        
        # Initialize Elasticsearch client
        self.es = AsyncElasticsearch([self.settings.elasticsearch_url])
        
        # Initialize structured logger
        self.audit_logger = structlog.get_logger("audit")
        
        # Initialize secure storage
        self.audit_dir = Path(self.settings.audit_dir)
        self.audit_dir.mkdir(exist_ok=True)
        
        # Initialize HMAC key
        self.hmac_key = self.settings.audit_hmac_key.encode()
        
    async def log_event(self,
                       event_type: str,
                       user_id: Optional[int],
                       resource: str,
                       action: str,
                       details: Dict[str, Any],
                       status: str = "success") -> str:
        """Log audit event with secure storage."""
        try:
            # Generate event ID
            event_id = str(uuid.uuid4())
            
            # Create event data
            event = {
                "event_id": event_id,
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "details": details,
                "status": status
            }
            
            # Add signature
            event["signature"] = self._create_signature(event)
            
            # Store event in multiple locations
            await asyncio.gather(
                self._store_elasticsearch(event),
                self._store_local(event),
                self.db.create_audit_event(event)
            )
            
            # Log structured event
            self.audit_logger.info(
                "audit_event",
                **event
            )
            
            return event_id
            
        except Exception as e:
            self.logger.error(f"Audit logging failed: {str(e)}")
            raise
            
    async def get_events(self,
                        filters: Dict[str, Any],
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve audit events with filtering."""
        try:
            # Build Elasticsearch query
            query = {
                "bool": {
                    "must": [
                        {"match": {k: v}} for k, v in filters.items()
                    ]
                }
            }
            
            if start_time or end_time:
                query["bool"]["filter"] = {
                    "range": {
                        "timestamp": {
                            "gte": start_time.isoformat() if start_time else None,
                            "lte": end_time.isoformat() if end_time else None
                        }
                    }
                }
                
            # Execute search
            response = await self.es.search(
                index=self.settings.audit_index,
                query=query,
                size=limit,
                sort=[{"timestamp": "desc"}]
            )
            
            events = []
            for hit in response["hits"]["hits"]:
                event = hit["_source"]
                
                # Verify signature
                stored_signature = event.pop("signature")
                calculated_signature = self._create_signature(event)
                
                if hmac.compare_digest(stored_signature, calculated_signature):
                    events.append(event)
                else:
                    self.logger.warning(
                        f"Invalid signature for event {event['event_id']}"
                    )
                    
            return events
            
        except Exception as e:
            self.logger.error(f"Event retrieval failed: {str(e)}")
            return []
            
    def _create_signature(self, event: Dict[str, Any]) -> str:
        """Create HMAC signature for event."""
        # Sort keys for consistent ordering
        event_str = json.dumps(event, sort_keys=True)
        
        # Create HMAC
        signature = hmac.new(
            self.hmac_key,
            event_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
        
    async def _store_local(self, event: Dict[str, Any]):
        """Store event in local file system."""
        file_path = self.audit_dir / f"{event['event_id']}.json"
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(event))
            
    async def _store_elasticsearch(self, event: Dict[str, Any]):
        """Store event in Elasticsearch."""
        await self.es.index(
            index=self.settings.audit_index,
            document=event,
            id=event['event_id']
        )
        
    async def verify_event(self, event_id: str) -> bool:
        """Verify event integrity."""
        try:
            # Get event from all storage locations
            event_sources = await asyncio.gather(
                self._get_local_event(event_id),
                self._get_elasticsearch_event(event_id),
                self._get_database_event(event_id)
            )
            
            # Compare events from different sources
            events = [e for e in event_sources if e is not None]
            if not events:
                return False
                
            # Verify signatures
            signatures = set()
            for event in events:
                stored_signature = event.pop("signature", None)
                if stored_signature:
                    calculated_signature = self._create_signature(event)
                    signatures.add(stored_signature)
                    
                    if not hmac.compare_digest(
                        stored_signature,
                        calculated_signature
                    ):
                        return False
                        
            # Check if all signatures match
            return len(signatures) == 1
            
        except Exception as e:
            self.logger.error(f"Event verification failed: {str(e)}")
            return False
            
    async def cleanup(self):
        """Cleanup resources."""
        await self.es.close()

# Global audit logger instance
audit_logger = AuditLogger() 