from typing import Dict, Any, Callable, Awaitable, Optional
import asyncio
import json
from datetime import datetime
from ..base import BaseComponent
from ..utils.errors import handle_errors

class EventHandler(BaseComponent):
    """WebSocket event handling system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._handlers: Dict[str, Dict[str, Callable]] = {}
        self._middlewares: Dict[str, Callable] = {}
        self._error_handlers: Dict[str, Callable] = {}
        self._default_error_handler: Optional[Callable] = None

    async def initialize(self) -> None:
        """Initialize event handler"""
        # Register core event handlers
        self.register_handler('system', 'ping', self._handle_ping)
        self.register_handler('system', 'error', self._handle_error)

    async def cleanup(self) -> None:
        """Cleanup event handler resources"""
        self._handlers.clear()
        self._middlewares.clear()
        self._error_handlers.clear()

    def register_handler(self,
                        namespace: str,
                        event: str,
                        handler: Callable[[str, str, Any], Awaitable[None]]) -> None:
        """Register event handler"""
        if namespace not in self._handlers:
            self._handlers[namespace] = {}
        self._handlers[namespace][event] = handler

    def register_middleware(self,
                          namespace: str,
                          middleware: Callable[[str, str, Any], Awaitable[bool]]) -> None:
        """Register event middleware"""
        self._middlewares[namespace] = middleware

    def register_error_handler(self,
                             event: str,
                             handler: Callable[[Exception, str, str, Any], Awaitable[None]]) -> None:
        """Register error handler"""
        self._error_handlers[event] = handler

    def set_default_error_handler(self,
                                handler: Callable[[Exception, str, str, Any], Awaitable[None]]) -> None:
        """Set default error handler"""
        self._default_error_handler = handler

    @handle_errors(logger=None)
    async def handle_event(self,
                         group: str,
                         connection_id: str,
                         message: Dict) -> None:
        """Handle WebSocket event"""
        namespace = message.get('namespace', 'default')
        event = message.get('event')
        payload = message.get('payload')
        
        if not event:
            return
            
        # Check middleware
        if namespace in self._middlewares:
            try:
                allowed = await self._middlewares[namespace](
                    group,
                    connection_id,
                    message
                )
                if not allowed:
                    return
            except Exception as e:
                await self._handle_middleware_error(
                    e,
                    group,
                    connection_id,
                    message
                )
                return
                
        # Find handler
        handler = None
        if namespace in self._handlers:
            handler = self._handlers[namespace].get(event)
            
        if not handler:
            self.logger.warning(
                f"No handler for event: {namespace}.{event}"
            )
            return
            
        # Execute handler
        try:
            await handler(group, connection_id, payload)
        except Exception as e:
            await self._handle_event_error(
                e,
                group,
                connection_id,
                message
            )

    async def _handle_ping(self,
                          group: str,
                          connection_id: str,
                          payload: Any) -> None:
        """Handle ping event"""
        ws_manager = self.app.get_component('websocket_manager')
        if not ws_manager:
            return
            
        await ws_manager.send_message(
            group,
            connection_id,
            {
                'event': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    async def _handle_error(self,
                          group: str,
                          connection_id: str,
                          payload: Any) -> None:
        """Handle error event"""
        self.logger.error(
            f"Client error: {group}/{connection_id} - {payload}"
        )

    async def _handle_event_error(self,
                                error: Exception,
                                group: str,
                                connection_id: str,
                                message: Dict) -> None:
        """Handle event execution error"""
        event = message.get('event')
        
        # Find error handler
        handler = self._error_handlers.get(event)
        if not handler:
            handler = self._default_error_handler
            
        if handler:
            try:
                await handler(error, group, connection_id, message)
            except Exception as e:
                self.logger.error(
                    f"Error handler failed: {str(e)}"
                )
        else:
            self.logger.error(
                f"Event error: {event} - {str(error)}"
            )

    async def _handle_middleware_error(self,
                                     error: Exception,
                                     group: str,
                                     connection_id: str,
                                     message: Dict) -> None:
        """Handle middleware execution error"""
        self.logger.error(
            f"Middleware error: {group}/{connection_id} - {str(error)}"
        ) 