from typing import Dict, Optional, List, Union
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from pathlib import Path
from ...base import BaseComponent
from ...utils.errors import NotificationError

class EmailChannel(BaseComponent):
    """Email notification channel for security alerts"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # SMTP settings
        self._host = config.get('email.host', 'smtp.gmail.com')
        self._port = config.get('email.port', 587)
        self._username = config.get('email.username')
        self._password = config.get('email.password')
        self._from_addr = config.get('email.from_address')
        self._use_tls = config.get('email.use_tls', True)
        
        # Template settings
        self._template_dir = Path(config.get('email.template_dir', 'templates/email'))
        self._templates: Dict[str, Template] = {}
        
        # Performance tracking
        self._stats = {
            'sent': 0,
            'failed': 0,
            'last_error': None
        }

    async def initialize(self) -> None:
        """Initialize email channel"""
        try:
            # Load email templates
            await self._load_templates()
            
            # Test SMTP connection
            await self._test_connection()
            
        except Exception as e:
            raise NotificationError(f"Email channel initialization failed: {str(e)}")

    async def send(self,
                  template_name: str,
                  alert_data: Dict,
                  recipients: Optional[List[str]] = None) -> bool:
        """Send email notification"""
        try:
            # Get template
            template = self._templates.get(template_name)
            if not template:
                raise NotificationError(f"Template not found: {template_name}")
            
            # Get recipients
            if not recipients:
                recipients = self._get_recipients(alert_data)
            
            if not recipients:
                raise NotificationError("No recipients specified")
            
            # Create message
            msg = await self._create_message(template, alert_data, recipients)
            
            # Send email
            await self._send_email(msg, recipients)
            
            self._stats['sent'] += 1
            return True
            
        except Exception as e:
            self._stats['failed'] += 1
            self._stats['last_error'] = str(e)
            self.logger.error(f"Email sending failed: {str(e)}")
            return False

    async def _load_templates(self) -> None:
        """Load email templates"""
        try:
            self._template_dir.mkdir(parents=True, exist_ok=True)
            
            # Load default template if none exist
            if not list(self._template_dir.glob('*.html')):
                await self._create_default_template()
            
            # Load all templates
            for template_file in self._template_dir.glob('*.html'):
                name = template_file.stem
                with open(template_file, 'r') as f:
                    self._templates[name] = Template(f.read())
                    
        except Exception as e:
            raise NotificationError(f"Template loading failed: {str(e)}")

    async def _create_default_template(self) -> None:
        """Create default email template"""
        default_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .alert { padding: 15px; margin: 10px 0; border-radius: 4px; }
                .critical { background: #ffebee; border: 1px solid #ef5350; }
                .high { background: #fff3e0; border: 1px solid #ff9800; }
                .medium { background: #e3f2fd; border: 1px solid #2196f3; }
                .low { background: #e8f5e9; border: 1px solid #4caf50; }
            </style>
        </head>
        <body>
            <h2>Security Alert</h2>
            <div class="alert {{ alert.level }}">
                <h3>{{ alert.type }}</h3>
                <p><strong>Time:</strong> {{ alert.timestamp }}</p>
                <p><strong>Location:</strong> {{ alert.data.location }}</p>
                {% if alert.data.person_id %}
                <p><strong>Person:</strong> {{ alert.data.person_id }}</p>
                {% endif %}
                <p><strong>Details:</strong> {{ alert.data.description }}</p>
            </div>
            {% if alert.data.image_url %}
            <p><a href="{{ alert.data.image_url }}">View Image</a></p>
            {% endif %}
            <p>Please take appropriate action based on security protocols.</p>
        </body>
        </html>
        """
        
        template_file = self._template_dir / 'default.html'
        with open(template_file, 'w') as f:
            f.write(default_template)

    async def _test_connection(self) -> None:
        """Test SMTP connection"""
        try:
            smtp = aiosmtplib.SMTP(hostname=self._host, port=self._port)
            await smtp.connect()
            
            if self._use_tls:
                await smtp.starttls()
            
            if self._username and self._password:
                await smtp.login(self._username, self._password)
            
            await smtp.quit()
            
        except Exception as e:
            raise NotificationError(f"SMTP connection failed: {str(e)}")

    async def _create_message(self,
                            template: Template,
                            alert_data: Dict,
                            recipients: List[str]) -> MIMEMultipart:
        """Create email message"""
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self._get_subject(alert_data)
            msg['From'] = self._from_addr
            msg['To'] = ', '.join(recipients)
            
            # Render template
            html = template.render(alert=alert_data)
            
            # Create HTML part
            html_part = MIMEText(html, 'html')
            msg.attach(html_part)
            
            return msg
            
        except Exception as e:
            raise NotificationError(f"Message creation failed: {str(e)}")

    async def _send_email(self,
                         msg: MIMEMultipart,
                         recipients: List[str]) -> None:
        """Send email via SMTP"""
        try:
            smtp = aiosmtplib.SMTP(hostname=self._host, port=self._port)
            await smtp.connect()
            
            if self._use_tls:
                await smtp.starttls()
            
            if self._username and self._password:
                await smtp.login(self._username, self._password)
            
            await smtp.send_message(msg, self._from_addr, recipients)
            await smtp.quit()
            
        except Exception as e:
            raise NotificationError(f"Email sending failed: {str(e)}")

    def _get_subject(self, alert_data: Dict) -> str:
        """Generate email subject"""
        level = alert_data.get('level', 'medium').upper()
        alert_type = alert_data.get('type', 'Security Alert')
        return f"{level} Alert: {alert_type}"

    def _get_recipients(self, alert_data: Dict) -> List[str]:
        """Get notification recipients based on alert data"""
        # Get default recipients
        recipients = self.config.get('email.recipients', [])
        
        # Add level-specific recipients
        level = alert_data.get('level', 'medium')
        level_recipients = self.config.get(f'email.recipients.{level}', [])
        recipients.extend(level_recipients)
        
        # Add type-specific recipients
        alert_type = alert_data.get('type', '')
        type_recipients = self.config.get(f'email.recipients.{alert_type}', [])
        recipients.extend(type_recipients)
        
        return list(set(recipients))  # Remove duplicates

    async def get_stats(self) -> Dict:
        """Get channel statistics"""
        return self._stats.copy() 