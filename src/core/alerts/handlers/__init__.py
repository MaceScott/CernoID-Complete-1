from typing import Protocol

class AlertHandler(Protocol):
    async def handle(self, alert_data: dict):
        pass
