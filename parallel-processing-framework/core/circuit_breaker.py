"""
Circuit breaker implementation for fault tolerance
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Union, List
from enum import Enum
from dataclasses import dataclass
import functools

from .interfaces import ICircuitBreaker
from config.settings import settings

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    half_open_max_calls: int = 3
    expected_exception: type = Exception
    success_threshold: int = 2  # consecutive successes needed to close from half-open


class CircuitBreakerStats:
    """Circuit breaker statistics"""
    
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.state_changes = 0
        self.total_open_time = 0.0
        self.last_state_change: Optional[datetime] = None
    
    def record_success(self):
        """Record a successful call"""
        self.total_calls += 1
        self.successful_calls += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success_time = datetime.utcnow()
    
    def record_failure(self):
        """Record a failed call"""
        self.total_calls += 1
        self.failed_calls += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = datetime.utcnow()
    
    def record_state_change(self, new_state: CircuitState):
        """Record a state change"""
        now = datetime.utcnow()
        if self.last_state_change:
            time_in_previous_state = (now - self.last_state_change).total_seconds()
            # If previous state was OPEN, add to total open time
            if hasattr(self, '_previous_state') and self._previous_state == CircuitState.OPEN:
                self.total_open_time += time_in_previous_state
        
        self.state_changes += 1
        self.last_state_change = now
        self._previous_state = new_state
    
    def get_failure_rate(self) -> float:
        """Get failure rate (0.0 to 1.0)"""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls
    
    def get_success_rate(self) -> float:
        """Get success rate (0.0 to 1.0)"""
        return 1.0 - self.get_failure_rate()


class AsyncCircuitBreaker(ICircuitBreaker):
    """Async circuit breaker implementation"""
    
    def __init__(self, 
                 name: str,
                 config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig(
            failure_threshold=settings.processing.failure_threshold,
            recovery_timeout=settings.processing.recovery_timeout,
            half_open_max_calls=settings.processing.half_open_max_calls
        )
        
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
        
        # Event hooks
        self.on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None
        self.on_failure: Optional[Callable[[Exception], None]] = None
        self.on_success: Optional[Callable[[], None]] = None
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection"""
        async with self._lock:
            # Check if we should allow the call
            if not await self._should_allow_call():
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
        
        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)
            
            # Record success
            await self._record_success()
            return result
            
        except self.config.expected_exception as e:
            # Record failure
            await self._record_failure(e)
            raise
    
    async def _should_allow_call(self) -> bool:
        """Check if a call should be allowed based on circuit state"""
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self.stats.last_failure_time and 
                datetime.utcnow() - self.stats.last_failure_time > 
                timedelta(seconds=self.config.recovery_timeout)):
                await self._change_state(CircuitState.HALF_OPEN)
                self.half_open_calls = 0
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited calls to test recovery
            if self.half_open_calls < self.config.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return False
    
    async def _record_success(self):
        """Record a successful call and update state if needed"""
        async with self._lock:
            self.stats.record_success()
            
            if self.on_success:
                try:
                    self.on_success()
                except Exception as e:
                    logger.warning(f"Error in success callback: {e}")
            
            # State transitions on success
            if self.state == CircuitState.HALF_OPEN:
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    await self._change_state(CircuitState.CLOSED)
                    self.half_open_calls = 0
    
    async def _record_failure(self, exception: Exception):
        """Record a failed call and update state if needed"""
        async with self._lock:
            self.stats.record_failure()
            
            if self.on_failure:
                try:
                    self.on_failure(exception)
                except Exception as e:
                    logger.warning(f"Error in failure callback: {e}")
            
            # State transitions on failure
            if self.state == CircuitState.CLOSED:
                if self.stats.consecutive_failures >= self.config.failure_threshold:
                    await self._change_state(CircuitState.OPEN)
            
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open state goes back to open
                await self._change_state(CircuitState.OPEN)
                self.half_open_calls = 0
    
    async def _change_state(self, new_state: CircuitState):
        """Change circuit breaker state"""
        old_state = self.state
        self.state = new_state
        self.stats.record_state_change(new_state)
        
        logger.info(f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}")
        
        if self.on_state_change:
            try:
                self.on_state_change(old_state, new_state)
            except Exception as e:
                logger.warning(f"Error in state change callback: {e}")
    
    def get_state(self) -> str:
        """Get current circuit breaker state"""
        return self.state.value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'total_calls': self.stats.total_calls,
            'successful_calls': self.stats.successful_calls,
            'failed_calls': self.stats.failed_calls,
            'consecutive_failures': self.stats.consecutive_failures,
            'consecutive_successes': self.stats.consecutive_successes,
            'failure_rate': self.stats.get_failure_rate(),
            'success_rate': self.stats.get_success_rate(),
            'last_failure_time': self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            'last_success_time': self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            'state_changes': self.stats.state_changes,
            'total_open_time': self.stats.total_open_time,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'half_open_max_calls': self.config.half_open_max_calls,
                'success_threshold': self.config.success_threshold
            }
        }
    
    async def reset(self):
        """Reset circuit breaker to closed state"""
        async with self._lock:
            old_state = self.state
            self.state = CircuitState.CLOSED
            self.stats = CircuitBreakerStats()
            self.half_open_calls = 0
            logger.info(f"Circuit breaker '{self.name}' reset from {old_state.value} to CLOSED")
    
    async def force_open(self):
        """Force circuit breaker to open state"""
        async with self._lock:
            await self._change_state(CircuitState.OPEN)
    
    async def force_half_open(self):
        """Force circuit breaker to half-open state"""
        async with self._lock:
            await self._change_state(CircuitState.HALF_OPEN)
            self.half_open_calls = 0


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, AsyncCircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def get_breaker(self, 
                         name: str, 
                         config: Optional[CircuitBreakerConfig] = None) -> AsyncCircuitBreaker:
        """Get or create a circuit breaker"""
        async with self._lock:
            if name not in self.breakers:
                self.breakers[name] = AsyncCircuitBreaker(name, config)
            return self.breakers[name]
    
    async def remove_breaker(self, name: str) -> bool:
        """Remove a circuit breaker"""
        async with self._lock:
            return self.breakers.pop(name, None) is not None
    
    def list_breakers(self) -> List[str]:
        """List all circuit breaker names"""
        return list(self.breakers.keys())
    
    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all circuit breakers"""
        stats = {}
        for name, breaker in self.breakers.items():
            stats[name] = breaker.get_stats()
        return stats
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            await breaker.reset()


# Global registry instance
_registry = CircuitBreakerRegistry()


def circuit_breaker(name: str, 
                   config: Optional[CircuitBreakerConfig] = None):
    """Decorator for applying circuit breaker to functions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = await _registry.get_breaker(name, config)
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


async def get_circuit_breaker(name: str, 
                            config: Optional[CircuitBreakerConfig] = None) -> AsyncCircuitBreaker:
    """Get a circuit breaker from the global registry"""
    return await _registry.get_breaker(name, config)


async def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get stats for all circuit breakers"""
    return await _registry.get_all_stats()


# Example usage patterns
class CircuitBreakerManager:
    """High-level manager for circuit breakers"""
    
    def __init__(self):
        self.registry = CircuitBreakerRegistry()
    
    async def create_external_service_breaker(self, 
                                            service_name: str,
                                            failure_threshold: int = 5,
                                            recovery_timeout: int = 60) -> AsyncCircuitBreaker:
        """Create a circuit breaker for external service calls"""
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=3,
            expected_exception=Exception
        )
        
        breaker = await self.registry.get_breaker(f"service_{service_name}", config)
        
        # Set up callbacks for monitoring
        def on_state_change(old_state: CircuitState, new_state: CircuitState):
            logger.warning(f"Service '{service_name}' circuit breaker: {old_state.value} -> {new_state.value}")
        
        def on_failure(exception: Exception):
            logger.error(f"Service '{service_name}' call failed: {exception}")
        
        breaker.on_state_change = on_state_change
        breaker.on_failure = on_failure
        
        return breaker
    
    async def create_resource_breaker(self, 
                                    resource_name: str,
                                    failure_threshold: int = 10,
                                    recovery_timeout: int = 30) -> AsyncCircuitBreaker:
        """Create a circuit breaker for resource-intensive operations"""
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=5,
            expected_exception=(MemoryError, OSError, RuntimeError)
        )
        
        return await self.registry.get_breaker(f"resource_{resource_name}", config)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of all circuit breakers"""
        all_stats = await self.registry.get_all_stats()
        
        total_breakers = len(all_stats)
        open_breakers = sum(1 for stats in all_stats.values() if stats['state'] == 'open')
        half_open_breakers = sum(1 for stats in all_stats.values() if stats['state'] == 'half_open')
        
        overall_failure_rate = 0.0
        if all_stats:
            overall_failure_rate = sum(stats['failure_rate'] for stats in all_stats.values()) / total_breakers
        
        return {
            'total_breakers': total_breakers,
            'open_breakers': open_breakers,
            'half_open_breakers': half_open_breakers,
            'closed_breakers': total_breakers - open_breakers - half_open_breakers,
            'overall_failure_rate': overall_failure_rate,
            'health_status': 'unhealthy' if open_breakers > 0 else 'healthy',
            'individual_stats': all_stats
        }