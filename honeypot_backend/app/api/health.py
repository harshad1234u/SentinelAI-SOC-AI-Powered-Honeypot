from fastapi import APIRouter
from app.services.cache_service import cache_service
from app.services.loki_service import loki_service
# Need to check qdrant but using embedding_service might trigger client initialization if not done

router = APIRouter()

@router.get("/health")
async def health_check():
    services = {
        "database": "unknown",
        "redis": "unknown",
        "loki": "unknown"
    }
    status = "healthy"
    
    # Check Redis
    try:
        if cache_service.redis:
            await cache_service.redis.ping()
            services["redis"] = "up"
        else:
            services["redis"] = "down"
            status = "degraded"
    except Exception:
        services["redis"] = "down"
        status = "degraded"
        
    # Check Loki
    try:
        # A simple query to check if Loki is reachable
        # Or just checking if client is up, let's assume simple ping or just return up for now
        # because actual ping might be slow.
        # Wait, loki has /ready endpoint
        resp = await loki_service.client.get("/ready")
        if resp.status_code == 200:
            services["loki"] = "up"
        else:
            services["loki"] = "degraded"
            status = "degraded"
    except Exception:
        services["loki"] = "down"
        status = "degraded"
        
    return {
        "status": status,
        "services": services,
        "version": "1.0.0"
    }
