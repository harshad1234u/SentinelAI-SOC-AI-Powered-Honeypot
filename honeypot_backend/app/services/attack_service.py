import asyncio
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, text, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.attack import Attack
from app.services.loki_service import loki_service
from app.services.log_parser import parse_log
from app.services.geoip_service import geoip_service
from app.services.threatintel_service import threatintel_service

# Note: We will import event_dispatcher locally to avoid circular dependencies
# from app.events.dispatcher import event_dispatcher 

logger = get_logger(__name__)

class AttackService:
    def __init__(self):
        self.settings = get_settings()

    def calculate_threat_score(self, abuse_confidence: int, attack_type: str, severity: str, command: str = None) -> int:
        score = 0
        if abuse_confidence and abuse_confidence > 90:
            score += 30
        if attack_type == "malware_download" or severity == "critical":
            score += 30
        if attack_type == "brute_force_success":
            score += 20
        if command and any(cmd in command for cmd in ["rm -rf", "wget", "chmod 777", "nc -e"]):
            score += 20
        # Placeholder for burst logic (+10)
        
        return min(max(score, 0), 100)

    def get_threat_level(self, score: int) -> str:
        if score <= 25:
            return "low"
        elif score <= 50:
            return "medium"
        elif score <= 75:
            return "high"
        return "critical"

    async def ingest_logs(self, db: AsyncSession):
        from app.events.dispatcher import event_dispatcher
        
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=5) # In a real implementation, read this from Redis
        
        logger.info(f"Ingesting logs from {start} to {end}")
        
        cowrie_logs = await loki_service.query_cowrie_logs(start, end)
        opencanary_logs = await loki_service.query_opencanary_logs(start, end)
        
        all_logs = [(log, "cowrie") for log in cowrie_logs] + [(log, "opencanary") for log in opencanary_logs]
        
        ingested_count = 0
        
        for raw_log, job in all_logs:
            parsed = parse_log(raw_log, job)
            if not parsed:
                continue
                
            src_ip = parsed.get("src_ip")
            if not src_ip:
                continue
                
            # GeoIP enrichment
            geo_info = geoip_service.enrich(src_ip)
            parsed["src_country"] = geo_info.country
            parsed["src_country_code"] = geo_info.country_code
            parsed["src_city"] = geo_info.city
            parsed["src_lat"] = geo_info.lat
            parsed["src_lon"] = geo_info.lon
            parsed["src_asn"] = geo_info.asn
            
            # Threat Intel enrichment
            threat_info = await threatintel_service.lookup_ip(src_ip)
            if threat_info:
                parsed["abuse_confidence"] = threat_info.abuse_confidence
                parsed["isp"] = threat_info.isp
                parsed["usage_type"] = threat_info.usage_type
                parsed["total_reports"] = threat_info.total_reports
                parsed["reputation"] = threat_info.reputation
            else:
                parsed["abuse_confidence"] = 0
                parsed["reputation"] = "low"
                
            # Threat score calculation
            score = self.calculate_threat_score(
                parsed["abuse_confidence"], 
                parsed["attack_type"], 
                parsed["severity"], 
                parsed.get("command")
            )
            parsed["threat_score"] = score
            
            # Use timestamp from log if available, else current time
            log_time_str = parsed.get("timestamp")
            if log_time_str:
                try:
                    # Basic parsing, might need adjustment based on real log format
                    if "T" in log_time_str:
                        dt = datetime.fromisoformat(log_time_str.replace("Z", "+00:00"))
                    else:
                        # try parse opencanary float timestamp or similar if needed
                        dt = datetime.now(timezone.utc)
                except Exception:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)
                
            # DB Save
            attack = Attack(
                timestamp=dt,
                src_ip=src_ip,
                src_country=parsed.get("src_country"),
                src_country_code=parsed.get("src_country_code"),
                src_city=parsed.get("src_city"),
                src_lat=parsed.get("src_lat"),
                src_lon=parsed.get("src_lon"),
                src_asn=parsed.get("src_asn"),
                dst_port=parsed.get("dst_port"),
                service=parsed.get("service"),
                username=parsed.get("username"),
                password=parsed.get("password"),
                command=parsed.get("command"),
                severity=parsed.get("severity"),
                attack_type=parsed.get("attack_type"),
                honeypot_type=parsed.get("honeypot_type"),
                session_id=parsed.get("session_id"),
                raw_log=parsed.get("raw_log"),
                vector_indexed=False,
                abuse_confidence=parsed.get("abuse_confidence"),
                isp=parsed.get("isp"),
                usage_type=parsed.get("usage_type"),
                total_reports=parsed.get("total_reports"),
                reputation=parsed.get("reputation"),
                threat_score=parsed.get("threat_score")
            )
            
            db.add(attack)
            await db.flush()  # To get the ID
            
            # Publish event
            await event_dispatcher.dispatch("attack_ingested", attack)
            ingested_count += 1
            
        await db.commit()
        logger.info(f"Ingested {ingested_count} attacks")
        return ingested_count

    async def get_attacks(self, db: AsyncSession, skip: int = 0, limit: int = 50, filters: dict = None):
        query = select(Attack).order_by(desc(Attack.timestamp))
        if filters:
            for k, v in filters.items():
                if v is not None and hasattr(Attack, k):
                    field = getattr(Attack, k)
                    if k in ["src_ip", "attack_type"] and isinstance(v, str):
                        query = query.where(field.ilike(f"%{v}%"))
                    else:
                        query = query.where(field == v)
        
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()
        return {"items": items, "total": total}

    async def get_attack_stats(self, db: AsyncSession):
        total = await db.scalar(select(func.count(Attack.id)))
        
        # attacks today
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        attacks_today = await db.scalar(select(func.count(Attack.id)).where(Attack.timestamp >= today))
        
        unique_ips = await db.scalar(select(func.count(Attack.src_ip.distinct())))
        unique_countries = await db.scalar(select(func.count(Attack.src_country.distinct())))
        
        # services
        services_result = await db.execute(select(Attack.service, func.count(Attack.id)).group_by(Attack.service).order_by(desc(func.count(Attack.id))).limit(5))
        top_services = [{"service": row[0], "count": row[1]} for row in services_result]
        
        # severity breakdown
        severity_result = await db.execute(select(Attack.severity, func.count(Attack.id)).group_by(Attack.severity))
        severity_breakdown = {row[0]: row[1] for row in severity_result}
        
        return {
            "total_attacks": total,
            "attacks_today": attacks_today,
            "unique_ips": unique_ips,
            "unique_countries": unique_countries,
            "top_services": top_services,
            "severity_breakdown": severity_breakdown
        }

    async def cleanup_old_attacks(self, db: AsyncSession):
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.settings.RETENTION_DAYS)
        await db.execute(text("DELETE FROM attacks WHERE timestamp < :cutoff"), {"cutoff": cutoff})
        await db.commit()

attack_service = AttackService()
