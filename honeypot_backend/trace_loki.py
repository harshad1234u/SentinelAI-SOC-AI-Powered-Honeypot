import asyncio
import httpx
import json
from datetime import datetime, timezone, timedelta
import urllib.parse

async def trace_loki():
    print("--- 1. Testing Loki Query (Last 5 Minutes) ---")
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=5)
    
    start_ns = int(start.timestamp() * 1e9)
    end_ns = int(end.timestamp() * 1e9)
    
    query = '{job=~"cowrie|opencanary"}'
    url = f"http://34.93.77.93:3100/loki/api/v1/query_range?query={urllib.parse.quote(query)}&start={start_ns}&end={end_ns}&limit=100"
    
    print(f"Loki URL: {url}")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        print(f"Loki Response Status: {resp.status_code}")
        try:
            data = resp.json()
            if data.get("data", {}).get("result"):
                res = data["data"]["result"]
                print(f"Found {len(res)} streams.")
                total_values = sum(len(stream.get("values", [])) for stream in res)
                print(f"Total values (logs): {total_values}")
                if total_values > 0:
                    print(json.dumps(res[0]["values"][0], indent=2))
            else:
                print("No results found in Loki.")
                print(data)
        except Exception as e:
            print(f"Failed to parse Loki response: {e}")
            print(resp.text)

if __name__ == "__main__":
    asyncio.run(trace_loki())
