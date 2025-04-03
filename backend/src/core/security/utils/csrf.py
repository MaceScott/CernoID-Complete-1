import secrets
import time
import logging
from typing import Dict, Optional
from fastapi import HTTPException, Request
from ..logging.config import LogConfig

logger = LogConfig().get_logger(__name__)

class CSRFProtection:
    def __init__(
        self,
        token_lifetime: int = 3600,  # 1 hour
        cleanup_interval: int = 300  # 5 minutes
    ):
        """
        Initialize CSRF protection.
        
        Args:
            token_lifetime: Token lifetime in seconds
            cleanup_interval: Cleanup interval in seconds
        """
        self.token_lifetime = token_lifetime
        self.cleanup_interval = cleanup_interval
        self.tokens: Dict[str, Dict] = {}
        self.last_cleanup = time.time()
        
    def generate_token(self, user_id: str) -> str:
        """
        Generate a CSRF token for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            str: CSRF token
        """
        try:
            # Generate token
            token = secrets.token_urlsafe(32)
            
            # Store token data
            self.tokens[token] = {
                "user_id": user_id,
                "created_at": time.time()
            }
            
            return token
            
        except Exception as e:
            logger.error(f"CSRF token generation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate CSRF token"
            )
            
    def validate_token(self, token: str, user_id: str) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: CSRF token
            user_id: User ID
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check if token exists
            if token not in self.tokens:
                return False
                
            token_data = self.tokens[token]
            
            # Check token lifetime
            if time.time() - token_data["created_at"] > self.token_lifetime:
                self.delete_token(token)
                return False
                
            # Check user ID
            if token_data["user_id"] != user_id:
                self.delete_token(token)
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"CSRF token validation error: {str(e)}")
            return False
            
    def delete_token(self, token: str) -> None:
        """
        Delete a CSRF token.
        
        Args:
            token: CSRF token
        """
        try:
            if token in self.tokens:
                del self.tokens[token]
                
        except Exception as e:
            logger.error(f"CSRF token deletion error: {str(e)}")
            
    def delete_user_tokens(self, user_id: str) -> None:
        """
        Delete all CSRF tokens for a user.
        
        Args:
            user_id: User ID
        """
        try:
            expired_tokens = [
                token for token, data in self.tokens.items()
                if data["user_id"] == user_id
            ]
            
            for token in expired_tokens:
                self.delete_token(token)
                
        except Exception as e:
            logger.error(f"User CSRF tokens deletion error: {str(e)}")
            
    def cleanup_expired_tokens(self) -> None:
        """Clean up expired CSRF tokens."""
        try:
            current_time = time.time()
            
            # Check if cleanup needed
            if current_time - self.last_cleanup < self.cleanup_interval:
                return
                
            # Clean up expired tokens
            expired_tokens = [
                token for token, data in self.tokens.items()
                if current_time - data["created_at"] > self.token_lifetime
            ]
            
            for token in expired_tokens:
                self.delete_token(token)
                
            self.last_cleanup = current_time
            
        except Exception as e:
            logger.error(f"CSRF token cleanup error: {str(e)}")
            
    def verify_csrf_token(self, request: Request, user_id: str) -> None:
        """
        Verify CSRF token from request.
        
        Args:
            request: FastAPI request
            user_id: User ID
            
        Raises:
            HTTPException: If CSRF token is invalid
        """
        try:
            # Get token from header
            token = request.headers.get("X-CSRF-Token")
            
            if not token:
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token missing"
                )
                
            # Validate token
            if not self.validate_token(token, user_id):
                raise HTTPException(
                    status_code=403,
                    detail="Invalid CSRF token"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CSRF verification error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to verify CSRF token"
            )

# Global CSRF protection instance
csrf_protection = CSRFProtection() 