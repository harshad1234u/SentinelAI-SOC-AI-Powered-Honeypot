from fastapi import APIRouter
from app.api import health, auth, attacks, ai, alerts, search, metrics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(attacks.router, tags=["attacks"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
