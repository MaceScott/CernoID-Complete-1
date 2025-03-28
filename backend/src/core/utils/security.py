"""
Security utilities and helpers.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
import os

import jwt
from passlib.context import CryptContext

class SecurityUtils:
    """Security utilities for the application."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: The plain text password.
            hashed_password: The hashed password.
            
        Returns:
            bool: True if the password matches, False otherwise.
        """
        if os.getenv("TESTING"):
            # For testing, use a simple comparison
            return plain_password == hashed_password
        else:
            # For production, use bcrypt
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: The password to hash.
            
        Returns:
            str: The hashed password.
        """
        if os.getenv("TESTING"):
            # For testing, return the password as is
            return password
        else:
            # For production, use bcrypt
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.hash(password)
    
    @staticmethod
    def create_token(data: dict, secret_key: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT token.
        
        Args:
            data: The data to encode in the token.
            secret_key: The secret key to use for signing.
            expires_delta: Optional expiration time.
            
        Returns:
            str: The encoded JWT token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, secret_key: str) -> dict:
        """
        Verify and decode a JWT token.
        
        Args:
            token: The token to verify.
            secret_key: The secret key used for signing.
            
        Returns:
            dict: The decoded token data.
            
        Raises:
            jwt.InvalidTokenError: If the token is invalid.
        """
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    
    @staticmethod
    def generate_random_string(length: int = 32) -> str:
        """
        Generate a cryptographically secure random string.
        
        Args:
            length: The length of the string to generate.
            
        Returns:
            str: The random string.
        """
        return secrets.token_urlsafe(length) 