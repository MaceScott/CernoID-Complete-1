from typing import Dict, List, Optional, Union, Callable
import asyncio
from datetime import datetime
import json
from pathlib import Path
from ..base import BaseComponent
from ..utils.errors import AlertError

class AlertManager(BaseComponent):
    """Security alert and notification management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # Alert configuration
        self._alert_levels = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        self._handlers: Dict[str, List[Callable]] = {}
        self._channels: Dict[str, 'AlertChannel'] = {}
        self._rules: List[Dict] = []
        
        # Alert buffering
        self._buffer_size = config.get('alerts.buffer_size', 100)
        self._buffer: List[Dict] = []
        self._processing = False
        
        # Storage settings
        self._storage_path = Path(config.get('alerts.storage_path', 'alerts'))
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self._stats = {
            'alerts_triggered': 0,
            'notifications_sent': 0,
            'failed_notifications': 0
        }

    async def initialize(self) -> None:
        """Initialize alert manager"""
        try:
            # Load alert rules
            await self._load_rules()
            
            # Initialize notification channels
            await self._initialize_channels()
            
            # Start background tasks
            self._start_background_tasks()
            
        except Exception as e:
            raise AlertError(f"Alert initialization failed: {str(e)}")

    async def trigger_alert(self,
                          alert_type: str,
                          data: Dict,
                          level: str = 'medium') -> bool:
        """Trigger new security alert"""
        try:
            # Validate alert level
            if level not in self._alert_levels:
                raise ValueError(f"Invalid alert level: {level}")
            
            # Create alert object
            alert = {
                'id': self._generate_alert_id(),
                'type': alert_type,
                'level': level,
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
            
            # Add to buffer
            self._buffer.append(alert)
            if len(self._buffer) >= self._buffer_size:
                await self._process_alerts()
            
            # Process immediately if critical
            if level == 'critical':
                await self._process_alert(alert)
            
            self._stats['alerts_triggered'] += 1
            return True
            
        except Exception as e:
            raise AlertError(f"Alert trigger failed: {str(e)}")

    async def add_handler(self,
                         alert_type: str,
                         handler: Callable) -> None:
        """Add alert handler function"""
        if alert_type not in self._handlers:
            self._handlers[alert_type] = []
        self._handlers[alert_type].append(handler)

    async def add_rule(self, rule: Dict) -> None:
        """Add alert processing rule"""
        try:
            # Validate rule format
            required_fields = ['type', 'conditions', 'actions']
            for field in required_fields:
                if field not in rule:
                    raise ValueError(f"Missing required field: {field}")
            
            self._rules.append(rule)
            await self._save_rules()
            
        except Exception as e:
            raise AlertError(f"Rule addition failed: {str(e)}")

    async def _process_alerts(self) -> None:
        """Process buffered alerts"""
        if self._processing or not self._buffer:
            return
            
        try:
            self._processing = True
            alerts = self._buffer.copy()
            self._buffer.clear()
            
            for alert in alerts:
                if not alert['processed']:
                    await self._process_alert(alert)
                    
        except Exception as e:
            self.logger.error(f"Alert processing error: {str(e)}")
        finally:
            self._processing = False

    async def _process_alert(self, alert: Dict) -> None:
        """Process single alert"""
        try:
            # Check alert rules
            actions = await self._evaluate_rules(alert)
            
            # Execute handlers
            if alert['type'] in self._handlers:
                for handler in self._handlers[alert['type']]:
                    try:
                        await handler(alert)
                    except Exception as e:
                        self.logger.error(f"Handler error: {str(e)}")
            
            # Execute actions
            for action in actions:
                await self._execute_action(action, alert)
            
            # Store alert
            await self._store_alert(alert)
            
            alert['processed'] = True
            
        except Exception as e:
            self.logger.error(f"Alert processing error: {str(e)}")

    async def _evaluate_rules(self, alert: Dict) -> List[Dict]:
        """Evaluate alert rules"""
        actions = []
        
        for rule in self._rules:
            if rule['type'] == alert['type'] or rule['type'] == '*':
                if await self._check_conditions(rule['conditions'], alert):
                    actions.extend(rule['actions'])
        
        return actions

    async def _check_conditions(self,
                              conditions: Dict,
                              alert: Dict) -> bool:
        """Check if alert matches conditions"""
        try:
            for key, value in conditions.items():
                if key == 'level':
                    if self._alert_levels[alert['level']] > self._alert_levels[value]:
                        return False
                elif key in alert['data']:
                    if isinstance(value, (list, tuple)):
                        if alert['data'][key] not in value:
                            return False
                    elif alert['data'][key] != value:
                        return False
            return True
        except Exception:
            return False

    async def _execute_action(self, action: Dict, alert: Dict) -> None:
        """Execute alert action"""
        try:
            action_type = action['type']
            
            if action_type == 'notify':
                # Send notification
                channel = action.get('channel', 'email')
                if channel in self._channels:
                    success = await self._channels[channel].send(
                        action.get('template', 'default'),
                        alert
                    )
                    if success:
                        self._stats['notifications_sent'] += 1
                    else:
                        self._stats['failed_notifications'] += 1
            
            elif action_type == 'webhook':
                # Call webhook
                await self.app.http.post(
                    action['url'],
                    json=alert
                )
            
            elif action_type == 'command':
                # Execute command
                await self.app.commands.execute(
                    action['command'],
                    alert
                )
            
        except Exception as e:
            self.logger.error(f"Action execution error: {str(e)}")

    async def _initialize_channels(self) -> None:
        """Initialize notification channels"""
        try:
            # Email channel
            from .channels.email import EmailChannel
            self._channels['email'] = EmailChannel(self.config)
            
            # SMS channel
            from .channels.sms import SMSChannel
            self._channels['sms'] = SMSChannel(self.config)
            
            # Push notification channel
            from .channels.push import PushChannel
            self._channels['push'] = PushChannel(self.config)
            
            # Initialize all channels
            for channel in self._channels.values():
                await channel.initialize()
                
        except Exception as e:
            raise AlertError(f"Channel initialization failed: {str(e)}")

    async def _load_rules(self) -> None:
        """Load alert rules from storage"""
        try:
            rules_file = self._storage_path / 'rules.json'
            if rules_file.exists():
                with open(rules_file, 'r') as f:
                    self._rules = json.load(f)
        except Exception as e:
            raise AlertError(f"Rules loading failed: {str(e)}")

    async def _save_rules(self) -> None:
        """Save alert rules to storage"""
        try:
            rules_file = self._storage_path / 'rules.json'
            with open(rules_file, 'w') as f:
                json.dump(self._rules, f, indent=2)
        except Exception as e:
            raise AlertError(f"Rules saving failed: {str(e)}")

    async def _store_alert(self, alert: Dict) -> None:
        """Store alert in database"""
        try:
            await self.app.db.alerts.insert_one(alert)
        except Exception as e:
            self.logger.error(f"Alert storage error: {str(e)}")

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        import uuid
        return str(uuid.uuid4())

    def _start_background_tasks(self) -> None:
        """Start background tasks"""
        asyncio.create_task(self._alert_processor())
        asyncio.create_task(self._cleanup_task())

    async def _alert_processor(self) -> None:
        """Background alert processing task"""
        while True:
            try:
                await self._process_alerts()
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Alert processor error: {str(e)}")
                await asyncio.sleep(1)

    async def _cleanup_task(self) -> None:
        """Cleanup old alerts task"""
        while True:
            try:
                # Cleanup alerts older than 30 days
                threshold = datetime.utcnow().timestamp() - (30 * 24 * 3600)
                await self.app.db.alerts.delete_many({
                    'timestamp': {'$lt': threshold}
                })
                await asyncio.sleep(3600)  # Run hourly
            except Exception as e:
                self.logger.error(f"Cleanup error: {str(e)}")
                await asyncio.sleep(3600)

    async def get_stats(self) -> Dict:
        """Get alert statistics"""
        return self._stats.copy() 