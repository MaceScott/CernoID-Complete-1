from .base import AlertHandler
from typing import Dict, Any
import aiosmtplib
from email.message import EmailMessage

class EmailAlertHandler(AlertHandler):
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.smtp_config = settings.get('smtp', {})

    async def handle(self, alert: 'Alert'):
        message = EmailMessage()
        message['Subject'] = f'[{alert.severity}] {alert.type}'
        message['From'] = self.smtp_config['from_email']
        message['To'] = self.smtp_config['to_email']
        message.set_content(alert.message)

        await aiosmtplib.send(
            message,
            hostname=self.smtp_config['host'],
            port=self.smtp_config['port'],
            username=self.smtp_config['username'],
            password=self.smtp_config['password'],
            use_tls=self.smtp_config.get('use_tls', True)
        )
