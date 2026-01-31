"""
NEURAXIS AI Service - Health Check Routes
"""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("")
async def health_check():
    """Check service health."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready")
async def readiness_check():
    """Check if service is ready to accept requests."""
    # TODO: Check database, redis, and other dependencies
    return {
        "status": "ready",
        "checks": {
            "database": "healthy",
            "redis": "healthy",
            "models": "healthy",
        },
    }


@router.get("/live")
async def liveness_check():
    """Check if service is alive."""
    return {"status": "alive"}
