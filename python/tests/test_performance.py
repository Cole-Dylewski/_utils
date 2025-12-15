"""
Performance and benchmark tests.
"""

import time

import pytest
from utils.cache import cache
from utils.resilience import RateLimiter


@pytest.mark.slow
@pytest.mark.unit
class TestPerformance:
    """Performance and benchmark tests."""

    def test_cache_performance(self, benchmark):
        """Benchmark cache performance."""

        @cache(ttl=10.0)
        def expensive_operation(x):
            time.sleep(0.001)  # Simulate work
            return x * 2

        # First call (cache miss)
        result1 = expensive_operation(5)
        assert result1 == 10

        # Benchmark cached call (cache hit)
        result2 = benchmark(expensive_operation, 5)
        assert result2 == 10

    def test_rate_limiter_performance(self, benchmark):
        """Benchmark rate limiter performance."""
        limiter = RateLimiter(max_calls=1000, period=1.0)

        def acquire_permit():
            return limiter.acquire()

        # Benchmark permit acquisition
        result = benchmark(acquire_permit)
        assert isinstance(result, bool)

    def test_logger_performance(self, benchmark):
        """Benchmark logger performance."""
        from utils.logger import get_logger

        logger = get_logger("test")

        def log_message():
            logger.info("Test message")

        benchmark(log_message)
