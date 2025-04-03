import secrets
import time
import logging
from typing import Dict, Optional
from fastapi import HTTPException
from ..logging.config import LogConfig

logger = LogConfig().get_logger(__name__)

class SessionManager:
    def __init__(
        self,
        session_lifetime: int = 3600,  # 1 hour
        max_sessions_per_user: int = 5,
        cleanup_interval: int = 300  # 5 minutes
    ):
        """
        Initialize session manager.
        
        Args:
            session_lifetime: Session lifetime in seconds
            max_sessions_per_user: Maximum sessions per user
            cleanup_interval: Cleanup interval in seconds
        """
        self.session_lifetime = session_lifetime
        self.max_sessions_per_user = max_sessions_per_user
        self.cleanup_interval = cleanup_interval
        self.sessions: Dict[str, Dict] = {}
        self.user_sessions: Dict[str, list] = {}
        self.last_cleanup = time.time()
        
    def create_session(self, user_id: str, ip: str) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: User ID
            ip: IP address
            
        Returns:
            str: Session token
            
        Raises:
            HTTPException: If max sessions exceeded
        """
        try:
            # Check max sessions per user
            if user_id in self.user_sessions:
                if len(self.user_sessions[user_id]) >= self.max_sessions_per_user:
                    raise HTTPException(
                        status_code=403,
                        detail="Maximum number of sessions reached"
                    )
                    
            # Generate session token
            token = secrets.token_urlsafe(32)
            
            # Create session data
            session_data = {
                "user_id": user_id,
                "ip": ip,
                "created_at": time.time(),
                "last_activity": time.time()
            }
            
            # Store session
            self.sessions[token] = session_data
            
            # Update user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(token)
            
            return token
            
        except Exception as e:
            logger.error(f"Session creation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create session"
            )
            
    def validate_session(self, token: str, ip: str) -> bool:
        """
        Validate a session token.
        
        Args:
            token: Session token
            ip: IP address
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check if session exists
            if token not in self.sessions:
                return False
                
            session = self.sessions[token]
            
            # Check session lifetime
            if time.time() - session["created_at"] > self.session_lifetime:
                self.delete_session(token)
                return False
                
            # Check IP address
            if session["ip"] != ip:
                self.delete_session(token)
                return False
                
            # Update last activity
            session["last_activity"] = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return False
            
    def delete_session(self, token: str) -> None:
        """
        Delete a session.
        
        Args:
            token: Session token
        """
        try:
            if token in self.sessions:
                user_id = self.sessions[token]["user_id"]
                del self.sessions[token]
                
                if user_id in self.user_sessions:
                    self.user_sessions[user_id].remove(token)
                    if not self.user_sessions[user_id]:
                        del self.user_sessions[user_id]
                        
        except Exception as e:
            logger.error(f"Session deletion error: {str(e)}")
            
    def delete_user_sessions(self, user_id: str) -> None:
        """
        Delete all sessions for a user.
        
        Args:
            user_id: User ID
        """
        try:
            if user_id in self.user_sessions:
                for token in self.user_sessions[user_id]:
                    del self.sessions[token]
                del self.user_sessions[user_id]
                
        except Exception as e:
            logger.error(f"User sessions deletion error: {str(e)}")
            
    def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        try:
            current_time = time.time()
            
            # Check if cleanup needed
            if current_time - self.last_cleanup < self.cleanup_interval:
                return
                
            # Clean up expired sessions
            expired_tokens = [
                token for token, session in self.sessions.items()
                if current_time - session["created_at"] > self.session_lifetime
            ]
            
            for token in expired_tokens:
                self.delete_session(token)
                
            self.last_cleanup = current_time
            
        except Exception as e:
            logger.error(f"Session cleanup error: {str(e)}")

# Global session manager instance
session_manager = SessionManager() 