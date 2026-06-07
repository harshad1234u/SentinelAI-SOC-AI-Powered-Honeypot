import asyncio
from app.services.geoip_service import geoip_service
from app.services.threatintel_service import threatintel_service

async def test():
    geoip_service.startup()
    print("Testing geoip on 192.168.1.100")
    try:
        geo = geoip_service.enrich("192.168.1.100")
        print("GeoIP:", geo)
    except Exception as e:
        print("GeoIP Error:", e)

    print("Testing threatintel on 192.168.1.100")
    try:
        threatintel_service.startup()
        ti = await threatintel_service.lookup_ip("192.168.1.100")
        print("ThreatIntel:", ti)
    except Exception as e:
        print("ThreatIntel Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
