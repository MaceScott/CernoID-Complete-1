"""
Security-related interfaces to break circular dependencies.
"""
from typing import Dict, Any, Optional, Protocol
from datetime import datetime

class AuditInterface(Protocol):
    """Interface for audit logging system."""
    
    async def log_event(self,
                       event_type: str,
                       user_id: Optional[int],
                       resource: str,
                       action: str,
                       details: Dict[str, Any],
                       status: str = "success") -> str:
        """Log audit event."""
        ...
        
    async def verify_event(self, event_id: str) -> bool:
        """Verify event integrity."""
        ...
        
    async def get_events(self,
                        start_time: datetime,
                        end_time: datetime,
                        filters: Optional[Dict[str, Any]] = None
                        ) -> List[Dict[str, Any]]:
        """Get audit events."""
        ...

class EncryptionInterface(Protocol):
    """Interface for encryption service."""
    
    async def encrypt(self,
                     data: bytes,
                     key_id: Optional[str] = None
                     ) -> Dict[str, Any]:
        """Encrypt data."""
        ...
        
    async def decrypt(self,
                     encrypted_data: Dict[str, Any]
                     ) -> bytes:
        """Decrypt data."""
        ...
        
    async def rotate_keys(self) -> Dict[str, Any]:
        """Rotate encryption keys."""
        ...

class DatabaseInterface(Protocol):
    """Interface for database operations."""
    
    async def create_audit_event(self,
                               event: Dict[str, Any]
                               ) -> str:
        """Create audit event record."""
        ...
        
    async def get_audit_events(self,
                             filters: Dict[str, Any]
                             ) -> List[Dict[str, Any]]:
        """Get audit events."""
        ...
        
    async def verify_event_integrity(self,
                                   event_id: str
                                   ) -> bool:
        """Verify event integrity."""
        ... 