"""
Tests for caching utilities.
"""

import time

import pytest
from utils.cache import clear_cache, get_cache_stats


@pytest.mark.unit
class TestCache:
    """Test cache utilities."""

    def test_cache_decorator_sync(self):
        """Test cache decorator for sync functions."""
        from utils.cache import cache

        call_count = 0

        @cache(ttl=1.0)
        def expensive_operation(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - should execute
        result1 = expensive_operation(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - should use cache
        result2 = expensive_operation(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

        # Different argument - should execute
        result3 = expensive_operation(10)
        assert result3 == 20
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_cache_decorator_async(self):
        """Test cache decorator for async functions."""
        from utils.cache import cache

        call_count = 0

        @cache(ttl=1.0)
        async def expensive_async_operation(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = await expensive_async_operation(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - should use cache
        result2 = await expensive_async_operation(5)
        assert result2 == 10
        assert call_count == 1

    def test_cache_expires_after_ttl(self):
        """Test that cache expires after TTL."""
        from utils.cache import cache

        call_count = 0

        @cache(ttl=0.1)
        def short_ttl_operation(x):
            nonlocal call_count
            call_count += 1
            return x

        # First call
        short_ttl_operation(1)
        assert call_count == 1

        # Second call - should use cache
        short_ttl_operation(1)
        assert call_count == 1

        # Wait for TTL to expire
        time.sleep(0.15)

        # Third call - should execute again
        short_ttl_operation(1)
        assert call_count == 2

    def test_clear_cache(self):
        """Test clearing cache."""
        from utils.cache import cache

        @cache(ttl=10.0)
        def cached_func(x):
            return x

        # Populate cache
        cached_func(1)
        cached_func(2)

        stats_before = get_cache_stats()
        assert stats_before["total_keys"] >= 2

        # Clear cache
        clear_cache()

        stats_after = get_cache_stats()
        assert stats_after["total_keys"] == 0

    def test_clear_cache_with_pattern(self):
        """Test clearing cache with pattern."""
        from utils.cache import cache

        @cache(ttl=10.0, key_prefix="prefix1")
        def func1(x):
            return x

        @cache(ttl=10.0, key_prefix="prefix2")
        def func2(x):
            return x

        # Populate cache
        func1(1)
        func2(1)

        stats_before = get_cache_stats()
        assert stats_before["total_keys"] >= 2

        # Clear only prefix1
        clear_cache("prefix1")

        stats_after = get_cache_stats()
        # Should have fewer keys now
        assert stats_after["total_keys"] < stats_before["total_keys"]

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        stats = get_cache_stats()
        assert "total_keys" in stats
        assert "active_keys" in stats
        assert "expired_keys" in stats
        assert "cache_type" in stats
        assert isinstance(stats["total_keys"], int)
        assert isinstance(stats["active_keys"], int)

    def test_cache_with_key_prefix(self):
        """Test cache decorator with key prefix."""
        from utils.cache import cache

        call_count = 0

        @cache(ttl=10.0, key_prefix="test_prefix")
        def prefixed_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = prefixed_func(5)
        assert result1 == 10
        assert call_count == 1

        result2 = prefixed_func(5)
        assert result2 == 10
        assert call_count == 1  # Should use cache

    @pytest.mark.asyncio
    async def test_cache_with_redis(self):
        """Test cache decorator with Redis (mocked)."""
        from unittest.mock import AsyncMock, MagicMock

        from utils.cache import cache

        mock_redis = MagicMock()
        mock_redis.get_key = AsyncMock(return_value=None)
        mock_redis.set_key = AsyncMock(return_value=None)

        call_count = 0

        @cache(ttl=10.0, use_redis=True, redis_handler=mock_redis)
        async def redis_cached_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result = await redis_cached_func(5)
        assert result == 10
        assert call_count == 1
        mock_redis.get_key.assert_called_once()
        mock_redis.set_key.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_with_redis_hit(self):
        """Test cache decorator with Redis cache hit."""
        from unittest.mock import AsyncMock, MagicMock

        from utils.cache import cache

        mock_redis = MagicMock()
        mock_redis.get_key = AsyncMock(return_value={"value": 10})
        mock_redis.set_key = AsyncMock(return_value=None)

        call_count = 0

        @cache(ttl=10.0, use_redis=True, redis_handler=mock_redis)
        async def redis_cached_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result = await redis_cached_func(5)
        assert result == 10
        assert call_count == 0  # Should use cache
        mock_redis.get_key.assert_called_once()
        mock_redis.set_key.assert_not_called()

    def test_make_cache_key(self):
        """Test cache key generation."""
        from utils.cache import _make_cache_key

        def test_func(a, b):
            return a + b

        key1 = _make_cache_key(test_func, 1, 2)
        key2 = _make_cache_key(test_func, 1, 2)
        key3 = _make_cache_key(test_func, 2, 3)

        assert key1 == key2  # Same args should produce same key
        assert key1 != key3  # Different args should produce different key
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length
