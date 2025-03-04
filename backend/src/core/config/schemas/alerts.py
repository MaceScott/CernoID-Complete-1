from typing import Dict, Any, List
from pydantic import BaseModel

class AlertThresholds(BaseModel):
    cpu: int = 80
    memory: int = 80
    disk: int = 90
    network: int = 1000

class QuietHours(BaseModel):
    enabled: bool = False
    start: str = '22:00'
    end: str = '07:00'

class AlertPreferences(BaseModel):
    enabled: bool = True
    channels: List[str] = ['EMAIL']
    minSeverity: str = 'MEDIUM'
    quietHours: QuietHours
    thresholds: AlertThresholds
