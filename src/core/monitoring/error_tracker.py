from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
from collections import defaultdict
import traceback

@dataclass
class ErrorEvent:
    """Error event details"""
    error_type: str
    message: str
    stack_trace: str
    timestamp: datetime
    service: str
    severity: str
    context: Dict

class ErrorTracker:
    """System-wide error tracking and analysis"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('ErrorTracker')
        self._error_threshold = config.get('error_threshold', 0.05)  # 5%
        self._errors: Dict[str, List[ErrorEvent]] = defaultdict(list)
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start error monitoring"""
        self._monitoring_task = asyncio.create_task(self._analyze_error_patterns())
        self.logger.info("Error tracking started")

    async def stop(self) -> None:
        """Stop error monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Error tracking stopped")

    async def track_error(self, error: Exception, service: str, 
                         severity: str = "ERROR", context: Dict = None) -> None:
        """Track new error occurrence"""
        try:
            error_event = ErrorEvent(
                error_type=type(error).__name__,
                message=str(error),
                stack_trace=traceback.format_exc(),
                timestamp=datetime.utcnow(),
                service=service,
                severity=severity,
                context=context or {}
            )
            
            self._errors[service].append(error_event)
            
            # Check error threshold
            if await self._check_error_threshold(service):
                await self._handle_error_threshold_exceeded(service)
                
            # Log error
            self.logger.error(
                f"Error in {service}: {error_event.message}",
                extra={
                    "error_type": error_event.error_type,
                    "service": service,
                    "severity": severity
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error tracking failed: {str(e)}")

    async def get_error_stats(self, 
                            service: Optional[str] = None,
                            time_window: timedelta = timedelta(hours=1)) -> Dict:
        """Get error statistics"""
        try:
            cutoff_time = datetime.utcnow() - time_window
            stats = {}
            
            services = [service] if service else self._errors.keys()
            
            for svc in services:
                recent_errors = [
                    e for e in self._errors[svc]
                    if e.timestamp >= cutoff_time
                ]
                
                error_types = defaultdict(int)
                for error in recent_errors:
                    error_types[error.error_type] += 1
                
                stats[svc] = {
                    "total_errors": len(recent_errors),
                    "error_types": dict(error_types),
                    "error_rate": len(recent_errors) / self.config['request_count'],
                    "most_recent": recent_errors[-1] if recent_errors else None
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error stats calculation failed: {str(e)}")
            raise

    async def _analyze_error_patterns(self) -> None:
        """Analyze error patterns periodically"""
        while True:
            try:
                for service in self._errors:
                    patterns = await self._detect_error_patterns(service)
                    if patterns:
                        await self._report_error_patterns(service, patterns)
                        
                # Clean up old errors
                await self._cleanup_old_errors()
                
                await asyncio.sleep(300)  # Analyze every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error pattern analysis failed: {str(e)}")
                await asyncio.sleep(5)

    async def _detect_error_patterns(self, service: str) -> Dict:
        """Detect patterns in error occurrences"""
        recent_errors = [
            e for e in self._errors[service]
            if e.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ]
        
        patterns = {
            "frequent_errors": self._get_frequent_errors(recent_errors),
            "error_spikes": self._detect_error_spikes(recent_errors),
            "correlated_errors": self._find_error_correlations(recent_errors)
        }
        
        return patterns

    async def _check_error_threshold(self, service: str) -> bool:
        """Check if error rate exceeds threshold"""
        stats = await self.get_error_stats(service)
        return stats[service]['error_rate'] > self._error_threshold

    async def _handle_error_threshold_exceeded(self, service: str) -> None:
        """Handle error threshold exceeded"""
        stats = await self.get_error_stats(service)
        alert_message = (
            f"Error threshold exceeded in {service}\n"
            f"Error rate: {stats[service]['error_rate']:.2%}\n"
            f"Total errors: {stats[service]['total_errors']}\n"
            f"Most common error: {max(stats[service]['error_types'].items(), key=lambda x: x[1])[0]}"
        )
        
        self.logger.warning(alert_message)
        # Implement alert notification system here

    async def _cleanup_old_errors(self) -> None:
        """Clean up old error records"""
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        for service in self._errors:
            self._errors[service] = [
                e for e in self._errors[service]
                if e.timestamp >= cutoff_time
            ]

    @staticmethod
    def _get_frequent_errors(errors: List[ErrorEvent]) -> Dict:
        """Get most frequent error types"""
        error_counts = defaultdict(int)
        for error in errors:
            error_counts[error.error_type] += 1
        return dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def _detect_error_spikes(errors: List[ErrorEvent]) -> List[Dict]:
        """Detect sudden spikes in error rates"""
        if not errors:
            return []
            
        # Group errors by minute
        error_timeline = defaultdict(int)
        for error in errors:
            minute = error.timestamp.replace(second=0, microsecond=0)
            error_timeline[minute] += 1
            
        # Detect spikes
        spikes = []
        baseline = sum(error_timeline.values()) / len(error_timeline)
        
        for minute, count in error_timeline.items():
            if count > baseline * 2:  # Spike threshold
                spikes.append({
                    "timestamp": minute,
                    "count": count,
                    "baseline": baseline
                })
                
        return spikes 