"""
FastAPI application factory with lifespan management.

Startup:  initialises DB engine, Redis, httpx clients, GeoIP, Qdrant, RQ queues.
Shutdown: disposes all resources gracefully.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as aioredis
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.session import create_engine_and_session, dispose_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application-level resources."""
    settings = get_settings()

    # ── Logging ──────────────────────────────────────────────────────────
    setup_logging(
        json_output=settings.is_production,
        log_level="INFO" if settings.is_production else "DEBUG",
    )
    logger.info(
        "Starting Honeypot SOC Backend",
        environment=settings.ENVIRONMENT,
    )

    # ── Database ─────────────────────────────────────────────────────────
    engine, async_session_factory = create_engine_and_session(settings)
    app.state.db_engine = engine
    app.state.async_session = async_session_factory
    logger.info("Database engine initialised")

    # ── Redis ────────────────────────────────────────────────────────────
    app.state.redis = None
    if getattr(settings, "REDIS_ENABLED", False):
        try:
            app.state.redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=50,
            )
            await app.state.redis.ping()
            logger.info("Redis connected")
        except Exception as exc:
            logger.warning("Redis connection failed (Cache will be disabled)", error=str(exc))
            app.state.redis = None
    else:
        logger.info("Redis disabled via configuration")

    # ── httpx (shared for Loki / ThreatIntel / Telegram) ─────────────────
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    logger.info("HTTP client initialised")

    # ── Prometheus ───────────────────────────────────────────────────────
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            excluded_handlers=["/health", "/metrics"],
        ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
        logger.info("Prometheus metrics enabled")
    except Exception as exc:
        logger.warning("Prometheus instrumentation failed", error=str(exc))

    # ── Services Initialization ──────────────────────────────────────────
    from app.events.handlers import register_handlers
    from app.services.cache_service import cache_service
    from app.services.geoip_service import geoip_service
    from app.services.threatintel_service import threatintel_service
    from app.ai.embedding_service import embedding_service
    
    register_handlers()
    cache_service.startup()
    geoip_service.startup()
    threatintel_service.startup()
    try:
        await embedding_service.ensure_collection()
    except Exception as exc:
        logger.warning("Failed to ensure Qdrant collection", error=str(exc))

    # ── Background Tasks ─────────────────────────────────────────────────
    from app.services.attack_service import attack_service
    from app.ai.nim_client import nim_client
    from app.alerts.telegram import telegram_alerter, AlertPayload
    from app.models.attack import Attack
    from sqlalchemy import select
    import uuid
    import asyncio
    from datetime import datetime, timedelta, timezone

    async def loki_ingestion_loop():
        while True:
            try:
                async_session_factory = app.state.async_session
                async with async_session_factory() as db:
                    await attack_service.ingest_logs(db)
            except Exception as e:
                logger.error(f"Loki ingestion loop error: {e}")
            await asyncio.sleep(10)

    async def hourly_ai_report_loop():
        while True:
            await asyncio.sleep(3600)
            try:
                now = datetime.now(timezone.utc)
                one_hour_ago = now - timedelta(hours=1)
                
                async_session_factory = app.state.async_session
                async with async_session_factory() as db:
                    query = select(Attack).where(Attack.timestamp >= one_hour_ago).limit(100)
                    result = await db.execute(query)
                    recent_attacks = list(result.scalars().all())
                
                if recent_attacks:
                    attacks_data = [
                        {
                            "id": str(a.id),
                            "timestamp": str(a.timestamp),
                            "src_ip": a.src_ip,
                            "dst_port": a.dst_port,
                            "service": a.service,
                            "attack_type": a.attack_type,
                        } for a in recent_attacks
                    ]
                    
                    context_str = "Generate a brief executive summary of these attacks from the last hour."
                    report_data, model_used, prompt_version = await nim_client.investigate_incident(
                        attacks_data, 
                        context_str
                    )
                    
                    summary = report_data.get("summary", "No summary generated.")
                    recommendations = "\n".join(report_data.get("recommended_actions", []))
                    
                    payload = AlertPayload(
                        attack_id=str(uuid.uuid4()),
                        src_ip="System",
                        alert_type="hourly_summary",
                        severity="info",
                        message=f"<b>📈 Hourly Threat Summary</b>\n\n<b>Total attacks in last hour:</b> {len(recent_attacks)}\n\n<b>AI Summary:</b>\n{summary}\n\n<b>Recommendations:</b>\n{recommendations}"
                    )
                    await telegram_alerter.send_alert(payload)
            except Exception as e:
                logger.error(f"Hourly AI report loop error: {e}")

    ingestion_task = asyncio.create_task(loki_ingestion_loop())
    report_task = asyncio.create_task(hourly_ai_report_loop())

    yield  # ── Application runs here ─────────────────────────────────────

    # ── Shutdown ─────────────────────────────────────────────────────────
    ingestion_task.cancel()
    report_task.cancel()
    from app.services.cache_service import cache_service
    from app.services.geoip_service import geoip_service
    from app.services.threatintel_service import threatintel_service
    from app.services.loki_service import loki_service
    from app.alerts.telegram import telegram_alerter

    logger.info("Shutting down Honeypot SOC Backend")

    await loki_service.close()
    await threatintel_service.close()
    await telegram_alerter.close()
    geoip_service.close()
    await cache_service.close()

    await app.state.http_client.aclose()
    if getattr(app.state, "redis", None):
        await app.state.redis.aclose()
    await dispose_engine(engine)

    logger.info("All resources disposed — goodbye")


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Honeypot SOC Backend",
        description="AI-powered cybersecurity honeypot monitoring platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Middleware (imported lazily to avoid circular imports) ────────────
    from app.middleware.request_id import RequestIDMiddleware
    app.add_middleware(RequestIDMiddleware)

    # ── Routers ──────────────────────────────────────────────────────────
    from app.api import api_router
    from app.api.health import router as health_router

    app.include_router(health_router)        # /health — public, no prefix
    app.include_router(api_router, prefix="/api/v1")

    # ── WebSocket ────────────────────────────────────────────────────────
    from app.websocket.handlers import websocket_attacks
    app.add_api_websocket_route(
        "/api/v1/ws/attacks",
        websocket_attacks,
        name="ws_attacks",
    )

    # ── Global exception handlers ────────────────────────────────────────
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            path=str(request.url),
            method=request.method,
            error=str(exc),
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
