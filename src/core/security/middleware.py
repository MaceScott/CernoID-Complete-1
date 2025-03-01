from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List, Dict, Callable, Any
import time
from core.auth.manager import AuthManager
from ..base import BaseComponent
from ..utils.errors import SecurityError, handle_errors
from .crypto import CryptoManager
import re
import ipaddress
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for FastAPI"""
    
    def __init__(self,
                 app: Any,
                 security: BaseComponent):
        super().__init__(app)
        self.security = security
        self.config = security.config
        self.logger = security.logger
        
        # Load config
        self._exclude_paths = self.config.get(
            'security.exclude_paths',
            []
        )
        self._rate_limit_paths = self.config.get(
            'security.rate_limit_paths',
            ['*']
        )
        self.auth_manager = AuthManager(self.config)
        self._rate_limits: Dict[str, List[float]] = {}
        self._crypto = CryptoManager(self.config)
        self._trusted_proxies = self.config.get('security.trusted_proxies', [])
        self._allowed_hosts = self.config.get('security.allowed_hosts', [])
        self._allowed_ips = self.config.get('security.allowed_ips', [])
        self._blocked_ips = self.config.get('security.blocked_ips', [])
        self._xss_protection = self.config.get('security.xss_protection', True)
        self._sql_protection = self.config.get('security.sql_protection', True)
        self._max_body_size = self.config.get('security.max_body_size', 10 * 1024 * 1024)
        self._validators: Dict[str, Callable] = {}
        self._public_paths = self.config.get('security.public_paths', [])
        self._token_header = self.config.get('security.token_header', 'Authorization')
        self._token_type = self.config.get('security.token_type', 'Bearer')

    async def initialize(self) -> None:
        """Initialize security middleware"""
        try:
            await self._crypto.initialize()
            self._setup_validators()
            self.logger.info("Security middleware initialized successfully")
        except Exception as e:
            self.logger.error(f"Security middleware initialization failed: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup security middleware"""
        try:
            await self._crypto.cleanup()
            self.logger.info("Security middleware cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Security middleware cleanup failed: {str(e)}")
            raise

    async def dispatch(self,
                      request: Request,
                      call_next: Callable) -> Response:
        """Process request"""
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        try:
            if self._should_rate_limit(request.url.path):
                key = self._get_rate_limit_key(request)
                if not await self.security.check_rate_limit(key):
                    self.logger.warning(f"Rate limit exceeded for key: {key}")
                    return JSONResponse(
                        status_code=429,
                        content={'detail': 'Too many requests'}
                    )

            token = self._get_token(request)
            if token:
                try:
                    payload = self.security.verify_token(token)
                    request.state.user = payload
                except jwt.InvalidTokenError as e:
                    self.logger.warning(f"Invalid token error: {str(e)}")
                    return JSONResponse(
                        status_code=401,
                        content={'detail': str(e)}
                    )

            response = await call_next(request)
            self._add_security_headers(response)

            self.logger.info(f"Request processed successfully: {request.url.path}")
            return response

        except Exception as e:
            self.logger.error(f"Security middleware error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={'detail': 'Internal server error'}
            )

    def _get_token(self, request: Request) -> Optional[str]:
        """Get token from request"""
        auth = request.headers.get('Authorization')
        if not auth:
            return None
            
        parts = auth.split()
        if parts[0].lower() != 'bearer':
            return None
            
        if len(parts) < 2:
            return None
            
        return parts[1]

    def _get_rate_limit_key(self, request: Request) -> str:
        """Get rate limit key for request"""
        # Use IP address and path
        ip = request.client.host
        path = request.url.path
        return f"{ip}:{path}"

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from security"""
        return any(
            path.startswith(prefix)
            for prefix in self._exclude_paths
        )

    def _should_rate_limit(self, path: str) -> bool:
        """Check if path should be rate limited"""
        if '*' in self._rate_limit_paths:
            return True
            
        return any(
            path.startswith(prefix)
            for prefix in self._rate_limit_paths
        )

    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response"""
        # HSTS
        if self.config.get('security.hsts', True):
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )
            
        # XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Type Options
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Frame Options
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Content Security Policy
        csp = self.config.get('security.csp')
        if csp:
            response.headers['Content-Security-Policy'] = csp

    async def authenticate_request(self, request: Request) -> Optional[Dict]:
        """Authenticate incoming request"""
        try:
            # Check authentication token
            token = await oauth2_scheme(request)
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
                
            # Verify token
            payload = self.auth_manager.verify_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
                
            return payload
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )

    async def check_permissions(self, request: Request, required_permissions: List[str]):
        """Check user permissions"""
        payload = await self.authenticate_request(request)
        user_permissions = payload.get("permissions", [])
        
        if not all(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

    async def rate_limit(self, request: Request):
        """Apply rate limiting"""
        if not self.config['security']['rate_limiting']['enabled']:
            return

        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self._rate_limits[client_ip] = [
            t for t in self._rate_limits.get(client_ip, [])
            if current_time - t < self.config['security']['rate_limiting']['period']
        ]
        
        # Check rate limit
        if len(self._rate_limits[client_ip]) >= self.config['security']['rate_limiting']['rate']:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
            
        # Add current request
        self._rate_limits[client_ip].append(current_time)

    async def process_request(self, request: Request) -> Optional[Response]:
        """Process and validate incoming request"""
        try:
            # Run all validators
            for validator in self._validators.values():
                result = await validator(request)
                if result:
                    return result
                    
            return None
            
        except Exception as e:
            raise SecurityError(f"Request validation failed: {str(e)}")

    def _setup_validators(self) -> None:
        """Setup request validators"""
        self._validators = {
            'ip': self._validate_ip,
            'host': self._validate_host,
            'size': self._validate_size,
            'xss': self._validate_xss,
            'sql': self._validate_sql,
            'content': self._validate_content_type
        }

    @handle_errors(logger=None)
    async def _validate_ip(self, request: Request) -> Optional[Response]:
        """Validate client IP address"""
        ip = self._get_client_ip(request)
        
        # Check blocked IPs
        if self._is_ip_blocked(ip):
            return Response(
                content="Access denied",
                status_code=403
            )
            
        # Check allowed IPs if configured
        if self._allowed_ips and not self._is_ip_allowed(ip):
            return Response(
                content="Access denied",
                status_code=403
            )
            
        return None

    @handle_errors(logger=None)
    async def _validate_host(self, request: Request) -> Optional[Response]:
        """Validate request host"""
        if not self._allowed_hosts:
            return None
            
        host = request.headers.get('host', '').split(':')[0]
        if host not in self._allowed_hosts:
            return Response(
                content="Invalid host",
                status_code=400
            )
            
        return None

    @handle_errors(logger=None)
    async def _validate_size(self, request: Request) -> Optional[Response]:
        """Validate request body size"""
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > self._max_body_size:
            return Response(
                content="Request too large",
                status_code=413
            )
            
        return None

    @handle_errors(logger=None)
    async def _validate_xss(self, request: Request) -> Optional[Response]:
        """Validate request for XSS attempts"""
        if not self._xss_protection:
            return None
            
        # Check headers and query params
        xss_patterns = [
            r"<script.*?>",
            r"javascript:",
            r"on\w+\s*=",
            r"eval\(",
        ]
        
        # Check URL and query parameters
        url = str(request.url)
        for pattern in xss_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return Response(
                    content="Invalid request",
                    status_code=400
                )
                
        return None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        if self._trusted_proxies:
            forwarded = request.headers.get('x-forwarded-for')
            if forwarded:
                ips = [ip.strip() for ip in forwarded.split(',')]
                for ip in reversed(ips):
                    if not self._is_proxy(ip):
                        return ip
                        
        return request.client.host

    def _is_proxy(self, ip: str) -> bool:
        """Check if IP is a trusted proxy"""
        return any(
            ipaddress.ip_address(ip) in ipaddress.ip_network(proxy)
            for proxy in self._trusted_proxies
        )

    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return any(
            ipaddress.ip_address(ip) in ipaddress.ip_network(blocked)
            for blocked in self._blocked_ips
        )

    def _is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed"""
        return any(
            ipaddress.ip_address(ip) in ipaddress.ip_network(allowed)
            for allowed in self._allowed_ips
        )

    async def process_request_with_all_checks(self, request: Request):
        """Process incoming request with all security checks"""
        # Apply rate limiting
        await self.rate_limit(request)
        
        # Authenticate request
        payload = await self.authenticate_request(request)
        
        # Add security headers
        request.state.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        }
        
        return payload

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public"""
        return any(
            path.startswith(public_path)
            for public_path in self._public_paths
        )

    def _unauthorized(self, message: str) -> Any:
        """Create unauthorized response"""
        return {
            'status': 401,
            'error': 'Unauthorized',
            'message': message
        } 