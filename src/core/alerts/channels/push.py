from typing import Dict, Optional, List, Union
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from ...base import BaseComponent
from ...utils.errors import NotificationError

class PushChannel(BaseComponent):
    """Push notification channel for mobile alerts"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # Firebase settings
        self._firebase_key = config.get('push.firebase_key')
        self._firebase_url = 'https://fcm.googleapis.com/fcm/send'
        
        # Device management
        self._device_file = Path(config.get('push.device_file', 'data/devices.json'))
        self._devices: Dict[str, Dict] = {}
        self._max_devices_per_user = config.get('push.max_devices', 5)
        
        # Notification settings
        self._notification_types = {
            'critical': {
                'priority': 'high',
                'ttl': 3600,  # 1 hour
                'sound': 'alert.wav'
            },
            'high': {
                'priority': 'high',
                'ttl': 7200,  # 2 hours
                'sound': 'notification.wav'
            },
            'medium': {
                'priority': 'normal',
                'ttl': 14400,  # 4 hours
                'sound': None
            },
            'low': {
                'priority': 'normal',
                'ttl': 28800,  # 8 hours
                'sound': None
            }
        }
        
        # Performance tracking
        self._stats = {
            'sent': 0,
            'failed': 0,
            'devices': 0,
            'last_error': None
        }

    async def initialize(self) -> None:
        """Initialize push notification channel"""
        try:
            # Validate Firebase settings
            if not self._firebase_key:
                raise NotificationError("Missing Firebase API key")
            
            # Load registered devices
            await self._load_devices()
            
            # Update statistics
            self._stats['devices'] = len(self._devices)
            
        except Exception as e:
            raise NotificationError(f"Push channel initialization failed: {str(e)}")

    async def send(self,
                  template_name: str,
                  alert_data: Dict,
                  recipients: Optional[List[str]] = None) -> bool:
        """Send push notification"""
        try:
            # Get recipients' devices
            devices = await self._get_recipient_devices(recipients, alert_data)
            if not devices:
                return True  # No devices to notify
            
            # Create notification
            notification = self._create_notification(alert_data)
            
            # Send to all devices
            success = True
            for device_tokens in self._chunk_devices(devices):
                if not await self._send_notification(device_tokens, notification):
                    success = False
            
            if success:
                self._stats['sent'] += len(devices)
            
            return success
            
        except Exception as e:
            self._stats['failed'] += 1
            self._stats['last_error'] = str(e)
            self.logger.error(f"Push notification failed: {str(e)}")
            return False

    async def register_device(self,
                            user_id: str,
                            token: str,
                            device_info: Dict) -> bool:
        """Register new device for push notifications"""
        try:
            # Validate token
            if not token or len(token) < 32:
                raise ValueError("Invalid device token")
            
            # Check user device limit
            user_devices = [d for d in self._devices.values() 
                          if d['user_id'] == user_id]
            if len(user_devices) >= self._max_devices_per_user:
                # Remove oldest device
                oldest = min(user_devices, key=lambda d: d['registered_at'])
                await self.remove_device(oldest['token'])
            
            # Add new device
            self._devices[token] = {
                'user_id': user_id,
                'token': token,
                'info': device_info,
                'registered_at': datetime.utcnow().isoformat()
            }
            
            # Save devices
            await self._save_devices()
            
            # Update statistics
            self._stats['devices'] = len(self._devices)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Device registration failed: {str(e)}")
            return False

    async def remove_device(self, token: str) -> bool:
        """Remove device registration"""
        try:
            if token in self._devices:
                del self._devices[token]
                await self._save_devices()
                
                # Update statistics
                self._stats['devices'] = len(self._devices)
                
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Device removal failed: {str(e)}")
            return False

    def _create_notification(self, alert_data: Dict) -> Dict:
        """Create push notification payload"""
        try:
            level = alert_data.get('level', 'medium')
            settings = self._notification_types[level]
            
            # Basic notification
            notification = {
                'title': f"{level.upper()} Security Alert",
                'body': self._create_message(alert_data),
                'icon': 'security_alert',
                'sound': settings['sound'],
                'priority': settings['priority'],
                'time_to_live': settings['ttl']
            }
            
            # Add data payload
            notification['data'] = {
                'alert_id': alert_data.get('id'),
                'type': alert_data.get('type'),
                'level': level,
                'timestamp': alert_data.get('timestamp'),
                'location': alert_data.get('data', {}).get('location')
            }
            
            return notification
            
        except Exception as e:
            self.logger.error(f"Notification creation failed: {str(e)}")
            return {}

    def _create_message(self, alert_data: Dict) -> str:
        """Create notification message"""
        try:
            location = alert_data.get('data', {}).get('location', 'Unknown')
            message = f"Security alert at {location}"
            
            if desc := alert_data.get('data', {}).get('description'):
                message += f": {desc}"
            
            return message
            
        except Exception:
            return "Security Alert - Check dashboard for details"

    async def _send_notification(self,
                               tokens: List[str],
                               notification: Dict) -> bool:
        """Send Firebase push notification"""
        try:
            headers = {
                'Authorization': f'key={self._firebase_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'registration_ids': tokens,
                'notification': notification,
                'data': notification['data']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._firebase_url,
                    headers=headers,
                    json=data
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        self._handle_firebase_response(response, tokens)
                        return True
                    else:
                        raise NotificationError(
                            f"Firebase API error: {resp.status}"
                        )
                        
        except Exception as e:
            raise NotificationError(f"Push notification failed: {str(e)}")

    def _handle_firebase_response(self,
                                response: Dict,
                                tokens: List[str]) -> None:
        """Handle Firebase response and cleanup invalid tokens"""
        results = response.get('results', [])
        for token, result in zip(tokens, results):
            if error := result.get('error'):
                if error in ['NotRegistered', 'InvalidRegistration']:
                    # Remove invalid token
                    asyncio.create_task(self.remove_device(token))

    def _chunk_devices(self,
                      devices: List[str],
                      chunk_size: int = 1000) -> List[List[str]]:
        """Split devices into chunks for batch processing"""
        return [devices[i:i + chunk_size] 
                for i in range(0, len(devices), chunk_size)]

    async def _get_recipient_devices(self,
                                   recipients: Optional[List[str]],
                                   alert_data: Dict) -> List[str]:
        """Get device tokens for recipients"""
        devices = []
        
        if recipients:
            # Get devices for specific recipients
            devices = [d['token'] for d in self._devices.values()
                      if d['user_id'] in recipients]
        else:
            # Get devices based on alert level
            level = alert_data.get('level', 'medium')
            level_recipients = self.config.get(f'push.recipients.{level}', [])
            devices = [d['token'] for d in self._devices.values()
                      if d['user_id'] in level_recipients]
        
        return devices

    async def _load_devices(self) -> None:
        """Load registered devices from file"""
        try:
            if self._device_file.exists():
                with open(self._device_file, 'r') as f:
                    self._devices = json.load(f)
        except Exception as e:
            raise NotificationError(f"Device loading failed: {str(e)}")

    async def _save_devices(self) -> None:
        """Save registered devices to file"""
        try:
            self._device_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._device_file, 'w') as f:
                json.dump(self._devices, f, indent=2)
        except Exception as e:
            raise NotificationError(f"Device saving failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get channel statistics"""
        return self._stats.copy() 