from typing import Dict, Optional, Any, List
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ...base import BaseComponent

class SMTPBackend(BaseComponent):
    """SMTP email backend"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._client = None
        self._host = self.config.get('email.smtp.host', 'localhost')
        self._port = self.config.get('email.smtp.port', 587)
        self._username = self.config.get('email.smtp.username')
        self._password = self.config.get('email.smtp.password')
        self._use_tls = self.config.get('email.smtp.tls', True)
        self._timeout = self.config.get('email.smtp.timeout', 30)
        self._pool_size = self.config.get('email.smtp.pool_size', 10)
        self._semaphore = None
        self._stats = {
            'connected': False,
            'sent': 0,
            'failed': 0
        }

    async def initialize(self) -> None:
        """Initialize SMTP backend"""
        self._semaphore = asyncio.Semaphore(self._pool_size)
        await self._connect()

    async def cleanup(self) -> None:
        """Cleanup backend resources"""
        if self._client:
            try:
                await self._client.quit()
            except Exception:
                pass
            self._client = None
            self._stats['connected'] = False

    async def send(self,
                  sender: str,
                  recipients: List[str],
                  message: str) -> bool:
        """Send email via SMTP"""
        async with self._semaphore:
            try:
                # Ensure connected
                if not self._client:
                    await self._connect()
                    
                # Send message
                await self._client.sendmail(
                    sender,
                    recipients,
                    message
                )
                
                self._stats['sent'] += 1
                return True
                
            except (aiosmtplib.SMTPException, ConnectionError) as e:
                self.logger.error(f"SMTP send error: {str(e)}")
                
                # Try to reconnect
                await self._connect()
                
                try:
                    # Retry send
                    await self._client.sendmail(
                        sender,
                        recipients,
                        message
                    )
                    
                    self._stats['sent'] += 1
                    return True
                    
                except Exception as e:
                    self.logger.error(
                        f"SMTP retry send error: {str(e)}"
                    )
                    self._stats['failed'] += 1
                    return False
                    
            except Exception as e:
                self.logger.error(f"SMTP error: {str(e)}")
                self._stats['failed'] += 1
                return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        return self._stats.copy()

    async def _connect(self) -> None:
        """Connect to SMTP server"""
        try:
            # Close existing connection
            if self._client:
                try:
                    await self._client.quit()
                except Exception:
                    pass
                    
            # Create client
            self._client = aiosmtplib.SMTP(
                hostname=self._host,
                port=self._port,
                timeout=self._timeout
            )
            
            # Connect
            await self._client.connect()
            
            # Start TLS if enabled
            if self._use_tls:
                await self._client.starttls()
                
            # Login if credentials provided
            if self._username and self._password:
                await self._client.login(
                    self._username,
                    self._password
                )
                
            self._stats['connected'] = True
            
        except Exception as e:
            self.logger.error(f"SMTP connection error: {str(e)}")
            self._client = None
            self._stats['connected'] = False
            raise 