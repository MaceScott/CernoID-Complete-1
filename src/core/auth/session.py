from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json
import aioredis
import secrets
from fastapi import Request, Response
from user_agents import parse

@dataclass
class SessionConfig:
    """Session configuration"""
    session_timeout: int = 3600  # 1 hour
    session_refresh: bool = True
    cookie_name: str = "session_id"
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "Lax"
    max_sessions_per_user: int = 5
    enable_device_tracking: bool = True
    enable_geo_tracking: bool = True

class SessionHandler:
    """Session management system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('SessionHandler')
        self._redis: Optional[aioredis.Redis] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._session_config = SessionConfig(**config.get('session', {}))
        self._active_sessions: Dict[str, Dict] = {}

    async def initialize(self) -> None:
        """Initialize session handler"""
        try:
            # Connect to Redis
            self._redis = await aioredis.create_redis_pool(
                self.config['redis_url']
            )
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(
                self._cleanup_expired_sessions()
            )
            
            self.logger.info("Session handler initialized")
            
        except Exception as e:
            self.logger.error(f"Session handler initialization failed: {str(e)}")
            raise

    async def create_session(self,
                           user_id: str,
                           request: Request) -> str:
        """Create new session"""
        try:
            # Generate session ID
            session_id = secrets.token_urlsafe(32)
            
            # Get device and location info
            device_info = self._get_device_info(request)
            geo_info = await self._get_geo_info(request) \
                if self._session_config.enable_geo_tracking else {}
            
            # Create session data
            session_data = {
                "user_id": user_id,
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat(),
                "expires_at": (
                    datetime.utcnow() + 
                    timedelta(seconds=self._session_config.session_timeout)
                ).isoformat(),
                "ip_address": request.client.host,
                "user_agent": str(request.headers.get("user-agent")),
                "device_info": device_info,
                "geo_info": geo_info
            }
            
            # Store in Redis
            await self._redis.setex(
                f"session:{session_id}",
                self._session_config.session_timeout,
                json.dumps(session_data)
            )
            
            # Update user's active sessions
            await self._update_user_sessions(user_id, session_id)
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Session creation failed: {str(e)}")
            raise

    async def get_session(self,
                         session_id: str) -> Optional[Dict]:
        """Get session data"""
        try:
            session_data = await self._redis.get(f"session:{session_id}")
            if not session_data:
                return None
                
            session = json.loads(session_data)
            
            # Check expiration
            if datetime.fromisoformat(session["expires_at"]) < datetime.utcnow():
                await self.destroy_session(session_id)
                return None
                
            # Refresh session if enabled
            if self._session_config.session_refresh:
                await self._refresh_session(session_id, session)
                
            return session
            
        except Exception as e:
            self.logger.error(f"Session retrieval failed: {str(e)}")
            return None

    async def update_session(self,
                           session_id: str,
                           data: Dict) -> bool:
        """Update session data"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
                
            # Update session data
            session.update(data)
            session["last_active"] = datetime.utcnow().isoformat()
            
            # Store updated session
            await self._redis.setex(
                f"session:{session_id}",
                self._session_config.session_timeout,
                json.dumps(session)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Session update failed: {str(e)}")
            return False

    async def destroy_session(self, session_id: str) -> bool:
        """Destroy session"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
                
            # Remove from Redis
            await self._redis.delete(f"session:{session_id}")
            
            # Update user's active sessions
            await self._remove_user_session(
                session["user_id"],
                session_id
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Session destruction failed: {str(e)}")
            return False

    async def cleanup(self) -> None:
        """Cleanup session handler resources"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                
            if self._redis:
                self._redis.close()
                await self._redis.wait_closed()
                
            self.logger.info("Session handler cleaned up")
            
        except Exception as e:
            self.logger.error(f"Session cleanup failed: {str(e)}")

    def _get_device_info(self, request: Request) -> Dict:
        """Get device information from request"""
        if not self._session_config.enable_device_tracking:
            return {}
            
        user_agent_string = request.headers.get("user-agent", "")
        user_agent = parse(user_agent_string)
        
        return {
            "browser": user_agent.browser.family,
            "browser_version": user_agent.browser.version_string,
            "os": user_agent.os.family,
            "os_version": user_agent.os.version_string,
            "device": user_agent.device.family,
            "is_mobile": user_agent.is_mobile,
            "is_tablet": user_agent.is_tablet,
            "is_pc": user_agent.is_pc
        }

    async def _get_geo_info(self, request: Request) -> Dict:
        """Get geolocation information from request"""
        # This is a placeholder - implement actual geo lookup
        return {
            "country": "Unknown",
            "city": "Unknown",
            "timezone": "UTC"
        }

    async def _update_user_sessions(self,
                                  user_id: str,
                                  session_id: str) -> None:
        """Update user's active sessions"""
        user_sessions = await self._redis.get(f"user_sessions:{user_id}")
        sessions = json.loads(user_sessions) if user_sessions else []
        
        # Add new session
        sessions.append(session_id)
        
        # Enforce max sessions limit
        if len(sessions) > self._session_config.max_sessions_per_user:
            oldest_session = sessions.pop(0)
            await self.destroy_session(oldest_session)
            
        await self._redis.set(
            f"user_sessions:{user_id}",
            json.dumps(sessions)
        )

    async def _remove_user_session(self,
                                 user_id: str,
                                 session_id: str) -> None:
        """Remove session from user's active sessions"""
        user_sessions = await self._redis.get(f"user_sessions:{user_id}")
        if user_sessions:
            sessions = json.loads(user_sessions)
            sessions.remove(session_id)
            await self._redis.set(
                f"user_sessions:{user_id}",
                json.dumps(sessions)
            )

    async def _refresh_session(self,
                             session_id: str,
                             session: Dict) -> None:
        """Refresh session expiration"""
        session["last_active"] = datetime.utcnow().isoformat()
        session["expires_at"] = (
            datetime.utcnow() + 
            timedelta(seconds=self._session_config.session_timeout)
        ).isoformat()
        
        await self._redis.setex(
            f"session:{session_id}",
            self._session_config.session_timeout,
            json.dumps(session)
        )

    async def _cleanup_expired_sessions(self) -> None:
        """Cleanup expired sessions periodically"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Get all session keys
                keys = await self._redis.keys("session:*")
                
                for key in keys:
                    session_data = await self._redis.get(key)
                    if session_data:
                        session = json.loads(session_data)
                        if datetime.fromisoformat(session["expires_at"]) < \
                           datetime.utcnow():
                            await self.destroy_session(
                                session["session_id"]
                            )
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Session cleanup failed: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying 