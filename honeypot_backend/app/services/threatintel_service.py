import asyncio
import httpx
import ipaddress
import orjson
from typing import Optional
from pydantic import BaseModel
import redis.asyncio as redis
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class ThreatIntelResult(BaseModel):
    ip: str
    abuse_confidence: int
    country: str | None = None
    isp: str | None = None
    usage_type: str | None = None
    domain: str | None = None
    is_tor: bool | None = None
    total_reports: int
    last_reported: str | None = None
    reputation: str = "low"

class VirusTotalResult(BaseModel):
    hash_value: str
    malicious: int
    total: int

class ThreatIntelService:
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = None
        self.http_client = httpx.AsyncClient(timeout=5.0)
        self.semaphore = asyncio.Semaphore(10)  # Free tier concurrency limit

    def startup(self):
        self.redis_client = redis.from_url(self.settings.REDIS_URL, decode_responses=True)

    async def close(self):
        await self.http_client.aclose()
        if self.redis_client:
            await self.redis_client.aclose()

    def calculate_reputation(self, abuse_score: int) -> str:
        if abuse_score <= 25:
            return "low"
        elif abuse_score <= 60:
            return "medium"
        elif abuse_score <= 90:
            return "high"
        return "critical"

    async def lookup_ip(self, ip: str) -> Optional[ThreatIntelResult]:
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                return None
        except ValueError:
            return None

        cache_key = f"threatintel:ip:{ip}"
        
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return ThreatIntelResult.model_validate_json(cached)
            except Exception as e:
                logger.warning("Redis cache read failed for threatintel", error=str(e), ip=ip)

        if not self.settings.ABUSEIPDB_API_KEY:
            return None

        url = f"{self.settings.ABUSEIPDB_BASE_URL}/check"
        headers = {
            "Accept": "application/json",
            "Key": self.settings.ABUSEIPDB_API_KEY
        }
        params = {
            "ipAddress": ip,
            "maxAgeInDays": "90",
            "verbose": ""
        }

        retries = 3
        backoff = 1.0

        for attempt in range(retries):
            try:
                async with self.semaphore:
                    response = await self.http_client.get(url, headers=headers, params=params)
                    
                    if response.status_code == 429:
                        logger.warning("AbuseIPDB rate limit exceeded")
                        return None
                        
                    response.raise_for_status()
                    data = response.json().get("data", {})
                    
                    score = data.get("abuseConfidenceScore", 0)
                    reputation = self.calculate_reputation(score)
                    
                    result = ThreatIntelResult(
                        ip=ip,
                        abuse_confidence=score,
                        country=data.get("countryName"),
                        isp=data.get("isp"),
                        usage_type=data.get("usageType"),
                        domain=data.get("domain"),
                        is_tor=data.get("isTor"),
                        total_reports=data.get("totalReports", 0),
                        last_reported=data.get("lastReportedAt"),
                        reputation=reputation
                    )

                    if self.redis_client:
                        try:
                            await self.redis_client.setex(
                                cache_key, 
                                self.settings.THREAT_INTEL_CACHE_TTL,
                                result.model_dump_json()
                            )
                        except Exception as e:
                            logger.warning("Redis cache write failed for threatintel", error=str(e))
                            
                    return result

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.error("AbuseIPDB API error", error=str(e), attempt=attempt+1, ip=ip)
                if attempt == retries - 1:
                    return None
                await asyncio.sleep(backoff)
                backoff *= 2

        return None

    async def lookup_hash(self, hash_value: str) -> Optional[VirusTotalResult]:
        # Placeholder for future VirusTotal implementation
        return None

threatintel_service = ThreatIntelService()
