from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass

class AlertHandler(ABC):
    @abstractmethod
    async def handle(self, alert: 'Alert'):
        pass
