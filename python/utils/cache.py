"""
Caching utilities for _utils package.

Provides caching decorators and utilities using Redis or in-memory storage.
"""

import asyncio
from collections.abc import Callable
import functools
import hashlib
import json
import pickle
from typing import Any, Optional, TypeVar

try:
    from utils.redis import RedisHandler

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

T = TypeVar("T")

# In-memory cache fallback
_memory_cache: dict[str, tuple[Any, float]] = {}


def _make_cache_key(func: Callable[..., T], *args: Any, **kwargs: Any) -> str:
    """Generate a cache key from function and arguments."""
    key_parts = [
        func.__module__,
        func.__name__,
        str(args),
        str(sorted(kwargs.items())),
    ]
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache(
    ttl: int = 3600,
    use_redis: bool = False,
    redis_handler: Optional[Any] = None,
    key_prefix: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Cache decorator with TTL support.

    Args:
        ttl: Time to live in seconds (default: 3600)
        use_redis: Whether to use Redis for caching
        redis_handler: RedisHandler instance (if use_redis=True)
        key_prefix: Optional prefix for cache keys

    Returns:
        Decorated function with caching
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            import time

            cache_key = _make_cache_key(func, *args, **kwargs)
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"

            # Try Redis first if enabled
            if use_redis and redis_handler and HAS_REDIS:
                try:
                    cached = await redis_handler.get_key(cache_key)
                    if cached and cached.get("value"):
                        return cached["value"]
                except Exception:
                    pass  # Fall back to memory cache

            # Check memory cache
            if cache_key in _memory_cache:
                value, expiry = _memory_cache[cache_key]
                if time.time() < expiry:
                    return value
                del _memory_cache[cache_key]

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            expiry_time = time.time() + ttl

            if use_redis and redis_handler and HAS_REDIS:
                from contextlib import suppress

                with suppress(Exception):
                    await redis_handler.set_key(cache_key, result, ttl=ttl)

            _memory_cache[cache_key] = (result, expiry_time)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            import time

            cache_key = _make_cache_key(func, *args, **kwargs)
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"

            # Check memory cache
            if cache_key in _memory_cache:
                value, expiry = _memory_cache[cache_key]
                if time.time() < expiry:
                    return value
                del _memory_cache[cache_key]

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            expiry_time = time.time() + ttl
            _memory_cache[cache_key] = (result, expiry_time)

            return result

        # Detect if function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def clear_cache(key_pattern: Optional[str] = None) -> None:
    """
    Clear cache entries.

    Args:
        key_pattern: Optional pattern to match keys (clears all if None)
    """
    if key_pattern:
        keys_to_delete = [k for k in _memory_cache if key_pattern in k]
        for key in keys_to_delete:
            del _memory_cache[key]
    else:
        _memory_cache.clear()


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    import time

    total_keys = len(_memory_cache)
    expired_keys = sum(1 for _, expiry in _memory_cache.values() if time.time() >= expiry)

    return {
        "total_keys": total_keys,
        "active_keys": total_keys - expired_keys,
        "expired_keys": expired_keys,
        "cache_type": "memory",
    }


# CLI functionality
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Cache utility CLI - Manage cache")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show cache statistics")

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear cache")
    clear_parser.add_argument(
        "--pattern", help="Pattern to match keys (clears all if not specified)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        import sys

        sys.exit(1)

    if args.command == "stats":
        stats = get_cache_stats()
        print(json.dumps(stats, indent=2))

    elif args.command == "clear":
        clear_cache(args.pattern)
        print("Cache cleared" + (f" (pattern: {args.pattern})" if args.pattern else ""))
