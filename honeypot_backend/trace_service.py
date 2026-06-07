import asyncio
from datetime import datetime, timezone, timedelta
from app.services.loki_service import loki_service

async def trace_service():
    print("Testing LokiService.query_opencanary_logs")
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=5)
    
    logs = await loki_service.query_opencanary_logs(start, end)
    print(f"LokiService returned {len(logs)} logs")
    if logs:
        print(logs[0])

if __name__ == "__main__":
    asyncio.run(trace_service())
