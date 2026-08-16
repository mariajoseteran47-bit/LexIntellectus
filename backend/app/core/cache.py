"""
LexIntellectus ERP - Redis Cache Utility
"""
import json
from typing import Optional, Any
import redis.asyncio as aioredis
from app.core.config import settings

# Global redis client for caching
redis_client = aioredis.from_url(settings.redis_url_computed, encoding="utf-8", decode_responses=True)

async def get_cache(key: str) -> Optional[Any]:
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None

async def set_cache(key: str, value: Any, expire_seconds: int = 3600):
    await redis_client.set(key, json.dumps(value), ex=expire_seconds)

async def delete_cache(key: str):
    await redis_client.delete(key)
