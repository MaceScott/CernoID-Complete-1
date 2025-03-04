from typing import Dict, Optional, Callable, Any
import asyncio
import time
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import aioredis
from functools import wraps

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitConfig:
    """Circuit breaker configuration"""
    name: str
    failure_threshold: int
    recovery_timeout: int
    half_open_calls: int
    error_types: Optional[List[Exception]] = None
    namespace: Optional[str] = None

class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('CircuitBreaker')
        self._redis: Optional[aioredis.Redis] = None
        self._circuits: Dict[str, CircuitConfig] = {}
        self._local_state: Dict[str, Dict] = {}
        self._state_change_callbacks: Dict[str, List[Callable]] = {}

    async def initialize(self) -> None:
        """Initialize circuit breaker"""
        try:
            # Connect to Redis
            self._redis = await aioredis.create_redis_pool(
                self.config['redis_url']
            )
            
            self.logger.info("Circuit breaker initialized")
            
        except Exception as e:
            self.logger.error(f"Circuit breaker initialization failed: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup circuit breaker resources"""
        if self._redis:
            self._redis.close()
            await self._redis.wait_closed()
            
        self.logger.info("Circuit breaker cleaned up")

    def register_circuit(self, circuit: CircuitConfig) -> None:
        """Register circuit breaker"""
        self._circuits[circuit.name] = circuit
        self._local_state[circuit.name] = {
            "state": CircuitState.CLOSED,
            "failures": 0,
            "last_failure": None,
            "last_success": None,
            "half_open_calls": 0
        }
        self.logger.info(f"Registered circuit: {circuit.name}")

    def on_state_change(self,
                       circuit_name: str,
                       callback: Callable[[str, CircuitState], None]) -> None:
        """Register state change callback"""
        if circuit_name not in self._state_change_callbacks:
            self._state_change_callbacks[circuit_name] = []
        self._state_change_callbacks[circuit_name].append(callback)

    async def get_circuit_state(self,
                              circuit_name: str) -> Optional[CircuitState]:
        """Get current circuit state"""
        try:
            circuit = self._circuits.get(circuit_name)
            if not circuit:
                raise ValueError(f"Unknown circuit: {circuit_name}")
                
            # Get state from Redis
            state_key = self._build_key(circuit, "state")
            state = await self._redis.get(state_key)
            
            if state:
                return CircuitState(state.decode())
                
            # Use local state as fallback
            return self._local_state[circuit_name]["state"]
            
        except Exception as e:
            self.logger.error(f"Failed to get circuit state: {str(e)}")
            return None

    async def record_success(self, circuit_name: str) -> None:
        """Record successful call"""
        try:
            circuit = self._circuits.get(circuit_name)
            if not circuit:
                raise ValueError(f"Unknown circuit: {circuit_name}")
                
            state = self._local_state[circuit_name]
            current_state = state["state"]
            
            if current_state == CircuitState.HALF_OPEN:
                state["half_open_calls"] += 1
                
                if state["half_open_calls"] >= circuit.half_open_calls:
                    await self._change_state(
                        circuit,
                        CircuitState.CLOSED
                    )
                    
            state["failures"] = 0
            state["last_success"] = time.time()
            
        except Exception as e:
            self.logger.error(f"Failed to record success: {str(e)}")

    async def record_failure(self,
                           circuit_name: str,
                           error: Exception) -> None:
        """Record failed call"""
        try:
            circuit = self._circuits.get(circuit_name)
            if not circuit:
                raise ValueError(f"Unknown circuit: {circuit_name}")
                
            # Check if error type should trigger circuit
            if circuit.error_types and \
               not any(isinstance(error, t) for t in circuit.error_types):
                return
                
            state = self._local_state[circuit_name]
            state["failures"] += 1
            state["last_failure"] = time.time()
            
            if state["failures"] >= circuit.failure_threshold:
                await self._change_state(
                    circuit,
                    CircuitState.OPEN
                )
                
        except Exception as e:
            self.logger.error(f"Failed to record failure: {str(e)}")

    def protect(self, circuit_name: str) -> Callable:
        """Circuit breaker decorator"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                state = await self.get_circuit_state(circuit_name)
                
                if state == CircuitState.OPEN:
                    circuit = self._circuits[circuit_name]
                    local_state = self._local_state[circuit_name]
                    
                    if time.time() - local_state["last_failure"] >= \
                       circuit.recovery_timeout:
                        await self._change_state(
                            circuit,
                            CircuitState.HALF_OPEN
                        )
                    else:
                        raise CircuitBreakerError(
                            f"Circuit {circuit_name} is OPEN"
                        )
                        
                try:
                    result = await func(*args, **kwargs)
                    await self.record_success(circuit_name)
                    return result
                except Exception as e:
                    await self.record_failure(circuit_name, e)
                    raise
                    
            return wrapper
        return decorator

    async def _change_state(self,
                           circuit: CircuitConfig,
                           new_state: CircuitState) -> None:
        """Change circuit state"""
        try:
            state_key = self._build_key(circuit, "state")
            
            # Update Redis
            await self._redis.set(
                state_key,
                new_state.value
            )
            
            # Update local state
            local_state = self._local_state[circuit.name]
            old_state = local_state["state"]
            local_state["state"] = new_state
            
            if new_state == CircuitState.CLOSED:
                local_state["failures"] = 0
                local_state["half_open_calls"] = 0
            elif new_state == CircuitState.HALF_OPEN:
                local_state["half_open_calls"] = 0
                
            # Notify callbacks
            if old_state != new_state:
                for callback in self._state_change_callbacks.get(
                    circuit.name, []
                ):
                    try:
                        callback(circuit.name, new_state)
                    except Exception as e:
                        self.logger.error(
                            f"State change callback failed: {str(e)}"
                        )
                        
            self.logger.info(
                f"Circuit {circuit.name} state changed: {old_state} -> {new_state}"
            )
            
        except Exception as e:
            self.logger.error(f"State change failed: {str(e)}")

    def _build_key(self, circuit: CircuitConfig, suffix: str) -> str:
        """Build Redis key"""
        if circuit.namespace:
            return f"circuit:{circuit.namespace}:{circuit.name}:{suffix}"
        return f"circuit:{circuit.name}:{suffix}"

class CircuitBreakerError(Exception):
    """Circuit breaker error"""
    pass 