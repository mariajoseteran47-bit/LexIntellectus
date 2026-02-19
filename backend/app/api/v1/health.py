"""
LexIntellectus - Health Check API
Verifies connectivity to all infrastructure services.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
import redis.asyncio as aioredis

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint — verifies PostgreSQL and Redis connectivity.
    Returns status of each service.
    """
    health = {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": "disconnected",
        "redis": "disconnected",
    }

    # Check PostgreSQL
    try:
        result = await db.execute(text("SELECT 1"))
        if result:
            health["database"] = "connected"
    except Exception as e:
        health["status"] = "degraded"
        health["database"] = f"error: {str(e)[:100]}"

    # Check Redis
    try:
        redis_client = aioredis.from_url(settings.redis_url_computed)
        pong = await redis_client.ping()
        if pong:
            health["redis"] = "connected"
        await redis_client.aclose()
    except Exception as e:
        health["status"] = "degraded"
        health["redis"] = f"error: {str(e)[:100]}"

    return health
