import asyncio
from datetime import datetime, timezone, timedelta
from app.services.attack_service import attack_service
from app.services.loki_service import loki_service
from app.services.geoip_service import geoip_service
from app.services.threatintel_service import threatintel_service
from app.services.log_parser import parse_log

class MockDB:
    def __init__(self):
        self.added = []
    def add(self, item):
        self.added.append(item)
    async def flush(self):
        pass
    async def commit(self):
        print(f"MockDB Commit: {len(self.added)} attacks saved")

async def test_ingest():
    print("Testing Ingest Flow for last 24h")
    geoip_service.startup()
    threatintel_service.startup()
    
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    
    cowrie_logs = await loki_service.query_cowrie_logs(start, end)
    opencanary_logs = await loki_service.query_opencanary_logs(start, end)
    
    all_logs = [(log, "cowrie") for log in cowrie_logs] + [(log, "opencanary") for log in opencanary_logs]
    print(f"Found {len(all_logs)} logs from Loki")
    
    db = MockDB()
    
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
        
        # Threat Intel enrichment
        threat_info = await threatintel_service.lookup_ip(src_ip)
        if threat_info:
            parsed["abuse_confidence"] = threat_info.abuse_confidence
        
        ingested_count += 1
        db.add(parsed)
        
    await db.commit()
    print(f"Ingested {ingested_count} logs")

if __name__ == "__main__":
    asyncio.run(test_ingest())
