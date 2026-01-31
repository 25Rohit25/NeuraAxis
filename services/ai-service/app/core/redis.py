"""
NEURAXIS - Redis Client
Redis connection management for caching
"""

import logging
from functools import lru_cache
from typing import Optional

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[ConnectionPool] = None
_client: Optional[Redis] = None


async def get_redis_client() -> Optional[Redis]:
    """
    Get Redis client instance.

    Returns:
        Redis client or None if not configured
    """
    global _pool, _client

    if not settings.REDIS_URL:
        logger.debug("Redis not configured")
        return None

    try:
        if _pool is None:
            _pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=10,
                decode_responses=True,
            )

        if _client is None:
            _client = Redis(connection_pool=_pool)

        # Test connection
        await _client.ping()

        return _client

    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        return None


async def close_redis_connection():
    """Close Redis connection on shutdown."""
    global _pool, _client

    if _client:
        await _client.close()
        _client = None

    if _pool:
        await _pool.disconnect()
        _pool = None

    logger.info("Redis connection closed")


class RedisCache:
    """
    Redis cache wrapper with common operations.
    """

    def __init__(self, prefix: str = "neuraxis"):
        self.prefix = prefix
        self._client: Optional[Redis] = None

    async def _get_client(self) -> Optional[Redis]:
        """Get or create Redis client."""
        if self._client is None:
            self._client = await get_redis_client()
        return self._client

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        client = await self._get_client()
        if not client:
            return None

        try:
            return await client.get(self._make_key(key))
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: int = 3600,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        client = await self._get_client()
        if not client:
            return False

        try:
            await client.setex(self._make_key(key), ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        client = await self._get_client()
        if not client:
            return False

        try:
            await client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await self._get_client()
        if not client:
            return False

        try:
            return await client.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.warning(f"Cache exists check failed: {e}")
            return False

    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in cache."""
        client = await self._get_client()
        if not client:
            return None

        try:
            return await client.incrby(self._make_key(key), amount)
        except Exception as e:
            logger.warning(f"Cache incr failed: {e}")
            return None

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key."""
        client = await self._get_client()
        if not client:
            return False

        try:
            return await client.expire(self._make_key(key), ttl)
        except Exception as e:
            logger.warning(f"Cache expire failed: {e}")
            return False


# Global cache instance
cache = RedisCache()
