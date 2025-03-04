from typing import Dict, Set, Optional, Union
import asyncio
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from ..base import BaseComponent
from ..utils.errors import WebSocketError

class WebSocketManager(BaseComponent):
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # Active connections
        self._connections: Dict[str, Dict[str, WebSocket]] = {
            'camera': {},      # Camera feed subscribers
            'alerts': {},      # Alert notification subscribers
            'recognition': {}  # Face recognition subscribers
        }
        
        # Connection settings
        self._max_connections = config.get('websocket.max_connections', 100)
        self._ping_interval = config.get('websocket.ping_interval', 30)
        
        # Message queue
        self._message_queue: asyncio.Queue = asyncio.Queue()
        
        # Performance tracking
        self._stats = {
            'active_connections': 0,
            'messages_sent': 0,
            'bytes_transferred': 0
        }

    async def connect(self,
                     websocket: WebSocket,
                     client_id: str,
                     subscription: str) -> None:
        """Accept new WebSocket connection"""
        try:
            # Check connection limit
            total_connections = sum(
                len(conns) for conns in self._connections.values()
            )
            if total_connections >= self._max_connections:
                raise WebSocketError("Maximum connections reached")
            
            # Accept connection
            await websocket.accept()
            
            # Add to subscribers
            if subscription not in self._connections:
                raise WebSocketError(f"Invalid subscription: {subscription}")
            
            self._connections[subscription][client_id] = websocket
            
            # Update statistics
            self._stats['active_connections'] = total_connections + 1
            
            # Start client handler
            asyncio.create_task(
                self._handle_client(websocket, client_id, subscription)
            )
            
        except Exception as e:
            raise WebSocketError(f"Connection failed: {str(e)}")

    async def disconnect(self,
                        client_id: str,
                        subscription: str) -> None:
        """Handle client disconnection"""
        try:
            if (subscription in self._connections and 
                client_id in self._connections[subscription]):
                # Remove connection
                del self._connections[subscription][client_id]
                
                # Update statistics
                total_connections = sum(
                    len(conns) for conns in self._connections.values()
                )
                self._stats['active_connections'] = total_connections
                
        except Exception as e:
            self.logger.error(f"Disconnect error: {str(e)}")

    async def broadcast(self,
                       subscription: str,
                       message: Dict) -> None:
        """Broadcast message to subscribers"""
        try:
            if subscription not in self._connections:
                raise WebSocketError(f"Invalid subscription: {subscription}")
            
            # Add message to queue
            await self._message_queue.put({
                'subscription': subscription,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            raise WebSocketError(f"Broadcast failed: {str(e)}")

    async def _handle_client(self,
                           websocket: WebSocket,
                           client_id: str,
                           subscription: str) -> None:
        """Handle client connection"""
        try:
            while True:
                try:
                    # Receive message (ping/pong or commands)
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    # Handle message
                    if data.get('type') == 'ping':
                        await websocket.send_text(
                            json.dumps({'type': 'pong'})
                        )
                    else:
                        await self._handle_message(
                            client_id,
                            subscription,
                            data
                        )
                    
                except WebSocketDisconnect:
                    await self.disconnect(client_id, subscription)
                    break
                    
                except Exception as e:
                    self.logger.error(f"Client handler error: {str(e)}")
                    await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.error(f"Client handler failed: {str(e)}")
            await self.disconnect(client_id, subscription)

    async def _handle_message(self,
                            client_id: str,
                            subscription: str,
                            message: Dict) -> None:
        """Handle client message"""
        try:
            # Handle subscription-specific messages
            if subscription == 'camera':
                await self._handle_camera_message(client_id, message)
            elif subscription == 'alerts':
                await self._handle_alert_message(client_id, message)
            elif subscription == 'recognition':
                await self._handle_recognition_message(client_id, message)
            
        except Exception as e:
            self.logger.error(f"Message handler error: {str(e)}")

    async def _message_processor(self) -> None:
        """Process message queue"""
        while True:
            try:
                # Get message from queue
                message = await self._message_queue.get()
                
                # Get subscribers
                subscribers = self._connections[message['subscription']]
                
                # Send to all subscribers
                for client_id, websocket in subscribers.items():
                    try:
                        await websocket.send_text(
                            json.dumps(message['message'])
                        )
                        
                        # Update statistics
                        self._stats['messages_sent'] += 1
                        self._stats['bytes_transferred'] += len(
                            json.dumps(message['message'])
                        )
                        
                    except Exception as e:
                        self.logger.error(
                            f"Failed to send to {client_id}: {str(e)}"
                        )
                        await self.disconnect(
                            client_id,
                            message['subscription']
                        )
                
            except Exception as e:
                self.logger.error(f"Message processor error: {str(e)}")
                await asyncio.sleep(1)

    async def _handle_camera_message(self,
                                   client_id: str,
                                   message: Dict) -> None:
        """Handle camera-related message"""
        try:
            command = message.get('command')
            
            if command == 'subscribe':
                # Subscribe to specific camera
                camera_id = message.get('camera_id')
                if camera_id:
                    await self.app.vision.subscribe_camera(
                        camera_id,
                        client_id
                    )
            
            elif command == 'unsubscribe':
                # Unsubscribe from camera
                camera_id = message.get('camera_id')
                if camera_id:
                    await self.app.vision.unsubscribe_camera(
                        camera_id,
                        client_id
                    )
            
        except Exception as e:
            self.logger.error(f"Camera message handler error: {str(e)}")

    async def _handle_alert_message(self,
                                  client_id: str,
                                  message: Dict) -> None:
        """Handle alert-related message"""
        try:
            command = message.get('command')
            
            if command == 'acknowledge':
                # Acknowledge alert
                alert_id = message.get('alert_id')
                notes = message.get('notes')
                
                if alert_id:
                    await self.app.alerts.acknowledge_alert(
                        alert_id,
                        client_id,
                        notes
                    )
            
        except Exception as e:
            self.logger.error(f"Alert message handler error: {str(e)}")

    async def _handle_recognition_message(self,
                                        client_id: str,
                                        message: Dict) -> None:
        """Handle recognition-related message"""
        try:
            command = message.get('command')
            
            if command == 'verify':
                # Verify face match
                match_id = message.get('match_id')
                verified = message.get('verified', False)
                
                if match_id:
                    await self.app.recognition.verify_match(
                        match_id,
                        verified,
                        client_id
                    )
            
        except Exception as e:
            self.logger.error(f"Recognition message handler error: {str(e)}")

    async def initialize(self) -> None:
        """Initialize WebSocket manager"""
        try:
            # Start message processor
            asyncio.create_task(self._message_processor())
            
        except Exception as e:
            raise WebSocketError(f"Initialization failed: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup WebSocket manager"""
        try:
            # Close all connections
            for subscription in self._connections:
                for client_id in list(self._connections[subscription].keys()):
                    await self.disconnect(client_id, subscription)
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get WebSocket statistics"""
        return self._stats.copy() 