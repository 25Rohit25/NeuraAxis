import logging
import time

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.cache import cache_client

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for static/health
        if request.url.path == "/health" or request.method == "OPTIONS":
            return await call_next(request)

        # Simple IP-based rate limit: 100 req/min
        client_ip = request.client.host if request.client else "unknown"

        # Use minute-window bucket
        key = f"rate_limit:{client_ip}:{int(time.time() // 60)}"

        if cache_client.client:
            try:
                # Increment count
                current = await cache_client.client.incr(key)

                # Set expiry on new key
                if current == 1:
                    await cache_client.client.expire(key, 60)

                # Check limit
                if current > 100:
                    logger.warning(f"Rate limit exceeded for {client_ip}")
                    return JSONResponse(
                        status_code=429, content={"detail": "Too Many Requests. Limit 100/min."}
                    )
            except Exception as e:
                # Fail open if Redis fails
                logger.error(f"Rate limit redis error: {e}")

        response = await call_next(request)
        return response


def setup_global_middleware(app: FastAPI):
    """Register all global middleware."""
    # Compression (Gzip) - Effective for JSON responses > 1KB
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Rate Limiting
    app.add_middleware(RateLimitMiddleware)

    # Note: CORSMiddleware is usually added in main.py, ensure order is correct (CORS first/last depending on need)
