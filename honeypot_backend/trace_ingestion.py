import asyncio
import httpx
import json
from datetime import datetime, timezone, timedelta
import urllib.parse

async def trace_loki():
    print("--- 1. Testing Loki Query ---")
    start_dt = datetime.now(timezone.utc) - timedelta(hours=1)
    end_dt = datetime.now(timezone.utc)
    
    start_ns = int(start_dt.timestamp() * 1e9)
    end_ns = int(end_dt.timestamp() * 1e9)
    
    query = '{job=~"cowrie|opencanary"}'
    url = f"http://34.93.77.93:3100/loki/api/v1/query_range?query={urllib.parse.quote(query)}&start={start_ns}&end={end_ns}&limit=10"
    
    print(f"Loki URL: {url}")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        print(f"Loki Response Status: {resp.status_code}")
        try:
            data = resp.json()
            print("Raw Loki Response Snippet (First Stream):")
            if data.get("data", {}).get("result"):
                print(json.dumps(data["data"]["result"][0], indent=2)[:500] + "...")
            else:
                print("No results found in Loki.")
                print(data)
        except Exception as e:
            print(f"Failed to parse Loki response: {e}")
            print(resp.text)

if __name__ == "__main__":
    asyncio.run(trace_loki())
