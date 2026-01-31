import json
import logging
import os
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        self.client = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
        try:
            await self.client.ping()
            logger.info("Connected to Redis Cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None

    async def close(self):
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> Any:
        if not self.client:
            return None
        return await self.client.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300):
        if not self.client:
            return
        # Handle dict/list serialization
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.client.set(key, value, ex=ttl)


cache_client = RedisCache()


def cache_response(ttl: int = 60, key_prefix: str = ""):
    """Decorator to cache API endpoint responses."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not cache_client.client:
                # Fallback if cache down
                return await func(*args, **kwargs)

            # Build Cache Key (simplified)
            # In a real app, hash the args/kwargs robustly
            # For FastAPI, usually involves request path + query params
            cache_key = f"{key_prefix}:{func.__name__}:{str(kwargs)}"

            cached = await cache_client.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except:
                    return cached

            result = await func(*args, **kwargs)

            # Cache the Pydantic model by converting to dict/json
            # This requires result to be serializable
            to_cache = result
            if hasattr(result, "dict"):
                to_cache = result.dict()
            elif hasattr(result, "json"):
                to_cache = result.json()

            await cache_client.set(cache_key, to_cache, ttl=ttl)
            return result

        return wrapper

    return decorator
