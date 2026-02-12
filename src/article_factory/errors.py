"""Error handling utilities for Article Factory.

Provides rate limiting and circuit breaker patterns for API resilience.
"""
import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Rate limiter for NotebookLM API calls.
    
    Ensures we don't exceed API rate limits by:
    - Limiting concurrent requests (max_concurrent)
    - Enforcing minimum time between calls (min_interval)
    """
    
    max_concurrent: int = 3
    min_interval: int = 120  # seconds between calls
    
    _semaphore: asyncio.Semaphore = field(default_factory=asyncio.Semaphore)
    _last_call: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    def __post_init__(self):
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def acquire(self) -> bool:
        """Acquire permission to make API call.
        
        Blocks if:
        - Too many concurrent calls active
        - Less than min_interval seconds since last call
        """
        await self._semaphore.acquire()
        async with self._lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self._last_call
            if time_since_last < self.min_interval:
                # Wait for minimum interval
                await asyncio.sleep(self.min_interval - time_since_last)
            self._last_call = asyncio.get_event_loop().time()
        return True
    
    def release(self):
        """Release semaphore after API call."""
        self._semaphore.release()


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitOpenError(Exception):
    """Circuit breaker is open - calls are blocked."""
    pass


@dataclass
class CircuitBreaker:
    """Circuit breaker for API failures.
    
    Prevents cascade failures by:
    - Tracking consecutive failures
    - Opening circuit after failure_threshold failures
    - Attempting recovery after recovery_timeout
    - Allowing test calls in half_open state
    """
    
    failure_threshold: int = 5
    recovery_timeout: int = 300  # 5 minutes
    
    _state: CircuitState = CircuitState.CLOSED
    _failure_count: int = 0
    _last_failure: Optional[datetime] = None
    _recovery_task: Optional[asyncio.Task] = None
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func
            
        Raises:
            CircuitOpenError: If circuit is open
            Exception: Any exception from func
        """
        if self._state == CircuitState.OPEN:
            raise CircuitOpenError(
                f"Circuit is open - {self._failure_count} consecutive failures. "
                f"Try again in {self.recovery_timeout}s"
            )
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """Handle successful call - reset failure count."""
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._recovery_task = None
    
    async def _on_failure(self):
        """Handle failed call - increment counter, possibly open circuit."""
        self._failure_count += 1
        self._last_failure = datetime.now()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            # Schedule recovery check
            self._recovery_task = asyncio.create_task(self._try_recover())
    
    async def _try_recover(self):
        """Try to close circuit after timeout."""
        await asyncio.sleep(self.recovery_timeout)
        self._state = CircuitState.HALF_OPEN


# Global instances for module-level access
rate_limiter = RateLimiter(max_concurrent=3, min_interval=120)
circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)
