from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
from app.services.cache_service import cache_service
from app.core.config import get_settings

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next):
        # Exempt endpoints
        path = request.url.path
        if path in ["/health", "/metrics"]:
            return await call_next(request)

        # Trust X-Forwarded-For if available, otherwise fallback to request.client.host
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        minute_bucket = int(time.time() / 60)
        
        # We handle aggressive limits for auth
        if path.startswith("/api/v1/auth"):
            limit = 10
            key = f"ratelimit:auth:{client_ip}:{minute_bucket}"
        else:
            limit = self.settings.RATE_LIMIT_PER_MINUTE
            key = f"ratelimit:{client_ip}:{minute_bucket}"

        redis = cache_service.redis
        if redis:
            try:
                # Increment counter
                current = await redis.incr(key)
                if current == 1:
                    await redis.expire(key, 120) # 2 minutes ttl
                
                if current > limit:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests"},
                        headers={"Retry-After": "60"}
                    )
            except Exception:
                pass # Fail open if redis is down
                
        return await call_next(request)
