from typing import Dict, List, Optional, Any, Union, Callable, Set
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json
import re
import hashlib
import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import Request, Response
import aioredis
import ipaddress
import jwt
import bcrypt
from ..base import BaseComponent
from ..utils.errors import handle_errors, SecurityError
import uuid
from pathlib import Path

# Configuration
@dataclass
class SecurityConfig:
    """Security configuration settings"""
    encryption_key: str
    enable_xss_protection: bool = True
    enable_csrf_protection: bool = True
    enable_ip_filtering: bool = True
    enable_rate_limiting: bool = True
    enable_request_validation: bool = True
    allowed_hosts: List[str] = None
    allowed_ips: List[str] = None
    blocked_ips: List[str] = None
    trusted_proxies: List[str] = None
    cors_origins: List[str] = None
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 30
    ssl_verify: bool = True

class TokenManager:
    """Handle JWT token operations"""
    def __init__(self, secret_key: str, token_ttl: int):
        self._secret_key = secret_key
        self._token_ttl = token_ttl
        self._blacklist: Dict[str, datetime] = {}
        self._refresh_tokens: Dict[str, Dict] = {}

    @handle_errors(logger=None)
    def create_access_token(self, data: Dict, expires_delta: Optional[int] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(seconds=expires_delta or self._token_ttl)
        to_encode.update({'exp': expire})
        return jwt.encode(to_encode, self._secret_key, algorithm='HS256')

    @handle_errors(logger=None)
    def create_refresh_token(self, user_id: str) -> str:
        token = str(uuid.uuid4())
        self._refresh_tokens[token] = {
            'user_id': user_id,
            'created': datetime.utcnow()
        }
        return token

    @handle_errors(logger=None)
    def verify_token(self, token: str, verify_exp: bool = True) -> Dict:
        try:
            if token in self._blacklist:
                self.logger.warning(f"Attempt to use blacklisted token: {token}")
                raise jwt.InvalidTokenError("Token is blacklisted")

            decoded_token = jwt.decode(token, self._secret_key, algorithms=['HS256'],
                                       options={'verify_exp': verify_exp})
            self.logger.info("Token verified successfully")
            return decoded_token

        except jwt.InvalidTokenError as e:
            self.logger.error(f"Token verification failed: {str(e)}")
            raise

    def blacklist_token(self, token: str) -> None:
        self._blacklist[token] = datetime.utcnow() + timedelta(seconds=self._token_ttl)

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        if refresh_token not in self._refresh_tokens:
            return None
        data = self._refresh_tokens[refresh_token]
        return self.create_access_token({'sub': data['user_id']})

class RequestValidator:
    """Handle request validation"""
    def __init__(self, config: SecurityConfig):
        self._config = config

    async def validate_host(self, request: Request) -> Optional[Response]:
        if not self._config.allowed_hosts:
            return None
        host = request.headers.get("host", "").split(":")[0]
        if host not in self._config.allowed_hosts:
            return Response(content=json.dumps({"error": "Invalid host"}),
                          status_code=400)
        return None

    async def validate_content_type(self, request: Request) -> Optional[Response]:
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data")):
                return Response(content=json.dumps({"error": "Invalid content type"}),
                              status_code=400)
        return None

    async def validate_content_length(self, request: Request) -> Optional[Response]:
        content_length = request.headers.get("content-length", 0)
        try:
            if int(content_length) > self._config.max_request_size:
                return Response(content=json.dumps({"error": "Request too large"}),
                              status_code=413)
        except ValueError:
            return Response(content=json.dumps({"error": "Invalid content length"}),
                          status_code=400)
        return None

class SecurityChecks:
    """Handle security checks and validations"""
    def __init__(self, config: SecurityConfig):
        self._config = config

    async def validate_xss(self, request: Request) -> Optional[Response]:
        if not self._config.enable_xss_protection:
            return None
        xss_patterns = [
            r"<script.*?>", r"javascript:", r"onload=",
            r"onerror=", r"onclick=", r"eval\(",
        ]
        url = str(request.url)
        for pattern in xss_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return Response(content=json.dumps({"error": "Potential XSS detected"}),
                              status_code=400)
        return None

    async def validate_sql_injection(self, request: Request) -> Optional[Response]:
        sql_patterns = [
            r"(\%27)|(\')", r"(\-\-)", r"(\/\*.*?\*\/)",
            r"(;.*?$)", r"(union.*?select)",
        ]
        url = str(request.url)
        for pattern in sql_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return Response(
                    content=json.dumps({"error": "Potential SQL injection detected"}),
                    status_code=400
                )
        return None

class SecurityManager(BaseComponent):
    """Main security manager coordinating all security operations"""
    def __init__(self, config: SecurityConfig):
        super().__init__()
        self._config = config
        self._token_manager = TokenManager(config.encryption_key, 3600)
        self._validator = RequestValidator(config)
        self._security_checks = SecurityChecks(config)
        self._fernet = Fernet(config.encryption_key.encode())
        self._redis = aioredis.from_url("redis://localhost")
        self._cleanup_task = asyncio.create_task(self._run_cleanup())

    async def validate_request(self, request: Request) -> Optional[Response]:
        """Validate incoming request"""
        try:
            if not self._config.enable_request_validation:
                return None

            # Run all validations
            validators = [
                self._validator.validate_host,
                self._validator.validate_content_type,
                self._validator.validate_content_length,
                self._security_checks.validate_xss,
                self._security_checks.validate_sql_injection
            ]

            for validator in validators:
                result = await validator(request)
                if result:
                    return result

            return None

        except Exception as e:
            self.logger.error(f"Request validation failed: {str(e)}")
            return Response(
                content=json.dumps({"error": "Security validation failed"}),
                status_code=400
            )

    async def encrypt_data(self, data: Union[str, bytes]) -> str:
        try:
            if isinstance(data, str):
                data = data.encode()
            return self._fernet.encrypt(data).decode()
        except Exception as e:
            self.logger.error(f"Data encryption failed: {str(e)}")
            raise

    async def decrypt_data(self, encrypted_data: str) -> str:
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            self.logger.error(f"Data decryption failed: {str(e)}")
            raise

    async def _run_cleanup(self) -> None:
        """Run periodic cleanup tasks"""
        while True:
            try:
                await self._token_manager._cleanup_expired_tokens()
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f"Cleanup task error: {str(e)}")
                await asyncio.sleep(60)

    async def cleanup(self) -> None:
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                await self._cleanup_task
            if self._redis:
                await self._redis.close()
            self.logger.info("Security resources cleaned up successfully")
        except asyncio.CancelledError:
            self.logger.info("Cleanup task cancelled successfully")
        except Exception as e:
            self.logger.error(f"Security cleanup failed: {str(e)}")
            raise 