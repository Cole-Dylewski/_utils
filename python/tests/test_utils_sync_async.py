"""
Tests for sync_async utilities.
"""

import asyncio

import pytest
from utils import sync_async


@pytest.mark.unit
class TestSyncAsyncUtils:
    """Test sync_async utility functions."""

    @pytest.mark.asyncio
    async def test_run_async_function(self):
        """Test running async function from sync context."""

        async def async_add(a, b):
            await asyncio.sleep(0.01)
            return a + b

        result = sync_async.run_async_function(async_add, 2, 3)
        assert result == 5

    def test_run_async_function_with_kwargs(self):
        """Test running async function with kwargs."""

        async def async_multiply(x, multiplier=2):
            await asyncio.sleep(0.01)
            return x * multiplier

        result = sync_async.run_async_function(async_multiply, 5, multiplier=3)
        assert result == 15

    def test_run_async_function_error_handling(self):
        """Test error handling in async function."""

        async def async_error():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            sync_async.run_async_function(async_error)
