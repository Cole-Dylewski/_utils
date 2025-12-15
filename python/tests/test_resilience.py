"""
Tests for resilience patterns (retry, circuit breaker, rate limiter).
"""

import asyncio
import time
from unittest.mock import patch

import pytest
from utils.resilience import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    RateLimiter,
    async_retry,
    async_timeout,
    retry,
)


@pytest.mark.unit
class TestRetry:
    """Test retry decorator."""

    def test_retry_success(self):
        """Test retry with successful operation."""
        call_count = 0

        @retry(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_with_failure_then_success(self):
        """Test retry that succeeds after failures."""
        call_count = 0

        @retry(max_attempts=3, delay=0.1)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 2

    def test_retry_exhausted(self):
        """Test retry that exhausts all attempts."""
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fails()
        assert call_count == 3

    def test_retry_specific_exception(self):
        """Test retry with specific exception types."""
        call_count = 0

        @retry(max_attempts=2, exceptions=(ValueError,))
        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Value error")

        with pytest.raises(ValueError, match="Value error"):
            raises_value_error()
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_retry(self):
        """Test async retry decorator."""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.1)
        async def async_flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = await async_flaky_func()
        assert result == "success"
        assert call_count == 2


@pytest.mark.unit
class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_circuit_breaker_closed(self):
        """Test circuit breaker in closed state."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)

        def successful_func():
            return "success"

        result = breaker.call(successful_func)
        assert result == "success"
        assert breaker.state.value == "closed"

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)

        def failing_func():
            raise ValueError("Failure")

        # First failure
        with pytest.raises(ValueError, match="Failure"):
            breaker.call(failing_func)
        assert breaker.failure_count == 1
        assert breaker.state.value == "closed"

        # Second failure - should open
        with pytest.raises(ValueError, match="Failure"):
            breaker.call(failing_func)
        assert breaker.failure_count == 2
        assert breaker.state.value == "open"

    def test_circuit_breaker_open_raises_error(self):
        """Test that open circuit breaker raises error."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1.0)
        # Properly set the circuit breaker to open state
        breaker.state = CircuitState.OPEN
        breaker.last_failure_time = time.time() - 0.5  # Set recent failure time

        def any_func():
            return "success"

        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(any_func)

    def test_circuit_breaker_reset_on_success(self):
        """Test circuit breaker resets on success."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        breaker.failure_count = 1

        def successful_func():
            return "success"

        result = breaker.call(successful_func)
        assert result == "success"
        assert breaker.failure_count == 0
        assert breaker.state.value == "closed"


@pytest.mark.unit
class TestRateLimiter:
    """Test rate limiter."""

    def test_rate_limiter_acquire(self):
        """Test rate limiter acquire."""
        limiter = RateLimiter(max_calls=2, period=1.0)

        assert limiter.acquire() is True
        assert limiter.acquire() is True
        assert limiter.acquire() is False  # Rate limit exceeded

    @patch("utils.resilience.time.sleep")
    def test_rate_limiter_wait(self, mock_sleep):
        """Test rate limiter wait functionality."""
        limiter = RateLimiter(max_calls=1, period=0.1)

        assert limiter.acquire() is True
        assert limiter.acquire() is False

        # wait_if_needed will wait and acquire internally
        limiter.wait_if_needed()
        # wait_if_needed already acquired, so clear calls to test next acquire
        limiter.calls.clear()
        # After clearing, should be able to acquire again
        assert limiter.acquire() is True
        mock_sleep.assert_called_once()

    def test_rate_limiter_resets_after_period(self):
        """Test rate limiter resets after period."""
        limiter = RateLimiter(max_calls=1, period=0.1)

        assert limiter.acquire() is True
        assert limiter.acquire() is False

        time.sleep(0.15)
        assert limiter.acquire() is True


@pytest.mark.unit
class TestTimeout:
    """Test timeout decorators."""

    @pytest.mark.asyncio
    async def test_async_timeout_success(self):
        """Test async timeout with successful operation."""

        @async_timeout(seconds=1.0)
        async def fast_operation():
            await asyncio.sleep(0.1)
            return "success"

        result = await fast_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_timeout_exceeded(self):
        """Test async timeout that exceeds limit."""

        @async_timeout(seconds=0.1)
        async def slow_operation():
            await asyncio.sleep(0.2)
            return "success"

        with pytest.raises(TimeoutError, match="timed out"):
            await slow_operation()

    def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker in half-open state."""
        from utils.resilience import CircuitState

        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        breaker.state = CircuitState.OPEN
        breaker.last_failure_time = 0  # Set to past

        def successful_func():
            return "success"

        # Should transition to half-open and succeed
        result = breaker.call(successful_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_half_open_failure(self):
        """Test circuit breaker in half-open state with failure."""
        from utils.resilience import CircuitState

        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        breaker.state = CircuitState.OPEN
        breaker.last_failure_time = 0  # Set to past

        def failing_func():
            raise ValueError("Failure")

        # Should transition to half-open, fail, and go back to open
        with pytest.raises(ValueError, match="Failure"):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN

    def test_timeout_sync_function(self):
        """Test timeout decorator for sync function (placeholder)."""
        from utils.resilience import timeout

        @timeout(seconds=1.0)
        def fast_operation():
            return "success"

        # Sync timeout is a placeholder, should just execute
        result = fast_operation()
        assert result == "success"

    def test_rate_limiter_wait_if_needed(self):
        """Test rate limiter wait_if_needed functionality."""
        limiter = RateLimiter(max_calls=1, period=0.1)

        assert limiter.acquire() is True
        assert limiter.acquire() is False

        # wait_if_needed will wait and acquire internally
        limiter.wait_if_needed()
        # wait_if_needed already acquired, so clear calls to test next acquire
        limiter.calls.clear()
        # After clearing, should be able to acquire again
        assert limiter.acquire() is True

    def test_circuit_breaker_should_attempt_reset(self):
        """Test circuit breaker reset logic."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        breaker.last_failure_time = None
        assert breaker._should_attempt_reset() is True

        breaker.last_failure_time = 0  # Past time
        assert breaker._should_attempt_reset() is True

        breaker.last_failure_time = time.time()  # Current time
        assert breaker._should_attempt_reset() is False

    def test_circuit_breaker_on_success(self):
        """Test circuit breaker success handler."""
        from utils.resilience import CircuitState

        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        breaker.failure_count = 1
        breaker.state = CircuitState.HALF_OPEN

        breaker._on_success()
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_on_failure(self):
        """Test circuit breaker failure handler."""
        from utils.resilience import CircuitState

        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        breaker.failure_count = 1

        breaker._on_failure()
        assert breaker.failure_count == 2
        assert breaker.last_failure_time is not None
        assert breaker.state == CircuitState.OPEN
