from typing import Dict, Any
from .models.alert import Alert
from .handlers.base import AlertHandler
from .services.real_time import RealTimeNotifier
from .channels import EmailChannel, PushChannel, SMSChannel
from ..config.settings import Settings

class AlertManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.handlers: Dict[str, AlertHandler] = {}
        self.channels: Dict[str, Any] = {}
        self.real_time = RealTimeNotifier()
        self._initialize()

    def _initialize(self):
        if not self.settings.alert_preferences['enabled']:
            return

        self._setup_channels()
        self._setup_handlers()

    def _setup_channels(self):
        channel_map = {
            'EMAIL': EmailChannel,
            'PUSH': PushChannel,
            'SMS': SMSChannel
        }

        for channel_type in self.settings.alert_preferences['channels']:
            if channel_type in channel_map:
                self.channels[channel_type] = channel_map[channel_type](self.settings)

    def _setup_handlers(self):
        # Initialize handlers based on settings
        pass

    async def send_alert(self, alert: Alert):
        if not self._should_send_alert(alert):
            return

        for channel in self.channels.values():
            await channel.send(alert)

        await self.real_time.notify(alert)

    def _should_send_alert(self, alert: Alert) -> bool:
        if not self.settings.alert_preferences['enabled']:
            return False

        if alert.severity < self.settings.alert_preferences['minSeverity']:
            return False

        return True
