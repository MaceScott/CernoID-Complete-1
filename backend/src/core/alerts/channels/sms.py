from typing import Dict, Optional, List, Union
import aiohttp
from datetime import datetime
from ...base import BaseComponent
from ...utils.errors import NotificationError

class SMSChannel(BaseComponent):
    """SMS notification channel for security alerts"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # Provider settings (supports Twilio, Nexmo, etc.)
        self._provider = config.get('sms.provider', 'twilio')
        self._api_key = config.get('sms.api_key')
        self._api_secret = config.get('sms.api_secret')
        self._from_number = config.get('sms.from_number')
        
        # Message settings
        self._max_length = config.get('sms.max_length', 160)
        self._priority_levels = ['critical', 'high']
        
        # Provider API endpoints
        self._api_endpoints = {
            'twilio': 'https://api.twilio.com/2010-04-01/Accounts/{account}/Messages.json',
            'nexmo': 'https://rest.nexmo.com/sms/json'
        }
        
        # Performance tracking
        self._stats = {
            'sent': 0,
            'failed': 0,
            'last_error': None
        }

    async def initialize(self) -> None:
        """Initialize SMS channel"""
        try:
            # Validate provider settings
            if not all([self._api_key, self._api_secret, self._from_number]):
                raise NotificationError("Missing SMS provider credentials")
            
            # Test provider connection
            await self._test_connection()
            
        except Exception as e:
            raise NotificationError(f"SMS channel initialization failed: {str(e)}")

    async def send(self,
                  template_name: str,
                  alert_data: Dict,
                  recipients: Optional[List[str]] = None) -> bool:
        """Send SMS notification"""
        try:
            # Check alert priority
            if alert_data.get('level') not in self._priority_levels:
                return True  # Skip non-priority alerts
            
            # Get recipients
            if not recipients:
                recipients = self._get_recipients(alert_data)
            
            if not recipients:
                raise NotificationError("No recipients specified")
            
            # Create message
            message = self._create_message(alert_data)
            
            # Send to all recipients
            success = True
            for recipient in recipients:
                if not await self._send_sms(recipient, message):
                    success = False
            
            if success:
                self._stats['sent'] += len(recipients)
            
            return success
            
        except Exception as e:
            self._stats['failed'] += 1
            self._stats['last_error'] = str(e)
            self.logger.error(f"SMS sending failed: {str(e)}")
            return False

    async def _test_connection(self) -> None:
        """Test provider connection"""
        try:
            # Send test message to test number if configured
            test_number = self.config.get('sms.test_number')
            if test_number:
                await self._send_sms(
                    test_number,
                    "CernoID-Complete SMS notification test"
                )
        except Exception as e:
            raise NotificationError(f"Provider connection failed: {str(e)}")

    def _create_message(self, alert_data: Dict) -> str:
        """Create SMS message from alert data"""
        try:
            # Basic message format
            level = alert_data.get('level', '').upper()
            alert_type = alert_data.get('type', 'Security Alert')
            location = alert_data.get('data', {}).get('location', 'Unknown')
            timestamp = datetime.fromisoformat(
                alert_data.get('timestamp')
            ).strftime('%H:%M:%S')
            
            message = f"{level} {alert_type}\n"
            message += f"Time: {timestamp}\n"
            message += f"Location: {location}\n"
            
            # Add person details if available
            if person_id := alert_data.get('data', {}).get('person_id'):
                message += f"Person ID: {person_id}\n"
            
            # Add description
            if desc := alert_data.get('data', {}).get('description'):
                message += f"Details: {desc}"
            
            # Truncate if too long
            if len(message) > self._max_length:
                message = message[:self._max_length-3] + "..."
            
            return message
            
        except Exception as e:
            self.logger.error(f"Message creation failed: {str(e)}")
            return "Security Alert - Check dashboard for details"

    async def _send_sms(self, recipient: str, message: str) -> bool:
        """Send SMS via provider API"""
        try:
            if self._provider == 'twilio':
                return await self._send_twilio(recipient, message)
            elif self._provider == 'nexmo':
                return await self._send_nexmo(recipient, message)
            else:
                raise NotificationError(f"Unsupported provider: {self._provider}")
                
        except Exception as e:
            self.logger.error(f"SMS sending failed: {str(e)}")
            return False

    async def _send_twilio(self, recipient: str, message: str) -> bool:
        """Send SMS via Twilio"""
        try:
            import base64
            
            # Prepare authentication
            auth = base64.b64encode(
                f"{self._api_key}:{self._api_secret}".encode()
            ).decode()
            
            # Prepare request
            url = self._api_endpoints['twilio'].format(account=self._api_key)
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'To': recipient,
                'From': self._from_number,
                'Body': message
            }
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as resp:
                    if resp.status == 201:
                        return True
                    else:
                        response = await resp.json()
                        raise NotificationError(
                            f"Twilio error: {response.get('message')}"
                        )
                        
        except Exception as e:
            raise NotificationError(f"Twilio sending failed: {str(e)}")

    async def _send_nexmo(self, recipient: str, message: str) -> bool:
        """Send SMS via Nexmo"""
        try:
            # Prepare request
            url = self._api_endpoints['nexmo']
            data = {
                'api_key': self._api_key,
                'api_secret': self._api_secret,
                'to': recipient,
                'from': self._from_number,
                'text': message
            }
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        # Check message status
                        messages = response.get('messages', [])
                        if messages and messages[0].get('status') == '0':
                            return True
                        else:
                            raise NotificationError(
                                f"Nexmo error: {messages[0].get('error-text')}"
                            )
                    else:
                        raise NotificationError(
                            f"Nexmo API error: {resp.status}"
                        )
                        
        except Exception as e:
            raise NotificationError(f"Nexmo sending failed: {str(e)}")

    def _get_recipients(self, alert_data: Dict) -> List[str]:
        """Get notification recipients based on alert data"""
        # Get default recipients
        recipients = self.config.get('sms.recipients', [])
        
        # Add level-specific recipients
        level = alert_data.get('level', 'medium')
        level_recipients = self.config.get(f'sms.recipients.{level}', [])
        recipients.extend(level_recipients)
        
        return list(set(recipients))  # Remove duplicates

    async def get_stats(self) -> Dict:
        """Get channel statistics"""
        return self._stats.copy() 