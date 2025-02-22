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

@dataclass
class SecurityConfig:
    """Security configuration"""
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

class SecurityManager(BaseComponent):
    """Security and access control system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Security settings
        self._jwt_secret = config.get('security.jwt_secret') or self._generate_secret()
        self._token_expiry = config.get('security.token_expiry', 3600)  # 1 hour
        self._max_failed_attempts = config.get('security.max_attempts', 5)
        
        # Initialize encryption
        self._encryption_key = self._load_or_create_key()
        self._cipher = Fernet(self._encryption_key)
        
        # Access control
        self._roles = {
            'admin': ['all'],
            'operator': ['view', 'operate', 'alert'],
            'viewer': ['view']
        }
        
        # Session management
        self._active_sessions: Dict[str, Dict] = {}
        self._failed_attempts: Dict[str, int] = {}
        self._blocked_users: Dict[str, datetime] = {}
        
        # Audit logging
        self._audit_logger = logging.getLogger('security_audit')
        self._setup_audit_logging()
        
        # Statistics
        self._stats = {
            'active_sessions': 0,
            'blocked_users': 0,
            'failed_attempts': 0,
            'security_events': 0
        }
        
        # Rate limiting config
        self._rate_limit_interval = self.config.get(
            'security.rate_limit.interval',
            60
        )
        self._rate_limit_max_requests = self.config.get(
            'security.rate_limit.max_requests',
            100
        )
        self.logger = logging.getLogger('SecurityManager')
        self._redis: Optional[aioredis.Redis] = None
        self._security_config = SecurityConfig(**config.get('security', {}))
        self._fernet: Optional[Fernet] = None
        self._ip_cache: Dict[str, Dict] = {}
        self._request_validators: List[Callable] = []
        self._cleanup_task: Optional[asyncio.Task] = None
        self._setup_encryption()
        self._setup_validators()

    def _generate_secret(self) -> str:
        """Generate secure JWT secret"""
        return str(uuid.uuid4())

    def _load_or_create_key(self) -> bytes:
        """Load or create encryption key"""
        key_path = Path('data/security/encryption.key')
        key_path.parent.mkdir(parents=True, exist_ok=True)
        
        if key_path.exists():
            return key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            key_path.write_bytes(key)
            return key

    def _setup_audit_logging(self) -> None:
        """Setup security audit logging"""
        handler = logging.FileHandler('logs/security_audit.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self._audit_logger.addHandler(handler)
        self._audit_logger.setLevel(logging.INFO)

    async def initialize(self) -> None:
        """Initialize security manager"""
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    def _setup_encryption(self) -> None:
        """Setup encryption tools"""
        try:
            # Generate key from configuration
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'security_manager_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(
                kdf.derive(
                    self._security_config.encryption_key.encode()
                )
            )
            self._fernet = Fernet(key)
            
        except Exception as e:
            self.logger.error(f"Encryption setup failed: {str(e)}")
            raise

    def _setup_validators(self) -> None:
        """Setup request validators"""
        if self._security_config.enable_request_validation:
            self._request_validators.extend([
                self._validate_host,
                self._validate_ip,
                self._validate_content_type,
                self._validate_content_length,
                self._validate_xss,
                self._validate_sql_injection
            ])

    async def validate_request(self, request: Request) -> Optional[Response]:
        """Validate incoming request"""
        try:
            if not self._security_config.enable_request_validation:
                return None
                
            # Run all validators
            for validator in self._request_validators:
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
        """Encrypt sensitive data"""
        try:
            if isinstance(data, str):
                data = data.encode()
            return self._fernet.encrypt(data).decode()
        except Exception as e:
            self.logger.error(f"Data encryption failed: {str(e)}")
            raise

    async def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt encrypted data"""
        try:
            return self._fernet.decrypt(
                encrypted_data.encode()
            ).decode()
        except Exception as e:
            self.logger.error(f"Data decryption failed: {str(e)}")
            raise

    async def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token"""
        try:
            if not self._security_config.enable_csrf_protection:
                return ""
                
            token = secrets.token_urlsafe(32)
            await self._redis.setex(
                f"csrf:{session_id}",
                3600,  # 1 hour
                token
            )
            return token
            
        except Exception as e:
            self.logger.error(f"CSRF token generation failed: {str(e)}")
            raise

    async def validate_csrf_token(self,
                                session_id: str,
                                token: str) -> bool:
        """Validate CSRF token"""
        try:
            if not self._security_config.enable_csrf_protection:
                return True
                
            stored_token = await self._redis.get(f"csrf:{session_id}")
            return stored_token and stored_token.decode() == token
            
        except Exception as e:
            self.logger.error(f"CSRF validation failed: {str(e)}")
            return False

    async def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed"""
        try:
            if not self._security_config.enable_ip_filtering:
                return True
                
            # Check cache first
            if ip in self._ip_cache:
                cache_entry = self._ip_cache[ip]
                if cache_entry['expires'] > datetime.utcnow():
                    return cache_entry['allowed']
                    
            # Check blocked IPs
            if self._security_config.blocked_ips:
                if self._is_ip_in_list(ip, self._security_config.blocked_ips):
                    return False
                    
            # Check allowed IPs
            if self._security_config.allowed_ips:
                allowed = self._is_ip_in_list(
                    ip,
                    self._security_config.allowed_ips
                )
            else:
                allowed = True
                
            # Cache result
            self._ip_cache[ip] = {
                'allowed': allowed,
                'expires': datetime.utcnow() + timedelta(minutes=5)
            }
            
            return allowed
            
        except Exception as e:
            self.logger.error(f"IP validation failed: {str(e)}")
            return False

    async def cleanup(self) -> None:
        """Cleanup security resources"""
        self._failed_attempts.clear()
        self._blocked_users.clear()
        self._active_sessions.clear()
        self._rate_limits.clear()

    async def _validate_host(self, request: Request) -> Optional[Response]:
        """Validate request host"""
        if not self._security_config.allowed_hosts:
            return None
            
        host = request.headers.get("host", "").split(":")[0]
        if host not in self._security_config.allowed_hosts:
            return Response(
                content=json.dumps({"error": "Invalid host"}),
                status_code=400
            )
        return None

    async def _validate_ip(self, request: Request) -> Optional[Response]:
        """Validate request IP"""
        if not await self.is_ip_allowed(request.client.host):
            return Response(
                content=json.dumps({"error": "IP not allowed"}),
                status_code=403
            )
        return None

    async def _validate_content_type(self,
                                   request: Request) -> Optional[Response]:
        """Validate request content type"""
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data")):
                return Response(
                    content=json.dumps({"error": "Invalid content type"}),
                    status_code=400
                )
        return None

    async def _validate_content_length(self,
                                     request: Request) -> Optional[Response]:
        """Validate request content length"""
        content_length = request.headers.get("content-length", 0)
        try:
            if int(content_length) > self._security_config.max_request_size:
                return Response(
                    content=json.dumps({"error": "Request too large"}),
                    status_code=413
                )
        except ValueError:
            return Response(
                content=json.dumps({"error": "Invalid content length"}),
                status_code=400
            )
        return None

    async def _validate_xss(self, request: Request) -> Optional[Response]:
        """Validate request for XSS attempts"""
        if not self._security_config.enable_xss_protection:
            return None
            
        # Check headers and query params
        xss_patterns = [
            r"<script.*?>",
            r"javascript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"eval\(",
        ]
        
        # Check URL
        url = str(request.url)
        for pattern in xss_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return Response(
                    content=json.dumps({"error": "Potential XSS detected"}),
                    status_code=400
                )
                
        return None

    async def _validate_sql_injection(self,
                                    request: Request) -> Optional[Response]:
        """Validate request for SQL injection attempts"""
        sql_patterns = [
            r"(\%27)|(\')",  # Single quote
            r"(\-\-)",       # SQL comment
            r"(\/\*.*?\*\/)",  # Multi-line comment
            r"(;.*?$)",      # SQL command terminator
            r"(union.*?select)",  # UNION based SQL injection
        ]
        
        # Check URL and query params
        url = str(request.url)
        for pattern in sql_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return Response(
                    content=json.dumps(
                        {"error": "Potential SQL injection detected"}
                    ),
                    status_code=400
                )
                
        return None

    def _is_ip_in_list(self, ip: str, ip_list: List[str]) -> bool:
        """Check if IP is in list (supports CIDR notation)"""
        try:
            ip_addr = ipaddress.ip_address(ip)
            return any(
                ip_addr in ipaddress.ip_network(net)
                for net in ip_list
            )
        except ValueError:
            return False

    @handle_errors(logger=None)
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt(self._password_policy['min_length'])
        ).decode()

    @handle_errors(logger=None)
    def verify_password(self,
                       password: str,
                       hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode(),
            hashed.encode()
        )

    @handle_errors(logger=None)
    def create_access_token(self,
                          data: Dict,
                          expires_delta: Optional[int] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        # Set expiry
        expire = datetime.utcnow() + timedelta(
            seconds=expires_delta or self._token_ttl
        )
        to_encode.update({'exp': expire})
        
        # Create token
        return jwt.encode(
            to_encode,
            self._secret_key,
            algorithm='HS256'
        )

    @handle_errors(logger=None)
    def create_refresh_token(self,
                           user_id: str) -> str:
        """Create refresh token"""
        import uuid
        token = str(uuid.uuid4())
        
        self._refresh_tokens[token] = {
            'user_id': user_id,
            'created': datetime.utcnow()
        }
        
        return token

    @handle_errors(logger=None)
    def verify_token(self,
                    token: str,
                    verify_exp: bool = True) -> Dict:
        """Verify JWT token"""
        if token in self._blacklist:
            raise jwt.InvalidTokenError("Token is blacklisted")
            
        return jwt.decode(
            token,
            self._secret_key,
            algorithms=['HS256'],
            options={'verify_exp': verify_exp}
        )

    def blacklist_token(self, token: str) -> None:
        """Add token to blacklist"""
        self._blacklist[token] = datetime.utcnow() + timedelta(
            seconds=self._token_ttl
        )

    async def refresh_access_token(self,
                                 refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token"""
        if refresh_token not in self._refresh_tokens:
            return None
            
        data = self._refresh_tokens[refresh_token]
        return self.create_access_token({
            'sub': data['user_id']
        })

    @handle_errors(logger=None)
    async def check_rate_limit(self,
                             key: str) -> bool:
        """Check rate limit for key"""
        now = datetime.utcnow()
        
        # Remove old requests
        if key in self._rate_limits:
            self._rate_limits[key] = [
                ts for ts in self._rate_limits[key]
                if (now - ts).total_seconds() < self._rate_limit_interval
            ]
        else:
            self._rate_limits[key] = []
            
        # Check limit
        if len(self._rate_limits[key]) >= self._rate_limit_max_requests:
            return False
            
        # Add request
        self._rate_limits[key].append(now)
        return True

    async def _cleanup_task(self) -> None:
        """Cleanup expired data"""
        while True:
            try:
                now = datetime.utcnow()
                
                # Cleanup failed attempts
                for identifier in list(self._failed_attempts.keys()):
                    attempts = self._failed_attempts[identifier]
                    attempts = [
                        attempt for attempt in attempts
                        if (now - attempt).total_seconds() < self._lockout_time
                    ]
                    if attempts:
                        self._failed_attempts[identifier] = attempts
                    else:
                        del self._failed_attempts[identifier]
                        
                # Cleanup blacklist
                for token in list(self._blacklist.keys()):
                    if now > self._blacklist[token]:
                        del self._blacklist[token]
                        
                # Cleanup refresh tokens
                expired = []
                for token, data in self._refresh_tokens.items():
                    if (now - data['created']).days > 30:
                        expired.append(token)
                        
                for token in expired:
                    del self._refresh_tokens[token]
                    
                # Clean rate limits
                for key in list(self._rate_limits.keys()):
                    self._rate_limits[key] = [
                        ts for ts in self._rate_limits[key]
                        if (now - ts).total_seconds() < self._rate_limit_interval
                    ]
                    if not self._rate_limits[key]:
                        del self._rate_limits[key]
                        
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                self.logger.error(f"Security cleanup error: {str(e)}")
                await asyncio.sleep(60)

    @handle_errors(logger=None)
    async def generate_token(self,
                           data: Dict,
                           expires_in: Optional[int] = None) -> str:
        """Generate JWT token"""
        try:
            # Set expiration
            exp = datetime.utcnow() + timedelta(
                seconds=expires_in or self._token_ttl
            )
            
            # Prepare payload
            payload = data.copy()
            payload['exp'] = exp.timestamp()
            payload['iat'] = datetime.utcnow().timestamp()
            
            # Generate token
            token = jwt.encode(
                payload,
                self._secret_key,
                algorithm='HS256'
            )
            
            self._stats['tokens_issued'] += 1
            return token
            
        except Exception as e:
            self.logger.error(f"Token generation error: {str(e)}")
            raise

    @handle_errors(logger=None)
    async def verify_token(self, token: str) -> Dict:
        """Verify JWT token"""
        try:
            # Check blacklist
            if token in self._blacklist:
                raise ValueError("Token is blacklisted")
                
            # Verify token
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=['HS256']
            )
            
            self._stats['tokens_verified'] += 1
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            self.logger.error(f"Token verification error: {str(e)}")
            raise

    async def blacklist_token(self,
                            token: str,
                            ttl: Optional[int] = None) -> bool:
        """Blacklist JWT token"""
        try:
            # Add to blacklist
            self._blacklist[token] = datetime.utcnow() + timedelta(
                seconds=ttl or self._token_ttl
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Token blacklist error: {str(e)}")
            return False

    def validate_password(self, password: str) -> List[str]:
        """Validate password against policy"""
        errors = []
        
        # Check length
        if len(password) < self._password_policy['min_length']:
            errors.append(
                f"Password must be at least "
                f"{self._password_policy['min_length']} characters long"
            )
            
        # Check uppercase
        if self._password_policy['require_upper']:
            if not any(c.isupper() for c in password):
                errors.append(
                    "Password must contain at least "
                    "one uppercase letter"
                )
                
        # Check lowercase
        if self._password_policy['require_lower']:
            if not any(c.islower() for c in password):
                errors.append(
                    "Password must contain at least "
                    "one lowercase letter"
                )
                
        # Check digits
        if self._password_policy['require_digit']:
            if not any(c.isdigit() for c in password):
                errors.append(
                    "Password must contain at least "
                    "one digit"
                )
                
        # Check special characters
        if self._password_policy['require_special']:
            special = '!@#$%^&*()_+-=[]{}|;:,.<>?'
            if not any(c in special for c in password):
                errors.append(
                    "Password must contain at least "
                    "one special character"
                )
                
        return errors

    async def check_attempts(self,
                           identifier: str) -> bool:
        """Check failed login attempts"""
        try:
            # Get attempts
            attempts = self._failed_attempts.get(identifier, [])
            
            # Remove expired attempts
            now = datetime.utcnow()
            attempts = [
                attempt for attempt in attempts
                if (now - attempt).total_seconds() < self._lockout_time
            ]
            
            # Check attempts count
            if len(attempts) >= self._max_attempts:
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Attempts check error: {str(e)}")
            return True

    async def record_attempt(self,
                           identifier: str,
                           success: bool) -> None:
        """Record login attempt"""
        try:
            if not success:
                # Add attempt
                if identifier not in self._failed_attempts:
                    self._failed_attempts[identifier] = []
                    
                self._failed_attempts[identifier].append(
                    datetime.utcnow()
                )
                self._stats['failed_attempts'] += 1
                
            else:
                # Clear attempts
                self._failed_attempts.pop(identifier, None)
                
        except Exception as e:
            self.logger.error(f"Attempt recording error: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return self._stats.copy()

    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return token"""
        try:
            # Check if user is blocked
            if self._is_user_blocked(username):
                self._audit_log('auth_blocked', username)
                raise SecurityError("Account temporarily blocked")
            
            # Verify credentials
            user = await self.app.storage.get_user(username)
            if not user:
                self._handle_failed_attempt(username)
                return None
            
            # Check password
            if not self._verify_password(password, user['password']):
                self._handle_failed_attempt(username)
                return None
            
            # Generate token
            token = self._generate_token(user)
            
            # Create session
            session_id = str(uuid.uuid4())
            self._active_sessions[session_id] = {
                'user': username,
                'roles': user['roles'],
                'created': datetime.utcnow(),
                'expires': datetime.utcnow() + timedelta(seconds=self._token_expiry)
            }
            
            # Update stats
            self._stats['active_sessions'] = len(self._active_sessions)
            
            # Clear failed attempts
            self._failed_attempts.pop(username, None)
            self._blocked_users.pop(username, None)
            
            self._audit_log('auth_success', username)
            return token
            
        except Exception as e:
            self._audit_log('auth_error', username, str(e))
            raise SecurityError(f"Authentication failed: {str(e)}")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception:
            return False

    def _generate_token(self, user: Dict) -> str:
        """Generate JWT token"""
        payload = {
            'sub': user['username'],
            'roles': user['roles'],
            'exp': datetime.utcnow() + timedelta(seconds=self._token_expiry)
        }
        return jwt.encode(payload, self._jwt_secret, algorithm='HS256')

    def _is_user_blocked(self, username: str) -> bool:
        """Check if user is blocked"""
        if username in self._blocked_users:
            block_time = self._blocked_users[username]
            if datetime.utcnow() < block_time:
                return True
            else:
                self._blocked_users.pop(username)
        return False

    def _handle_failed_attempt(self, username: str) -> None:
        """Handle failed authentication attempt"""
        self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1
        self._stats['failed_attempts'] += 1
        
        if self._failed_attempts[username] >= self._max_failed_attempts:
            # Block user for 15 minutes
            self._blocked_users[username] = datetime.utcnow() + timedelta(minutes=15)
            self._stats['blocked_users'] = len(self._blocked_users)
            self._audit_log('user_blocked', username)

    def _audit_log(self,
                  event_type: str,
                  username: str,
                  details: str = None) -> None:
        """Log security audit event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event_type,
            'user': username,
            'details': details
        }
        self._audit_logger.info(event)
        self._stats['security_events'] += 1

    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=['HS256']
            )
            
            # Check if session is active
            session = self._find_session(payload['sub'])
            if not session:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self._audit_log('token_expired', payload.get('sub', 'unknown'))
            return None
        except Exception:
            return None

    def _find_session(self, username: str) -> Optional[Dict]:
        """Find active session for user"""
        for session in self._active_sessions.values():
            if session['user'] == username and session['expires'] > datetime.utcnow():
                return session
        return None

    async def check_permission(self,
                             token: str,
                             required_permission: str) -> bool:
        """Check if token has required permission"""
        try:
            payload = await self.verify_token(token)
            if not payload:
                return False
            
            roles = payload.get('roles', [])
            
            # Check each role's permissions
            for role in roles:
                if role == 'admin' or \
                   required_permission in self._roles.get(role, []):
                    return True
            
            return False
            
        except Exception:
            return False

    async def cleanup_sessions(self) -> None:
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self._active_sessions.items()
            if session['expires'] <= now
        ]
        
        for sid in expired:
            self._active_sessions.pop(sid)
        
        self._stats['active_sessions'] = len(self._active_sessions)

    async def get_stats(self) -> Dict:
        """Get security statistics"""
        return self._stats.copy() 