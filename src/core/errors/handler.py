from typing import Dict, List, Optional, Callable, Any, Type
import asyncio
from datetime import datetime
import logging
from dataclasses import dataclass
import traceback
import sys
import json
from pathlib import Path
import aiofiles
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from ..base import BaseComponent
from ..utils.errors import handle_errors

@dataclass
class ErrorConfig:
    """Error handling configuration"""
    name: str
    error_types: List[Type[Exception]]
    max_retries: int = 3
    retry_delay: int = 5
    notify: bool = True
    log_level: str = "ERROR"
    custom_handler: Optional[Callable] = None

class ErrorHandler(BaseComponent):
    """Advanced error handling system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._handlers: Dict[Type[Exception], Callable] = {}
        self._error_hooks: List[Callable] = []
        self._error_queue: asyncio.Queue = asyncio.Queue()
        self._include_traceback = self.config.get(
            'errors.include_traceback',
            False
        )
        self._error_codes: Dict[Type[Exception], int] = {}
        self.logger = logging.getLogger('ErrorHandler')
        self._error_log: Path = Path(config.get('error_log', 'errors.log'))
        self._notification_callbacks: List[Callable] = []
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup error logging"""
        try:
            # Ensure error log directory exists
            self._error_log.parent.mkdir(parents=True, exist_ok=True)
            
            # Setup file handler
            file_handler = logging.FileHandler(self._error_log)
            file_handler.setLevel(logging.ERROR)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            self.logger.error(f"Error logging setup failed: {str(e)}")

    async def initialize(self) -> None:
        """Initialize error handler"""
        # Start error processor
        self.add_cleanup_task(
            asyncio.create_task(self._process_errors())
        )
        
        # Register default handlers
        self.register_handler(
            Exception,
            self._handle_default_error
        )

    async def cleanup(self) -> None:
        """Cleanup error handling resources"""
        self._handlers.clear()
        self._error_hooks.clear()
        
        # Clear error queue
        while not self._error_queue.empty():
            try:
                self._error_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    def register_handler(self,
                        exception_type: Type[Exception],
                        handler: Callable) -> None:
        """Register error handler"""
        self._handlers[exception_type] = handler

    def register_error_hook(self,
                          hook: Callable) -> None:
        """Register error processing hook"""
        self._error_hooks.append(hook)

    def set_error_code(self,
                      exception_type: Type[Exception],
                      code: int) -> None:
        """Set HTTP error code for exception type"""
        self._error_codes[exception_type] = code

    @handle_errors(logger=None)
    async def handle_error(self,
                          error: Exception,
                          request: Optional[Request] = None) -> Response:
        """Handle application error"""
        # Find appropriate handler
        handler = self._get_handler(error)
        
        # Process error
        await self._error_queue.put({
            'error': error,
            'request': request,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Generate response
        return await handler(error, request)

    async def log_error(self,
                       error: Exception,
                       context: Optional[Dict] = None) -> None:
        """Log error without handling"""
        await self._error_queue.put({
            'error': error,
            'context': context,
            'timestamp': datetime.utcnow().isoformat()
        })

    def format_error(self,
                    error: Exception,
                    include_traceback: Optional[bool] = None) -> Dict:
        """Format error for response"""
        error_type = type(error).__name__
        
        response = {
            'error': error_type,
            'message': str(error),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if include_traceback or (
            include_traceback is None and
            self._include_traceback
        ):
            response['traceback'] = self._format_traceback(error)
            
        return response

    def _get_handler(self,
                    error: Exception) -> Callable:
        """Get appropriate error handler"""
        for error_type, handler in self._handlers.items():
            if isinstance(error, error_type):
                return handler
                
        return self._handlers[Exception]

    async def _handle_default_error(self,
                                  error: Exception,
                                  request: Optional[Request] = None) -> Response:
        """Default error handler"""
        status_code = self._get_status_code(error)
        
        return JSONResponse(
            status_code=status_code,
            content=self.format_error(error)
        )

    def _get_status_code(self,
                        error: Exception) -> int:
        """Get HTTP status code for error"""
        for error_type, code in self._error_codes.items():
            if isinstance(error, error_type):
                return code
                
        return 500

    def _format_traceback(self,
                         error: Exception) -> List[str]:
        """Format exception traceback"""
        return traceback.format_exception(
            type(error),
            error,
            error.__traceback__
        )

    async def _process_errors(self) -> None:
        """Process error queue"""
        while True:
            try:
                error_info = await self._error_queue.get()
                
                # Log error
                logger = self.app.get_component('log_manager')
                if logger:
                    log = logger.get_logger('errors')
                    log.error(
                        f"Application error: {error_info['error']}",
                        exc_info=error_info['error']
                    )
                    
                # Execute error hooks
                for hook in self._error_hooks:
                    try:
                        await hook(error_info)
                    except Exception as e:
                        print(f"Error hook failed: {str(e)}")
                        
                self._error_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing failed: {str(e)}")
                await asyncio.sleep(1)

    def add_notification_callback(self,
                                callback: Callable[[Dict], None]) -> None:
        """Add error notification callback"""
        self._notification_callbacks.append(callback)

    async def handle_error(self,
                          error: Exception,
                          context: Optional[Dict] = None) -> None:
        """Handle system error"""
        try:
            # Find matching handler
            handler = self._find_handler(error)
            if not handler:
                # Use default handling
                await self._default_error_handling(error, context)
                return
                
            # Update error count
            self._error_counts[handler.name] += 1
            
            # Log error
            log_level = getattr(logging, handler.log_level.upper())
            self.logger.log(log_level, 
                          f"Error in {handler.name}: {str(error)}",
                          exc_info=True)
            
            # Record error details
            await self._record_error(handler.name, error, context)
            
            # Notify if configured
            if handler.notify:
                await self._notify_error(handler.name, error, context)
                
            # Execute custom handler if provided
            if handler.custom_handler:
                try:
                    await handler.custom_handler(error, context)
                except Exception as e:
                    self.logger.error(
                        f"Custom handler failed: {str(e)}"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error handling failed: {str(e)}")

    def retry(self,
             handler_name: str,
             max_retries: Optional[int] = None,
             retry_delay: Optional[int] = None) -> Callable:
        """Retry decorator for error handling"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                handler = self._handlers.get(handler_name)
                if not handler:
                    return await func(*args, **kwargs)
                    
                retries = max_retries or handler.max_retries
                delay = retry_delay or handler.retry_delay
                
                for attempt in range(retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except tuple(handler.error_types) as e:
                        if attempt == retries:
                            raise
                            
                        await self.handle_error(e, {
                            "attempt": attempt + 1,
                            "max_retries": retries,
                            "function": func.__name__
                        })
                        
                        await asyncio.sleep(delay)
                        
            return wrapper
        return decorator

    async def get_error_stats(self) -> Dict:
        """Get error statistics"""
        try:
            stats = {
                "total_errors": sum(self._error_counts.values()),
                "handlers": {
                    name: {
                        "error_count": count,
                        "config": {
                            "max_retries": handler.max_retries,
                            "retry_delay": handler.retry_delay,
                            "notify": handler.notify,
                            "log_level": handler.log_level
                        }
                    }
                    for name, (handler, count) in zip(
                        self._handlers.keys(),
                        self._error_counts.items()
                    )
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get error stats: {str(e)}")
            return {}

    def _find_handler(self, error: Exception) -> Optional[ErrorConfig]:
        """Find matching error handler"""
        for handler in self._handlers.values():
            if any(isinstance(error, t) for t in handler.error_types):
                return handler
        return None

    async def _default_error_handling(self,
                                    error: Exception,
                                    context: Optional[Dict] = None) -> None:
        """Default error handling"""
        self.logger.error(f"Unhandled error: {str(error)}", exc_info=True)
        await self._record_error("default", error, context)

    async def _record_error(self,
                           handler_name: str,
                           error: Exception,
                           context: Optional[Dict] = None) -> None:
        """Record error details"""
        try:
            error_details = {
                "timestamp": datetime.utcnow().isoformat(),
                "handler": handler_name,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "context": context or {}
            }
            
            async with aiofiles.open(self._error_log, 'a') as f:
                await f.write(json.dumps(error_details) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error recording failed: {str(e)}")

    async def _notify_error(self,
                           handler_name: str,
                           error: Exception,
                           context: Optional[Dict] = None) -> None:
        """Notify error to callbacks"""
        notification = {
            "timestamp": datetime.utcnow().isoformat(),
            "handler": handler_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        for callback in self._notification_callbacks:
            try:
                await callback(notification)
            except Exception as e:
                self.logger.error(
                    f"Error notification failed: {str(e)}"
                ) 