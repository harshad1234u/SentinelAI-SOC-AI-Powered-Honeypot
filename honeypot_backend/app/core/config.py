"""
Application settings loaded from environment variables.

Uses pydantic-settings BaseSettings with @lru_cache singleton.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from .env / environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment ──────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://soc:change-me-in-production@postgres:5432/honeypot_soc"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def strip_database_url(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_ENABLED: bool = False  # Changed default to False for Cloud Run
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Loki ─────────────────────────────────────────────────────────────
    LOKI_URL: str = "http://loki:3100"
    LOKI_COWRIE_LABEL: str = '{job="cowrie"}'
    LOKI_OPENCANARY_LABEL: str = '{job="opencanary"}'

    # ── NVIDIA NIM ───────────────────────────────────────────────────────
    NIM_API_KEY: str = ""
    NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    REALTIME_MODEL: str = "deepseek-v4-flash"
    FALLBACK_REALTIME_MODEL: str = "llama-3.1-nemotron-nano-8b-v1"
    INVESTIGATION_MODEL: str = "qwen3-next-80b-a3b-instruct"
    EMBED_MODEL: str = "nv-embedqa-e5-v5"

    @field_validator("NIM_API_KEY", mode="before")
    @classmethod
    def strip_nim_api_key(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    # ── AI Cost Protection ───────────────────────────────────────────────
    MAX_INVESTIGATION_ATTACKS: int = 50
    MAX_RAG_CONTEXT_ATTACKS: int = 20
    AI_CACHE_TTL: int = 3600  # seconds

    # ── Qdrant ───────────────────────────────────────────────────────────
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "attack_vectors"

    # ── Telegram ─────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_COOLDOWN_SECONDS: int = 300  # 5 min per-IP cooldown
    TELEGRAM_MAX_PER_MINUTE: int = 20

    @field_validator("TELEGRAM_BOT_TOKEN", mode="before")
    @classmethod
    def strip_telegram_bot_token(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    # ── JWT ───────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def strip_jwt_secret_key(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    # ── Admin (v1 single-user) ───────────────────────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me-in-production"

    # ── GeoIP ────────────────────────────────────────────────────────────
    GEOIP_CITY_DB: str = "./data/GeoLite2-City.mmdb"
    GEOIP_ASN_DB: str = "./data/GeoLite2-ASN.mmdb"

    # ── Threat Intelligence ──────────────────────────────────────────────
    ABUSEIPDB_API_KEY: str = ""
    ABUSEIPDB_BASE_URL: str = "https://api.abuseipdb.com/api/v2"
    THREAT_INTEL_CACHE_TTL: int = 86400  # 24 hours

    @field_validator("ABUSEIPDB_API_KEY", mode="before")
    @classmethod
    def strip_abuseipdb_api_key(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    # ── Rate Limiting ────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Retention ────────────────────────────────────────────────────────
    RETENTION_DAYS: int = 30

    # ── DB Pool ──────────────────────────────────────────────────────────
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()
