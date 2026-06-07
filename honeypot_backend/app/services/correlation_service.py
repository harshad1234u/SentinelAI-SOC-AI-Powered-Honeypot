import time
import uuid
from pydantic import BaseModel
from typing import Any
from app.models.attack import Attack
from app.services.cache_service import cache_service

class Correlation(BaseModel):
    id: str
    type: str
    description: str
    severity: str
    related_attacks: list[str] = []

class CampaignResult(BaseModel):
    id: str
    name: str
    attacks: list[str]

class CorrelationService:
    def __init__(self):
        pass

    async def detect_correlations(self, attack: Attack) -> list[Correlation]:
        correlations = []
        redis = cache_service.redis
        if not redis:
            return correlations

        current_time = int(time.time())
        window_60s = current_time - 60
        window_1h = current_time - 3600

        # Repeated attacker
        ip_key = f"corr:ip:{attack.src_ip}"
        await redis.zadd(ip_key, {str(attack.id): current_time})
        await redis.zremrangebyscore(ip_key, 0, window_1h)
        ip_count = await redis.zcard(ip_key)
        
        if ip_count > 20:
            correlations.append(Correlation(
                id=str(uuid.uuid4()),
                type="repeated_attacker",
                description=f"IP {attack.src_ip} seen {ip_count} times in the last hour",
                severity="medium",
                related_attacks=[]
            ))

        # Brute force burst
        if attack.attack_type == "brute_force" or attack.attack_type == "brute_force_success":
            bf_key = f"corr:bf:{attack.src_ip}"
            await redis.zadd(bf_key, {str(attack.id): current_time})
            await redis.zremrangebyscore(bf_key, 0, window_60s)
            bf_count = await redis.zcard(bf_key)
            if bf_count > 10:
                correlations.append(Correlation(
                    id=str(uuid.uuid4()),
                    type="brute_force_burst",
                    description=f">10 login attempts from {attack.src_ip} in 60s",
                    severity="high"
                ))

        # Distributed scan (Simplified: multiple IPs to same port)
        # Using a redis set of IPs for a port in a time window
        if attack.dst_port:
            port_key = f"corr:port:{attack.dst_port}"
            await redis.sadd(port_key, attack.src_ip)
            await redis.expire(port_key, 3600) # expire in 1 hour
            ip_set_count = await redis.scard(port_key)
            if ip_set_count > 50:
                correlations.append(Correlation(
                    id=str(uuid.uuid4()),
                    type="distributed_scan",
                    description=f"More than 50 IPs scanning port {attack.dst_port} recently",
                    severity="high"
                ))

        # Geographic anomaly (New country)
        if attack.src_country_code:
            country_key = f"corr:country:{attack.src_country_code}"
            seen_before = await redis.get(country_key)
            if not seen_before:
                correlations.append(Correlation(
                    id=str(uuid.uuid4()),
                    type="geographic_anomaly",
                    description=f"First time seeing attacks from {attack.src_country_code}",
                    severity="medium"
                ))
            await redis.setex(country_key, 30 * 86400, "1") # remember for 30 days

        return correlations

    async def get_campaign_attacks(self, campaign_id: str) -> list[Any]:
        # Placeholder for DB query based on campaign logic
        return []

    async def detect_campaign(self, attacks: list[Attack]) -> CampaignResult | None:
        # Placeholder for complex campaign clustering
        if not attacks:
            return None
        return CampaignResult(
            id=str(uuid.uuid4()),
            name="Unknown Campaign",
            attacks=[str(a.id) for a in attacks]
        )

correlation_service = CorrelationService()
