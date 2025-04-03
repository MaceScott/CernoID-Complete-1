from typing import Optional
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..utils.rate_limit import check_rate_limit
from ..utils.session import session_manager
from ..utils.csrf import csrf_protection
from ..logging.config import LogConfig

logger = LogConfig().get_logger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        require_csrf: bool = True,
        require_session: bool = True,
        rate_limit: bool = True,
        exclude_paths: Optional[list] = None
    ):
        """
        Initialize security middleware.
        
        Args:
            app: FastAPI application
            require_csrf: Whether to require CSRF tokens
            require_session: Whether to require valid sessions
            rate_limit: Whether to apply rate limiting
            exclude_paths: Paths to exclude from security checks
        """
        super().__init__(app)
        self.require_csrf = require_csrf
        self.require_session = require_session
        self.rate_limit = rate_limit
        self.exclude_paths = exclude_paths or []
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request through security middleware.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/route handler
            
        Returns:
            Response: Processed response
        """
        try:
            # Skip security checks for excluded paths
            if request.url.path in self.exclude_paths:
                return await call_next(request)
                
            # Get client IP
            ip = request.client.host if request.client else "unknown"
            
            # Apply rate limiting
            if self.rate_limit:
                check_rate_limit(ip)
                
            # Get session token from cookie
            session_token = request.cookies.get("session_token")
            
            # Validate session if required
            if self.require_session and session_token:
                if not session_manager.validate_session(session_token, ip):
                    session_token = None
                    
            # Get user ID from session
            user_id = None
            if session_token and session_token in session_manager.sessions:
                user_id = session_manager.sessions[session_token]["user_id"]
                
            # Verify CSRF token for non-GET requests
            if (
                self.require_csrf
                and request.method != "GET"
                and user_id
            ):
                csrf_protection.verify_csrf_token(request, user_id)
                
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:;"
            )
            
            # Add CSRF token to response if user is authenticated
            if user_id:
                csrf_token = csrf_protection.generate_token(user_id)
                response.set_cookie(
                    "csrf_token",
                    csrf_token,
                    httponly=True,
                    secure=True,
                    samesite="Strict"
                )
                
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            raise 