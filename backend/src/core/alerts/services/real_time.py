from typing import List, Dict
import asyncio
from datetime import datetime
from dataclasses import dataclass
from core.alerts.notification_service import NotificationService
from core.error_handling import handle_exceptions

@dataclass
class SecurityNotification:
    level: str
    message: str
    timestamp: datetime
    details: Dict
    recipients: List[str]
    channels: List[str]

class RealTimeNotifier:
    def __init__(self):
        self.notification_service = NotificationService()
        self.notification_queue = asyncio.Queue()
        self.is_running = False

    async def start(self):
        self.is_running = True
        await self._process_notification_queue()

    async def stop(self):
        self.is_running = False

    @handle_exceptions(logger=notification_logger.error)
    async def send_instant_notification(self, notification: SecurityNotification):
        await self.notification_queue.put(notification)

    async def _process_notification_queue(self):
        while self.is_running:
            notification = await self.notification_queue.get()
            try:
                await self._send_notification(notification)
            except Exception as e:
                notification_logger.error(f"Failed to send notification: {e}")
            finally:
                self.notification_queue.task_done()

    async def _send_notification(self, notification: SecurityNotification):
        tasks = []
        for channel in notification.channels:
            if channel == 'sms':
                tasks.append(self._send_sms(notification))
            elif channel == 'email':
                tasks.append(self._send_email(notification))
            elif channel == 'push':
                tasks.append(self._send_push_notification(notification))
        
        await asyncio.gather(*tasks) 
