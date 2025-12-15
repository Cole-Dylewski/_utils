"""
Resilience patterns for _utils package.

Provides retry, circuit breaker, rate limiting, and timeout utilities.
"""

import asyncio
from collections import deque
from collections.abc import Callable
from enum import Enum
import functools
import time
from typing import Any, Optional, TypeVar, cast

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by stopping requests when a service is failing.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that triggers failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception: Optional[Exception] = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise

            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry failure")

        return wrapper

    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Async retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated async function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Optional[Exception] = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise

            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry failure")

        return wrapper

    return decorator


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.

    Limits the number of operations per time period.
    """

    def __init__(self, max_calls: int, period: float) -> None:
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: deque[float] = deque()

    def acquire(self) -> bool:
        """
        Try to acquire a permit for an operation.

        Returns:
            True if permit acquired, False if rate limit exceeded
        """
        now = time.time()

        # Remove old calls outside the time window
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True

        return False

    def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded."""
        if not self.acquire():
            if self.calls:
                sleep_time = self.period - (time.time() - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.acquire()


def timeout(seconds: float) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Timeout decorator for synchronous functions.

    Args:
        seconds: Timeout in seconds

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # For sync functions, we can't easily implement timeout
            # This is a placeholder - real timeout requires threading
            return func(*args, **kwargs)

        return wrapper

    return decorator


def async_timeout(seconds: float) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Timeout decorator for async functions.

    Args:
        seconds: Timeout in seconds

    Returns:
        Decorated async function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")

        return wrapper

    return decorator
