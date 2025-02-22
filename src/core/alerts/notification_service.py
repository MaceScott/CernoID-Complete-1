from typing import List
import aiosmtplib
from email.message import EmailMessage
from twilio.rest import Client
from core.config.manager import ConfigManager
from core.error_handling import handle_exceptions

class NotificationService:
    def __init__(self):
        self.config = ConfigManager()
        self.twilio_client = self._setup_twilio()
        self.email_config = self._load_email_config()

    def _setup_twilio(self):
        return Client(
            self.config.get('notifications.twilio.account_sid'),
            self.config.get('notifications.twilio.auth_token')
        )

    @handle_exceptions(logger=notification_logger.error)
    async def send_alert(self, alert: SecurityAlert, channels: List[str]):
        tasks = []
        if 'sms' in channels:
            tasks.append(self.send_sms_alert(alert))
        if 'email' in channels:
            tasks.append(self.send_email_alert(alert))
        
        await asyncio.gather(*tasks)

    async def send_sms_alert(self, alert: SecurityAlert):
        message = self._format_sms_message(alert)
        recipients = self.config.get('notifications.sms.recipients', [])
        
        for recipient in recipients:
            await self.twilio_client.messages.create(
                body=message,
                from_=self.config.get('notifications.sms.from_number'),
                to=recipient
            )

    async def send_email_alert(self, alert: SecurityAlert):
        message = self._format_email_message(alert)
        recipients = self.config.get('notifications.email.recipients', [])
        
        async with aiosmtplib.SMTP(
            hostname=self.email_config['host'],
            port=self.email_config['port'],
            use_tls=True
        ) as smtp:
            await smtp.login(
                self.email_config['username'],
                self.email_config['password']
            )
            await smtp.send_message(message) 
