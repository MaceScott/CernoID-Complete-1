from typing import List, Dict
import firebase_admin
from firebase_admin import messaging
from dataclasses import dataclass
from datetime import datetime
from core.error_handling import handle_exceptions

@dataclass
class MobileNotification:
    title: str
    body: str
    data: Dict
    priority: str = "high"
    topic: str = "security_alerts"

class MobileNotificationService:
    def __init__(self):
        self.firebase_app = firebase_admin.initialize_app()
        self.default_ttl = 3600  # 1 hour

    @handle_exceptions(logger=mobile_logger.error)
    async def send_notification(
        self,
        notification: MobileNotification,
        user_tokens: List[str]
    ):
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.body
            ),
            data=notification.data,
            tokens=user_tokens,
            android=messaging.AndroidConfig(
                priority=notification.priority,
                ttl=self.default_ttl
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=notification.title,
                            body=notification.body
                        ),
                        sound="default"
                    )
                )
            )
        )
        
        response = await messaging.send_multicast(message)
        return response

    async def subscribe_to_topic(self, token: str, topic: str):
        response = await messaging.subscribe_to_topic(
            [token],
            topic
        )
        return response

    async def unsubscribe_from_topic(self, token: str, topic: str):
        response = await messaging.unsubscribe_from_topic(
            [token],
            topic
        )
        return response 
