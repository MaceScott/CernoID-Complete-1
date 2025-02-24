"""
Notification service implementation.
Handles sending notifications through various channels.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import httpx
from core.config.settings import get_settings
from core.utils.errors import handle_errors
import asyncio
import json
import firebase_admin
from firebase_admin import messaging, credentials
import aiohttp
from pathlib import Path
from core.database.service import DatabaseService

logger = logging.getLogger(__name__)
settings = get_settings()

class NotificationService:
    """
    Advanced notification service with multiple providers
    """
    
    def __init__(self):
        self.email_config = {
            "hostname": settings.smtp_host,
            "port": settings.smtp_port,
            "username": settings.smtp_username,
            "password": settings.smtp_password,
            "use_tls": settings.smtp_use_tls
        }
        
        self.webhook_urls = settings.notification_webhooks
        self._http_client = httpx.AsyncClient(timeout=10.0)
        
        # Initialize Firebase
        self._init_firebase()
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession()
        
        # Initialize notification queue
        self.queue = asyncio.Queue()
        
        # Start queue processor
        self.processor_task = asyncio.create_task(self._process_queue())
        
        self.db = DatabaseService()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.aclose()

    @handle_errors
    async def send_access_notification(self,
                                     person_name: str,
                                     access_point: str,
                                     access_type: str,
                                     success: bool,
                                     recipients: List[str],
                                     metadata: Optional[Dict] = None) -> bool:
        """
        Send access notification to specified recipients
        
        Args:
            person_name: Name of person accessing
            access_point: Location or device ID
            access_type: Type of access (entry/exit)
            success: Whether access was granted
            recipients: List of recipient email addresses
            metadata: Additional notification information
            
        Returns:
            True if notification sent successfully
        """
        # Prepare notification content
        subject = f"Access {'Granted' if success else 'Denied'}: {person_name}"
        content = (
            f"Access {'granted' if success else 'denied'} for {person_name}\n"
            f"Access Point: {access_point}\n"
            f"Type: {access_type}\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        
        if metadata:
            content += "\nAdditional Information:\n"
            for key, value in metadata.items():
                content += f"{key}: {value}\n"

        # Send email notification
        await self.send_email(recipients, subject, content)
        
        # Send webhook notifications if configured
        if self.webhook_urls:
            notification_data = {
                "event": "access",
                "person_name": person_name,
                "access_point": access_point,
                "access_type": access_type,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            await self.send_webhooks(notification_data)

        return True

    @handle_errors
    async def send_email(self,
                        recipients: List[str],
                        subject: str,
                        content: str,
                        html_content: Optional[str] = None) -> bool:
        """
        Send email to recipients
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            content: Plain text content
            html_content: Optional HTML content
            
        Returns:
            True if email sent successfully
        """
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.email_config["username"]
        message["To"] = ", ".join(recipients)

        # Add plain text content
        message.attach(MIMEText(content, "plain"))

        # Add HTML content if provided
        if html_content:
            message.attach(MIMEText(html_content, "html"))

        # Send email
        try:
            async with aiosmtplib.SMTP(
                hostname=self.email_config["hostname"],
                port=self.email_config["port"],
                use_tls=self.email_config["use_tls"]
            ) as smtp:
                await smtp.login(
                    self.email_config["username"],
                    self.email_config["password"]
                )
                await smtp.send_message(message)
                
            logger.info(f"Email sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise

    @handle_errors
    async def send_webhooks(self, data: Dict[str, Any]) -> List[bool]:
        """
        Send notifications to configured webhooks
        
        Args:
            data: Notification data to send
            
        Returns:
            List of success/failure for each webhook
        """
        results = []
        
        for webhook_url in self.webhook_urls:
            try:
                response = await self._http_client.post(
                    webhook_url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                success = response.status_code in (200, 201, 202)
                results.append(success)
                
                if not success:
                    logger.warning(
                        f"Webhook notification failed for {webhook_url}: "
                        f"Status {response.status_code}"
                    )
                    
            except Exception as e:
                logger.error(f"Webhook notification failed for {webhook_url}: {str(e)}")
                results.append(False)

        return results

    @handle_errors
    async def send_alert(self,
                        title: str,
                        message: str,
                        level: str = "info",
                        recipients: Optional[List[str]] = None) -> bool:
        """
        Send alert notification
        
        Args:
            title: Alert title
            message: Alert message
            level: Alert level (info/warning/error)
            recipients: Optional list of recipients
            
        Returns:
            True if alert sent successfully
        """
        if recipients is None:
            recipients = settings.alert_recipients.get(level, [])

        if not recipients:
            logger.warning(f"No recipients configured for {level} alerts")
            return False

        # Send email alert
        subject = f"[{level.upper()}] {title}"
        await self.send_email(recipients, subject, message)

        # Send webhook alert if configured
        if self.webhook_urls:
            alert_data = {
                "event": "alert",
                "title": title,
                "message": message,
                "level": level,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_webhooks(alert_data)

        return True

    def _init_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            cred = credentials.Certificate(
                self.settings.firebase_credentials_path
            )
            firebase_admin.initialize_app(cred)
            self.logger.info("Firebase initialized successfully")
        except Exception as e:
            self.logger.error(f"Firebase initialization failed: {str(e)}")
            
    async def send_notification(self,
                              user_ids: List[int],
                              title: str,
                              body: str,
                              data: Optional[Dict] = None,
                              priority: str = "high") -> bool:
        """
        Send notification to specified users.
        """
        try:
            # Get user tokens
            tokens = await self._get_user_tokens(user_ids)
            if not tokens:
                return False
                
            # Create message
            message = messaging.MulticastMessage(
                tokens=tokens,
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                android=messaging.AndroidConfig(
                    priority=priority,
                    notification=messaging.AndroidNotification(
                        icon="notification_icon",
                        color="#4CAF50"
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1
                        )
                    )
                )
            )
            
            # Add to queue
            await self.queue.put({
                "type": "fcm",
                "message": message,
                "timestamp": datetime.utcnow()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Notification error: {str(e)}")
            return False
            
    async def send_alert(self,
                        alert_type: str,
                        message: str,
                        metadata: Optional[Dict] = None) -> bool:
        """
        Send security alert to all admin users.
        """
        try:
            # Get admin users
            admin_ids = await self._get_admin_users()
            
            # Prepare alert data
            data = {
                "type": alert_type,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Send notification
            return await self.send_notification(
                user_ids=admin_ids,
                title=f"Security Alert: {alert_type}",
                body=message,
                data=data,
                priority="high"
            )
            
        except Exception as e:
            self.logger.error(f"Alert error: {str(e)}")
            return False
            
    async def send_threat_notification(self,
                                     threat_data: Dict) -> bool:
        """
        Send notification for detected threat.
        """
        try:
            # Get security personnel
            security_ids = await self._get_security_users()
            
            # Prepare message
            title = f"Threat Detected: {threat_data['type']}"
            body = f"Location: {threat_data['location']}"
            
            # Send notification
            return await self.send_notification(
                user_ids=security_ids,
                title=title,
                body=body,
                data=threat_data,
                priority="high"
            )
            
        except Exception as e:
            self.logger.error(f"Threat notification error: {str(e)}")
            return False
            
    async def _process_queue(self):
        """
        Process notification queue.
        """
        while True:
            try:
                # Get notification from queue
                notification = await self.queue.get()
                
                if notification["type"] == "fcm":
                    # Send Firebase notification
                    response = await asyncio.to_thread(
                        messaging.send_multicast,
                        notification["message"]
                    )
                    
                    # Log results
                    self.logger.info(
                        f"Sent {response.success_count} messages successfully"
                    )
                    
                    if response.failure_count > 0:
                        self.logger.warning(
                            f"Failed to send {response.failure_count} messages"
                        )
                        
                self.queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Queue processing error: {str(e)}")
                await asyncio.sleep(1)
                
    async def _get_user_tokens(self,
                             user_ids: List[int]) -> List[str]:
        """Get FCM tokens for users."""
        try:
            tokens = []
            async with self.db.session() as session:
                for user_id in user_ids:
                    user = await session.get_user(user_id)
                    if user and user.fcm_token:
                        tokens.append(user.fcm_token)
            return tokens
        except Exception as e:
            self.logger.error(f"Token retrieval error: {str(e)}")
            return []
            
    async def _get_admin_users(self) -> List[int]:
        """Get all admin user IDs."""
        try:
            users = await self.db.search_users({"role": "admin"})
            return [user.id for user in users]
        except Exception as e:
            self.logger.error(f"Admin user retrieval error: {str(e)}")
            return []
            
    async def _get_security_users(self) -> List[int]:
        """Get all security personnel user IDs."""
        try:
            users = await self.db.search_users({"role": "security"})
            return [user.id for user in users]
        except Exception as e:
            self.logger.error(f"Security user retrieval error: {str(e)}")
            return []
            
    async def cleanup(self):
        """Cleanup resources."""
        # Cancel queue processor
        self.processor_task.cancel()
        try:
            await self.processor_task
        except asyncio.CancelledError:
            pass
            
        # Close HTTP session
        await self.session.close() 