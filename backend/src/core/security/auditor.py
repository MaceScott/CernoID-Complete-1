from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import logging
from dataclasses import dataclass
import json
from pathlib import Path
import hashlib
import jwt
from cryptography.fernet import Fernet
import shutil

@dataclass
class SecurityEvent:
    """Security audit event"""
    event_id: str
    timestamp: datetime
    event_type: str
    severity: str
    source: str
    user_id: Optional[str]
    ip_address: Optional[str]
    details: Dict
    raw_data: str

class SecurityAuditor:
    """Security auditing and monitoring"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('SecurityAuditor')
        self.audit_dir = Path(config['audit_dir'])
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._current_log: Optional[Path] = None
        self._encryption_key = Fernet.generate_key()
        self._fernet = Fernet(self._encryption_key)
        self._setup_logging()

    async def log_event(self, event: SecurityEvent) -> None:
        """Log security event"""
        try:
            event.raw_data = self._encrypt_data(event.raw_data)
            event_hash = self._generate_event_hash(event)

            log_entry = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "severity": event.severity,
                "source": event.source,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "details": event.details,
                "raw_data": event.raw_data,
                "hash": event_hash
            }

            await self._write_log_entry(log_entry)
            await self._check_security_alerts(event)

            self.logger.info(f"Event {event.event_id} logged successfully")

        except Exception as e:
            self.logger.error(f"Event logging failed: {str(e)}")
            raise

    async def analyze_events(self, 
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           event_types: Optional[List[str]] = None) -> Dict:
        """Analyze security events"""
        try:
            events = await self._load_events(start_time, end_time, event_types)
            
            analysis = {
                "total_events": len(events),
                "severity_distribution": self._analyze_severity(events),
                "event_type_distribution": self._analyze_event_types(events),
                "ip_analysis": self._analyze_ip_addresses(events),
                "user_analysis": self._analyze_users(events),
                "temporal_analysis": self._analyze_temporal_patterns(events),
                "anomalies": self._detect_anomalies(events)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Event analysis failed: {str(e)}")
            raise

    async def verify_integrity(self) -> Dict:
        """Verify audit log integrity"""
        try:
            verification_results = {
                "verified": True,
                "issues": []
            }
            
            # Load all events
            events = await self._load_events()
            
            # Verify each event
            for event in events:
                stored_hash = event.pop('hash')
                calculated_hash = self._generate_event_hash(event)
                
                if stored_hash != calculated_hash:
                    verification_results["verified"] = False
                    verification_results["issues"].append({
                        "event_id": event['event_id'],
                        "timestamp": event['timestamp'],
                        "issue": "Hash mismatch"
                    })
                    
            return verification_results
            
        except Exception as e:
            self.logger.error(f"Integrity verification failed: {str(e)}")
            raise

    def _encrypt_data(self, data: str) -> str:
        try:
            encrypted_data = self._fernet.encrypt(data.encode()).decode()
            self.logger.info("Data encrypted successfully")
            return encrypted_data
        except Exception as e:
            self.logger.error(f"Data encryption failed: {str(e)}")
            raise

    def _decrypt_data(self, encrypted_data: str) -> str:
        try:
            decrypted_data = self._fernet.decrypt(encrypted_data.encode()).decode()
            self.logger.info("Data decrypted successfully")
            return decrypted_data
        except Exception as e:
            self.logger.error(f"Data decryption failed: {str(e)}")
            raise

    def _generate_event_hash(self, event: Dict) -> str:
        """Generate event hash for integrity verification"""
        event_str = json.dumps(event, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()

    async def _write_log_entry(self, entry: Dict) -> None:
        """Write log entry to file"""
        if not self._current_log or \
           self._current_log.stat().st_size > self.config['max_log_size']:
            await self._rotate_log_file()
            
        async with aiofiles.open(self._current_log, 'a') as f:
            await f.write(json.dumps(entry) + '\n')

    async def _rotate_log_file(self) -> None:
        """Rotate audit log file"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            self._current_log = self.audit_dir / f"audit_{timestamp}.log"

            if self._current_log.exists():
                archive_name = f"audit_{timestamp}.archive"
                shutil.move(self._current_log, self.audit_dir / archive_name)

            self.logger.info(f"Log file rotated successfully: {self._current_log}")
        except Exception as e:
            self.logger.error(f"Log file rotation failed: {str(e)}")
            raise

    async def _check_security_alerts(self, event: SecurityEvent) -> None:
        """Check for security alerts"""
        if event.severity in ['high', 'critical']:
            await self._send_security_alert(event)
            
        # Check for specific patterns
        if event.event_type == 'auth_failure':
            await self._check_auth_failures(event)
        elif event.event_type == 'access_denied':
            await self._check_access_violations(event)

    async def _send_security_alert(self, event: SecurityEvent) -> None:
        """Send security alert"""
        alert = {
            "timestamp": event.timestamp.isoformat(),
            "severity": event.severity,
            "event_type": event.event_type,
            "source": event.source,
            "details": event.details
        }
        
        # Implement alert notification system here
        self.logger.warning(f"Security Alert: {json.dumps(alert)}")

    def _analyze_severity(self, events: List[Dict]) -> Dict:
        """Analyze event severity distribution"""
        severity_counts = {}
        for event in events:
            severity = event['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts

    def _analyze_temporal_patterns(self, events: List[Dict]) -> Dict:
        """Analyze temporal patterns in events"""
        # Convert timestamps to datetime objects
        timestamps = [datetime.fromisoformat(e['timestamp']) for e in events]
        
        # Analyze hourly distribution
        hour_distribution = {}
        for ts in timestamps:
            hour = ts.hour
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
            
        return {
            "hourly_distribution": hour_distribution,
            "total_duration": (max(timestamps) - min(timestamps)).total_seconds()
        }

    def _detect_anomalies(self, events: List[Dict]) -> List[Dict]:
        """Detect security anomalies"""
        anomalies = []
        
        # Group events by source
        source_events = {}
        for event in events:
            source = event['source']
            if source not in source_events:
                source_events[source] = []
            source_events[source].append(event)
            
        # Detect anomalies for each source
        for source, source_events in source_events.items():
            # Check event frequency
            avg_interval = self._calculate_avg_interval(source_events)
            if avg_interval < self.config.get('min_event_interval', 1):
                anomalies.append({
                    "type": "high_frequency",
                    "source": source,
                    "details": f"Average interval: {avg_interval:.2f}s"
                })
                
        return anomalies

    @staticmethod
    def _calculate_avg_interval(events: List[Dict]) -> float:
        """Calculate average interval between events"""
        if len(events) < 2:
            return float('inf')
            
        timestamps = [
            datetime.fromisoformat(e['timestamp'])
            for e in sorted(events, key=lambda x: x['timestamp'])
        ]
        
        intervals = [
            (t2 - t1).total_seconds()
            for t1, t2 in zip(timestamps[:-1], timestamps[1:])
        ]
        
        return sum(intervals) / len(intervals) 