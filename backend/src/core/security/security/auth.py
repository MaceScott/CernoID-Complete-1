from typing import Dict, Optional, Any, List, Union
import jwt
import bcrypt
from datetime import datetime, timedelta
import uuid
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from ..base import BaseComponent
from ..utils.errors import handle_errors
from ...utils.config import get_settings
from ...utils.logging import get_logger
from ..database.service import DatabaseService
from ..interfaces.security import AuditInterface

class User(BaseModel):
    """User model with role-based permissions."""
    id: int
    email: str
    username: Optional[str]  # Make username optional
    role: str
    permissions: List[str]
    is_active: bool
    last_login: Optional[datetime]

class AuthService:
    """Advanced authentication service with RBAC"""
    
    def __init__(self, audit: AuditInterface):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.db = DatabaseService()
        self.audit = audit
        
        # Initialize security tools
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto"
        )
        self.oauth2_scheme = OAuth2PasswordBearer(
            tokenUrl="auth/login"
        )
        
        # Initialize JWT settings
        self.jwt_secret = self.settings.jwt_secret
        self.jwt_algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=30)
        self.refresh_token_expire = timedelta(days=7)
        
    async def authenticate_user(self,
                              email: str,  # Changed from username to email
                              password: str
                              ) -> Optional[User]:
        """
        Authenticate user using email and password.
        
        Args:
            email: User's email address
            password: Plain text password to verify
            
        Returns:
            Optional[User]: Authenticated user or None if authentication fails
            
        Raises:
            Exception: If database operation fails
        """
        try:
            # Get user from database by email
            user_data = await self.db.get_user_by_email(email)
            if not user_data:
                # Log failed attempt - user not found
                await self.audit.log_event(
                    event_type="authentication",
                    resource="auth",
                    action="login_failed",
                    details={
                        "email": email,
                        "reason": "user_not_found"
                    }
                )
                return None
                
            # Verify password against hashed_password
            if not self.verify_password(password, user_data["hashed_password"]):
                # Log failed attempt - invalid password
                await self.audit.log_event(
                    event_type="authentication",
                    user_id=user_data["id"],
                    resource="auth",
                    action="login_failed",
                    details={
                        "email": email,
                        "reason": "invalid_password"
                    }
                )
                return None
                
            # Update last login
            await self.db.update_last_login(user_data["id"])
            
            # Create user object
            user = User(**user_data)
            
            # Log successful authentication
            await self.audit.log_event(
                event_type="authentication",
                user_id=user.id,
                resource="auth",
                action="login_success",
                details={"email": email}
            )
            
            return user
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise
            
    def verify_password(self,
                       plain_password: str,
                       hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            self.logger.error(f"Password verification failed: {str(e)}")
            return False
        
    def create_password_hash(self, password: str) -> str:
        """Create password hash."""
        return self.pwd_context.hash(password)
        
    async def create_tokens(self,
                          user: User
                          ) -> Dict[str, str]:
        """Create access and refresh tokens."""
        try:
            # Create access token
            access_token_data = {
                "sub": str(user.id),
                "email": user.email,  # Changed from username to email
                "role": user.role,
                "permissions": user.permissions,
                "type": "access",
                "exp": datetime.utcnow() + self.access_token_expire
            }
            
            access_token = jwt.encode(
                access_token_data,
                self.jwt_secret,
                algorithm=self.jwt_algorithm
            )
            
            # Create refresh token
            refresh_token_data = {
                "sub": str(user.id),
                "type": "refresh",
                "exp": datetime.utcnow() + self.refresh_token_expire
            }
            
            refresh_token = jwt.encode(
                refresh_token_data,
                self.jwt_secret,
                algorithm=self.jwt_algorithm
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            self.logger.error(f"Token creation failed: {str(e)}")
            raise
            
    async def verify_token(self,
                          token: str,
                          token_type: str = "access"
                          ) -> Dict[str, Any]:
        """Verify JWT token."""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
    async def refresh_access_token(self,
                                 refresh_token: str
                                 ) -> Dict[str, str]:
        """Refresh access token using refresh token."""
        try:
            # Verify refresh token
            payload = await self.verify_token(refresh_token, "refresh")
            
            # Get user
            user_data = await self.db.get_user_by_id(int(payload["sub"]))
            user = User(**user_data)
            
            # Create new access token
            access_token_data = {
                "sub": str(user.id),
                "email": user.email,  # Changed from username to email
                "role": user.role,
                "permissions": user.permissions,
                "type": "access",
                "exp": datetime.utcnow() + self.access_token_expire
            }
            
            access_token = jwt.encode(
                access_token_data,
                self.jwt_secret,
                algorithm=self.jwt_algorithm
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            self.logger.error(f"Token refresh failed: {str(e)}")
            raise
            
    async def check_permission(self,
                             user: User,
                             required_permission: str) -> bool:
        """Check if user has required permission."""
        return required_permission in user.permissions
        
    async def get_current_user(self,
                             token: str = Depends(oauth2_scheme)
                             ) -> User:
        """Get current user from token."""
        try:
            # Verify token
            payload = await self.verify_token(token)
            
            # Get user
            user_data = await self.db.get_user_by_id(int(payload["sub"]))
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
                
            return User(**user_data)
            
        except Exception as e:
            self.logger.error(f"Get current user failed: {str(e)}")
            raise

# Global auth service instance
auth_service = AuthService()

class AuthManager(BaseComponent):
    """Authentication and authorization management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._secret_key = self.config.get('auth.secret_key', str(uuid.uuid4()))
        self._token_expire = self.config.get('auth.token_expire', 3600)
        self._refresh_expire = self.config.get('auth.refresh_expire', 86400)
        self._algorithm = self.config.get('auth.algorithm', 'HS256')
        self._token_type = self.config.get('auth.token_type', 'Bearer')
        self._sessions: Dict[str, Dict] = {}
        self._blacklist: List[str] = []

    async def initialize(self) -> None:
        """Initialize auth manager"""
        # Load blacklisted tokens
        await self._load_blacklist()
        
        # Start cleanup task
        self.add_cleanup_task(
            asyncio.create_task(self._cleanup_sessions())
        )

    async def cleanup(self) -> None:
        """Cleanup auth resources"""
        self._sessions.clear()
        self._blacklist.clear()

    @handle_errors(logger=None)
    async def authenticate(self,
                         username: str,
                         password: str) -> Dict[str, str]:
        """Authenticate user and generate tokens"""
        # Get user from database
        db = self.app.get_component('database')
        user = await db.fetch_one(
            "SELECT * FROM users WHERE username = $1",
            username
        )
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
            
        # Verify password
        if not self._verify_password(password, user['password']):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
            
        # Generate tokens
        access_token = self._create_token(
            {'sub': str(user['id'])},
            expires_delta=timedelta(seconds=self._token_expire)
        )
        
        refresh_token = self._create_token(
            {'sub': str(user['id']), 'type': 'refresh'},
            expires_delta=timedelta(seconds=self._refresh_expire)
        )
        
        # Store session
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            'user_id': str(user['id']),
            'refresh_token': refresh_token,
            'created': datetime.utcnow().isoformat(),
            'expires': (
                datetime.utcnow() + 
                timedelta(seconds=self._refresh_expire)
            ).isoformat()
        }
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': self._token_type
        }

    @handle_errors(logger=None)
    async def refresh_token(self,
                          refresh_token: str) -> Dict[str, str]:
        """Refresh access token"""
        # Verify refresh token
        try:
            payload = jwt.decode(
                refresh_token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
            
        # Check token type
        if payload.get('type') != 'refresh':
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )
            
        # Check if token is blacklisted
        if refresh_token in self._blacklist:
            raise HTTPException(
                status_code=401,
                detail="Token has been revoked"
            )
            
        # Generate new access token
        access_token = self._create_token(
            {'sub': payload['sub']},
            expires_delta=timedelta(seconds=self._token_expire)
        )
        
        return {
            'access_token': access_token,
            'token_type': self._token_type
        }

    @handle_errors(logger=None)
    async def validate_token(self,
                           token: str) -> Dict:
        """Validate access token"""
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
            
        # Check if token is blacklisted
        if token in self._blacklist:
            raise HTTPException(
                status_code=401,
                detail="Token has been revoked"
            )
            
        return payload

    async def revoke_token(self, token: str) -> None:
        """Revoke token by adding to blacklist"""
        if token not in self._blacklist:
            self._blacklist.append(token)
            await self._save_blacklist()

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(
            password.encode(),
            salt
        ).decode()

    def _verify_password(self,
                        plain_password: str,
                        hashed_password: str) -> bool:
        """Verify password hash"""
        return bcrypt.checkpw(
            plain_password.encode(),
            hashed_password.encode()
        )

    def _create_token(self,
                     data: Dict,
                     expires_delta: timedelta) -> str:
        """Create JWT token"""
        payload = data.copy()
        expire = datetime.utcnow() + expires_delta
        payload.update({
            'exp': expire,
            'iat': datetime.utcnow()
        })
        
        return jwt.encode(
            payload,
            self._secret_key,
            algorithm=self._algorithm
        )

    async def _load_blacklist(self) -> None:
        """Load blacklisted tokens from storage"""
        try:
            db = self.app.get_component('database')
            records = await db.fetch_all(
                "SELECT token FROM blacklisted_tokens"
            )
            self._blacklist = [r['token'] for r in records]
        except Exception as e:
            self.logger.error(f"Failed to load blacklist: {str(e)}")

    async def _save_blacklist(self) -> None:
        """Save blacklisted tokens to storage"""
        try:
            db = self.app.get_component('database')
            await db.execute(
                "DELETE FROM blacklisted_tokens"
            )
            if self._blacklist:
                await db.execute_many(
                    "INSERT INTO blacklisted_tokens (token) VALUES ($1)",
                    [(token,) for token in self._blacklist]
                )
        except Exception as e:
            self.logger.error(f"Failed to save blacklist: {str(e)}")

    async def _cleanup_sessions(self) -> None:
        """Cleanup expired sessions"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                now = datetime.utcnow()
                expired = []
                
                for session_id, session in self._sessions.items():
                    expires = datetime.fromisoformat(session['expires'])
                    if expires < now:
                        expired.append(session_id)
                        await self.revoke_token(session['refresh_token'])
                        
                for session_id in expired:
                    del self._sessions[session_id]
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Session cleanup failed: {str(e)}")
                await asyncio.sleep(60) 