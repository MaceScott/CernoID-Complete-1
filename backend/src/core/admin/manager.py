from typing import Dict, Optional, List, Union
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import jwt
from ..base import BaseComponent
from ..utils.errors import AdminError

class AdminManager(BaseComponent):
    """Administrative dashboard manager"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # Authentication settings
        self._jwt_secret = config.get('admin.jwt_secret', 'your-secret-key')
        self._token_expiry = config.get('admin.token_expiry', 86400)  # 24 hours
        self._refresh_expiry = config.get('admin.refresh_expiry', 604800)  # 7 days
        
        # Session management
        self._active_sessions: Dict[str, Dict] = {}
        self._max_sessions = config.get('admin.max_sessions', 5)
        
        # Access levels
        self._access_levels = {
            'admin': 100,
            'supervisor': 75,
            'operator': 50,
            'viewer': 25
        }
        
        # System state
        self._system_status = {
            'cameras': {},
            'alerts': {},
            'recognition': {},
            'notifications': {}
        }
        
        # Performance tracking
        self._stats = {
            'active_users': 0,
            'alerts_today': 0,
            'faces_registered': 0,
            'system_uptime': 0
        }

    async def initialize(self) -> None:
        """Initialize admin dashboard"""
        try:
            # Start background tasks
            self._start_background_tasks()
            
            # Initialize system status
            await self._update_system_status()
            
        except Exception as e:
            raise AdminError(f"Admin initialization failed: {str(e)}")

    async def authenticate(self, username: str, password: str) -> Dict:
        """Authenticate admin user"""
        try:
            # Verify credentials
            user = await self._verify_credentials(username, password)
            if not user:
                raise AdminError("Invalid credentials")
            
            # Generate tokens
            access_token = self._generate_token(user, 'access')
            refresh_token = self._generate_token(user, 'refresh')
            
            # Create session
            session_id = await self._create_session(user, access_token)
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_id': session_id,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'permissions': user['permissions']
                }
            }
            
        except Exception as e:
            raise AdminError(f"Authentication failed: {str(e)}")

    async def get_system_status(self, access_level: str) -> Dict:
        """Get system status based on access level"""
        try:
            status = {}
            level = self._access_levels.get(access_level, 0)
            
            # Basic status for all levels
            status['uptime'] = self._stats['system_uptime']
            status['active_users'] = self._stats['active_users']
            
            # Add camera status for operators and above
            if level >= self._access_levels['operator']:
                status['cameras'] = self._system_status['cameras']
            
            # Add detailed stats for supervisors and above
            if level >= self._access_levels['supervisor']:
                status['alerts'] = self._system_status['alerts']
                status['recognition'] = self._system_status['recognition']
            
            # Add full system status for admins
            if level >= self._access_levels['admin']:
                status['notifications'] = self._system_status['notifications']
                status['performance'] = await self._get_performance_metrics()
            
            return status
            
        except Exception as e:
            raise AdminError(f"Status retrieval failed: {str(e)}")

    async def register_face(self,
                          images: List[Union[str, bytes]],
                          metadata: Dict,
                          access_level: str) -> Dict:
        """Register new face in system"""
        try:
            # Verify access level
            if self._access_levels.get(access_level, 0) < self._access_levels['supervisor']:
                raise AdminError("Insufficient permissions")
            
            # Register face
            result = await self.app.recognition.registration.register_person(
                images,
                metadata
            )
            
            # Update statistics
            self._stats['faces_registered'] += 1
            
            return result
            
        except Exception as e:
            raise AdminError(f"Face registration failed: {str(e)}")

    async def update_system_config(self,
                                 config: Dict,
                                 access_level: str) -> bool:
        """Update system configuration"""
        try:
            # Verify admin access
            if self._access_levels.get(access_level, 0) < self._access_levels['admin']:
                raise AdminError("Admin access required")
            
            # Validate configuration
            if not await self._validate_config(config):
                raise AdminError("Invalid configuration")
            
            # Update configuration
            await self.app.config.update(config)
            
            # Restart affected components
            await self._restart_components(config)
            
            return True
            
        except Exception as e:
            raise AdminError(f"Configuration update failed: {str(e)}")

    async def get_alert_history(self,
                              start_time: datetime,
                              end_time: datetime,
                              access_level: str) -> List[Dict]:
        """Get historical alert data"""
        try:
            # Verify operator access
            if self._access_levels.get(access_level, 0) < self._access_levels['operator']:
                raise AdminError("Insufficient permissions")
            
            # Query alerts
            alerts = await self.app.db.alerts.find({
                'timestamp': {
                    '$gte': start_time.isoformat(),
                    '$lte': end_time.isoformat()
                }
            }).to_list(None)
            
            return alerts
            
        except Exception as e:
            raise AdminError(f"Alert history retrieval failed: {str(e)}")

    async def _verify_credentials(self,
                                username: str,
                                password: str) -> Optional[Dict]:
        """Verify user credentials"""
        try:
            # Get user from database
            user = await self.app.db.users.find_one({'username': username})
            if not user:
                return None
            
            # Verify password
            if not await self._verify_password(password, user['password']):
                return None
            
            return user
            
        except Exception:
            return None

    def _generate_token(self, user: Dict, token_type: str) -> str:
        """Generate JWT token"""
        try:
            expiry = self._token_expiry if token_type == 'access' else self._refresh_expiry
            payload = {
                'user_id': str(user['id']),
                'username': user['username'],
                'role': user['role'],
                'type': token_type,
                'exp': datetime.utcnow() + timedelta(seconds=expiry)
            }
            
            return jwt.encode(payload, self._jwt_secret, algorithm='HS256')
            
        except Exception as e:
            raise AdminError(f"Token generation failed: {str(e)}")

    async def _create_session(self, user: Dict, token: str) -> str:
        """Create new user session"""
        try:
            # Clean old sessions
            user_sessions = [s for s in self._active_sessions.values()
                           if s['user_id'] == user['id']]
            
            if len(user_sessions) >= self._max_sessions:
                # Remove oldest session
                oldest = min(user_sessions, key=lambda s: s['created_at'])
                del self._active_sessions[oldest['id']]
            
            # Create new session
            session_id = str(uuid.uuid4())
            self._active_sessions[session_id] = {
                'id': session_id,
                'user_id': user['id'],
                'token': token,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Update statistics
            self._stats['active_users'] = len(set(
                s['user_id'] for s in self._active_sessions.values()
            ))
            
            return session_id
            
        except Exception as e:
            raise AdminError(f"Session creation failed: {str(e)}")

    async def _update_system_status(self) -> None:
        """Update system status information"""
        try:
            # Update camera status
            self._system_status['cameras'] = {
                camera_id: await camera.get_stats()
                for camera_id, camera in self.app.vision._cameras.items()
            }
            
            # Update alert status
            self._system_status['alerts'] = await self.app.alerts.get_stats()
            
            # Update recognition status
            self._system_status['recognition'] = {
                'matcher': await self.app.recognition.matcher.get_stats(),
                'registration': await self.app.recognition.registration.get_stats()
            }
            
            # Update notification status
            self._system_status['notifications'] = {
                channel: await handler.get_stats()
                for channel, handler in self.app.alerts._channels.items()
            }
            
        except Exception as e:
            self.logger.error(f"Status update failed: {str(e)}")

    def _start_background_tasks(self) -> None:
        """Start background tasks"""
        asyncio.create_task(self._status_update_task())
        asyncio.create_task(self._session_cleanup_task())

    async def _status_update_task(self) -> None:
        """Periodic status update task"""
        while True:
            try:
                await self._update_system_status()
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                self.logger.error(f"Status update error: {str(e)}")
                await asyncio.sleep(5)

    async def _session_cleanup_task(self) -> None:
        """Clean expired sessions"""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_sessions = [
                    sid for sid, session in self._active_sessions.items()
                    if current_time - datetime.fromisoformat(session['created_at']) >
                    timedelta(seconds=self._token_expiry)
                ]
                
                for session_id in expired_sessions:
                    del self._active_sessions[session_id]
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Session cleanup error: {str(e)}")
                await asyncio.sleep(300)

    async def get_stats(self) -> Dict:
        """Get admin dashboard statistics"""
        return self._stats.copy() 