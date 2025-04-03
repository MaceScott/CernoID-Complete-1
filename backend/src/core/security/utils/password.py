import bcrypt
import secrets
import logging
from typing import Tuple, Optional
from ..logging.config import LogConfig

logger = LogConfig().get_logger(__name__)

def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Hash a password using bcrypt with a random salt.
    
    Args:
        password: Password to hash
        salt: Optional salt to use (for testing)
        
    Returns:
        Tuple[bytes, bytes]: (hashed_password, salt)
    """
    try:
        # Generate random salt if not provided
        if salt is None:
            salt = bcrypt.gensalt()
            
        # Hash password with salt
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return hashed, salt
        
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise ValueError("Failed to hash password")

def verify_password(password: str, hashed: bytes) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Password to verify
        hashed: Hashed password to check against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed
        )
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def generate_password_reset_token() -> str:
    """
    Generate a secure random token for password reset.
    
    Returns:
        str: Random token
    """
    try:
        return secrets.token_urlsafe(32)
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        raise ValueError("Failed to generate token")

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
        
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
        
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
        
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
        
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
        
    return True, "Password meets strength requirements" 