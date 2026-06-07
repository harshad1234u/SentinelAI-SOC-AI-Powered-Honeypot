import orjson
import redis.asyncio as redis
from typing import Any
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class CacheService:
    def __init__(self):
        self.settings = get_settings()
        self.redis = None

    def startup(self):
        if getattr(self.settings, "REDIS_ENABLED", False):
            try:
                self.redis = redis.from_url(self.settings.REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.warning("Cache startup error: Redis unavailable", error=str(e))
                self.redis = None
        else:
            logger.info("Cache startup skipped: REDIS_ENABLED=False")

    async def close(self):
        if self.redis:
            await self.redis.aclose()

    async def get_cached_analysis(self, cache_key: str) -> dict[str, Any] | None:
        if not self.redis:
            return None
        try:
            data = await self.redis.get(cache_key)
            if data:
                return orjson.loads(data)
        except Exception as e:
            logger.warning("Cache read error", error=str(e), key=cache_key)
        return None

    async def cache_analysis(self, cache_key: str, analysis: dict[str, Any], ttl: int = None):
        if not self.redis:
            return
        if ttl is None:
            ttl = self.settings.AI_CACHE_TTL
        try:
            data = orjson.dumps(analysis).decode("utf-8")
            await self.redis.setex(cache_key, ttl, data)
        except Exception as e:
            logger.warning("Cache write error", error=str(e), key=cache_key)

    async def invalidate(self, pattern: str):
        if not self.redis:
            return
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.warning("Cache invalidate error", error=str(e), pattern=pattern)

cache_service = CacheService()
