from typing import Dict, Optional, Any, List, Union
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
import aiosmtplib
from jinja2 import Template
from ..base import BaseComponent
from ..utils.decorators import handle_errors

class EmailManager(BaseComponent):
    """Advanced email management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._backend = None
        self._templates: Dict[str, Template] = {}
        self._default_sender = self.config.get('email.default_sender')
        self._template_dir = Path(
            self.config.get('email.template_dir', 'templates/email')
        )
        self._max_retries = self.config.get('email.max_retries', 3)
        self._retry_delay = self.config.get('email.retry_delay', 5)
        self._batch_size = self.config.get('email.batch_size', 50)
        self._stats = {
            'sent': 0,
            'failed': 0,
            'retried': 0
        }

    async def initialize(self) -> None:
        """Initialize email manager"""
        # Initialize backend
        backend = self.config.get('email.backend', 'smtp')
        
        if backend == 'smtp':
            from .backends.smtp import SMTPBackend
            self._backend = SMTPBackend(self.config)
        elif backend == 'sendgrid':
            from .backends.sendgrid import SendgridBackend
            self._backend = SendgridBackend(self.config)
        elif backend == 'mailgun':
            from .backends.mailgun import MailgunBackend
            self._backend = MailgunBackend(self.config)
        else:
            from .backends.dummy import DummyBackend
            self._backend = DummyBackend(self.config)
            
        await self._backend.initialize()
        
        # Load templates
        await self._load_templates()

    async def cleanup(self) -> None:
        """Cleanup email resources"""
        if self._backend:
            await self._backend.cleanup()
        self._templates.clear()

    @handle_errors(logger=None)
    async def send(self,
                  to: Union[str, List[str]],
                  subject: str,
                  body: str,
                  sender: Optional[str] = None,
                  cc: Optional[Union[str, List[str]]] = None,
                  bcc: Optional[Union[str, List[str]]] = None,
                  html: Optional[str] = None,
                  attachments: Optional[List[Union[str, Path, Dict]]] = None,
                  template: Optional[str] = None,
                  template_data: Optional[Dict] = None,
                  headers: Optional[Dict] = None) -> bool:
        """Send email"""
        # Normalize recipients
        recipients = self._normalize_recipients(to)
        cc = self._normalize_recipients(cc) if cc else []
        bcc = self._normalize_recipients(bcc) if bcc else []
        
        # Get sender
        sender = sender or self._default_sender
        if not sender:
            raise ValueError("Sender email not specified")
            
        # Handle template
        if template:
            if template not in self._templates:
                raise ValueError(f"Template not found: {template}")
                
            template_data = template_data or {}
            body = self._templates[template].render(**template_data)
            
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = sender
        message['To'] = ', '.join(recipients)
        
        if cc:
            message['Cc'] = ', '.join(cc)
        if bcc:
            message['Bcc'] = ', '.join(bcc)
            
        # Add headers
        if headers:
            for key, value in headers.items():
                message[key] = value
                
        # Add text body
        message.attach(MIMEText(body, 'plain'))
        
        # Add HTML body
        if html:
            message.attach(MIMEText(html, 'html'))
            
        # Add attachments
        if attachments:
            for attachment in attachments:
                part = self._create_attachment(attachment)
                if part:
                    message.attach(part)
                    
        # Send message
        retries = 0
        while retries <= self._max_retries:
            try:
                success = await self._backend.send(
                    sender,
                    recipients + cc + bcc,
                    message.as_string()
                )
                
                if success:
                    self._stats['sent'] += 1
                    return True
                    
                retries += 1
                self._stats['retried'] += 1
                await asyncio.sleep(self._retry_delay)
                
            except Exception as e:
                self.logger.error(f"Email send error: {str(e)}")
                retries += 1
                self._stats['retried'] += 1
                await asyncio.sleep(self._retry_delay)
                
        self._stats['failed'] += 1
        return False

    @handle_errors(logger=None)
    async def send_batch(self,
                        emails: List[Dict]) -> List[bool]:
        """Send batch of emails"""
        results = []
        
        # Process in batches
        for i in range(0, len(emails), self._batch_size):
            batch = emails[i:i + self._batch_size]
            tasks = [
                self.send(**email)
                for email in batch
            ]
            
            # Send batch
            batch_results = await asyncio.gather(
                *tasks,
                return_exceptions=True
            )
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(str(result))
                    results.append(False)
                else:
                    results.append(result)
                    
        return results

    def add_template(self,
                    name: str,
                    template: Union[str, Template]) -> None:
        """Add email template"""
        if isinstance(template, str):
            template = Template(template)
        self._templates[name] = template

    async def get_stats(self) -> Dict[str, Any]:
        """Get email statistics"""
        stats = self._stats.copy()
        
        # Add backend stats
        if self._backend:
            backend_stats = await self._backend.get_stats()
            stats.update(backend_stats)
            
        return stats

    def _normalize_recipients(self,
                            recipients: Union[str, List[str]]) -> List[str]:
        """Normalize email recipients"""
        if not recipients:
            return []
            
        if isinstance(recipients, str):
            return [recipients]
            
        return recipients

    def _create_attachment(self,
                         attachment: Union[str, Path, Dict]) -> Optional[MIMEApplication]:
        """Create email attachment"""
        try:
            if isinstance(attachment, (str, Path)):
                path = Path(attachment)
                if not path.exists():
                    self.logger.error(
                        f"Attachment not found: {path}"
                    )
                    return None
                    
                with open(path, 'rb') as f:
                    part = MIMEApplication(f.read())
                    part.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=path.name
                    )
                    return part
                    
            elif isinstance(attachment, dict):
                data = attachment.get('data')
                filename = attachment.get('filename')
                content_type = attachment.get('content_type')
                
                if not data or not filename:
                    return None
                    
                part = MIMEApplication(data)
                part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=filename
                )
                
                if content_type:
                    part.add_header(
                        'Content-Type',
                        content_type
                    )
                    
                return part
                
        except Exception as e:
            self.logger.error(
                f"Attachment error: {str(e)}"
            )
            return None

    async def _load_templates(self) -> None:
        """Load email templates"""
        if not self._template_dir.exists():
            return
            
        for path in self._template_dir.glob('*.html'):
            try:
                template = Template(path.read_text())
                self.add_template(path.stem, template)
            except Exception as e:
                self.logger.error(
                    f"Template load error: {str(e)}"
                ) 