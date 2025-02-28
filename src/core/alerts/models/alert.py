from typing import Dict, Optional, List
from datetime import datetime
from pydantic import validator
from .base import BaseDBModel

class Alert(BaseDBModel):
    """Alert model"""
    
    type: str
    level: str
    data: Dict
    location: str
    camera_id: Optional[str]
    face_id: Optional[str]
    acknowledged: bool = False
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    notes: Optional[str]
    notifications_sent: List[Dict] = []
    
    @validator('level')
    def validate_level(cls, v):
        """Validate alert level"""
        valid_levels = ['critical', 'high', 'medium', 'low']
        if v not in valid_levels:
            raise ValueError(f"Invalid alert level: {v}")
        return v

    async def send_notifications(self, app) -> None:
        """Send alert notifications"""
        try:
            # Get notification channels
            channels = app.alerts._channels
            
            # Send to each channel
            for name, channel in channels.items():
                try:
                    success = await channel.send(
                        'alert',
                        self.dict()
                    )
                    
                    self.notifications_sent.append({
                        'channel': name,
                        'success': success,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    app.logger.error(
                        f"Notification failed for channel {name}: {str(e)}"
                    )
            
            # Update notification status
            await app.db.alerts.update_one(
                {'id': self.id},
                {'$set': {'notifications_sent': self.notifications_sent}}
            )
            
        except Exception as e:
            app.logger.error(f"Alert notification failed: {str(e)}") 