"""
Tests for Redis utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from utils import redis


@pytest.mark.unit
class TestRedisHandler:
    """Test RedisHandler class."""

    @patch("utils.redis.redis.StrictRedis")
    @patch("utils.redis.aioredis.Redis")
    def test_redis_handler_initialization(self, mock_async_redis, mock_redis):
        """Test RedisHandler initialization."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        mock_async_redis.return_value = MagicMock()

        handler = redis.RedisHandler(host="localhost", port=6379)
        assert handler.client is not None
        assert handler.async_client is not None
        mock_client.ping.assert_called_once()

    @patch("utils.redis.redis.StrictRedis")
    @patch("utils.redis.aioredis.Redis")
    def test_redis_handler_connection_failure(self, mock_async_redis, mock_redis):
        """Test RedisHandler initialization with connection failure."""
        from fastapi import HTTPException

        mock_client = MagicMock()
        mock_client.ping.return_value = False
        mock_redis.return_value = mock_client

        with pytest.raises(HTTPException, match="Unable to connect"):
            redis.RedisHandler(host="localhost", port=6379)

    @patch("utils.redis.redis.StrictRedis")
    @patch("utils.redis.aioredis.Redis")
    def test_redis_handler_connection_error(self, mock_async_redis, mock_redis):
        """Test RedisHandler initialization with connection error."""
        from fastapi import HTTPException
        import redis as redis_lib

        mock_redis.side_effect = redis_lib.ConnectionError("Connection failed")

        with pytest.raises(HTTPException, match="Redis connection failed"):
            redis.RedisHandler(host="localhost", port=6379)

    @pytest.mark.asyncio
    @patch("utils.redis.redis.StrictRedis")
    @patch("utils.redis.aioredis.Redis")
    async def test_get_all_keys(self, mock_async_redis, mock_redis):
        """Test getting all keys."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.return_value = mock_client
        mock_async_redis.return_value = MagicMock()

        handler = redis.RedisHandler(host="localhost", port=6379)
        keys = await handler.get_all_keys()
        assert isinstance(keys, list)
        assert len(keys) == 3
        mock_client.keys.assert_called_once_with("*")

    @pytest.mark.asyncio
    @patch("utils.redis.redis.StrictRedis")
    @patch("utils.redis.aioredis.Redis")
    async def test_flush(self, mock_async_redis, mock_redis):
        """Test flushing Redis database."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.flushdb.return_value = True
        mock_redis.return_value = mock_client
        mock_async_redis.return_value = MagicMock()

        handler = redis.RedisHandler(host="localhost", port=6379)
        result = await handler.flush()
        assert "deleted" in result.lower() or "cleared" in result.lower()
        mock_client.flushdb.assert_called_once()

    @pytest.mark.asyncio
    @patch("utils.redis.redis.StrictRedis")
    @patch("utils.redis.aioredis.Redis")
    async def test_get_keys_without_ttl(self, mock_async_redis, mock_redis):
        """Test getting keys without TTL."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = ["key1", "key2"]
        mock_client.ttl.side_effect = [-1, 3600]  # key1 has no TTL, key2 has TTL
        mock_redis.return_value = mock_client
        mock_async_redis.return_value = MagicMock()

        handler = redis.RedisHandler(host="localhost", port=6379)
        keys = await handler.get_keys_without_ttl()
        assert isinstance(keys, list)
        assert "key1" in keys
        assert "key2" not in keys

    @pytest.mark.asyncio
    @patch("utils.redis.redis.StrictRedis")
    @patch("utils.redis.aioredis.Redis")
    async def test_condemn_keys(self, mock_async_redis, mock_redis):
        """Test condemning keys (setting TTL)."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = ["key1"]
        mock_client.ttl.return_value = -1  # No TTL
        mock_client.expire.return_value = True
        mock_redis.return_value = mock_client
        mock_async_redis.return_value = MagicMock()

        handler = redis.RedisHandler(host="localhost", port=6379)
        result = await handler.condemn_keys(ttl=3600)
        assert isinstance(result, list)
        mock_client.expire.assert_called()
