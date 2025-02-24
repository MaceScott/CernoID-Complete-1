"""
Security headers middleware with CSP and other protections.
"""
from fastapi import Request, Response
from typing import Dict, Optional
import uuid
from datetime import datetime
import json

from ...utils.config import get_settings
from ...utils.logging import get_logger
from ...core.security.audit import audit_logger

class SecurityHeaders:
    """
    Advanced security headers middleware
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize CSP directives
        self.csp_directives = self._init_csp_directives()
        
    def _init_csp_directives(self) -> Dict[str, str]:
        """Initialize Content Security Policy directives."""
        return {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: https:",
            "font-src": "'self'",
            "connect-src": "'self'",
            "media-src": "'self'",
            "object-src": "'none'",
            "frame-src": "'self'",
            "frame-ancestors": "'self'",
            "form-action": "'self'",
            "base-uri": "'self'",
            "upgrade-insecure-requests": ""
        }
        
    async def __call__(self,
                      request: Request,
                      call_next) -> Response:
        """Apply security headers to response."""
        try:
            # Generate request ID
            request_id = str(uuid.uuid4())
            
            # Add request ID to request state
            request.state.request_id = request_id
            
            # Get response
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-Request-ID"] = request_id
            
            # Add Content Security Policy
            response.headers["Content-Security-Policy"] = self._build_csp()
            
            # Add Feature Policy
            response.headers["Permissions-Policy"] = (
                "camera=self, microphone=self, geolocation=self"
            )
            
            # Add HSTS
            if not self.settings.debug:
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains; preload"
                )
                
            # Log security event
            await self._log_security_event(request, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Security headers error: {str(e)}")
            raise
            
    def _build_csp(self) -> str:
        """Build Content Security Policy header value."""
        directives = []
        
        for directive, value in self.csp_directives.items():
            if value:
                directives.append(f"{directive} {value}")
            else:
                directives.append(directive)
                
        return "; ".join(directives)
        
    async def _log_security_event(self,
                                request: Request,
                                response: Response):
        """Log security-related event."""
        try:
            event_details = {
                "request_id": request.state.request_id,
                "method": request.method,
                "path": str(request.url),
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
            
            await audit_logger.log_event(
                event_type="security",
                user_id=getattr(request.state, "user_id", None),
                resource="http",
                action="request",
                details=event_details
            )
            
        except Exception as e:
            self.logger.error(f"Security event logging failed: {str(e)}")

# Global security headers middleware instance
security_headers = SecurityHeaders() 