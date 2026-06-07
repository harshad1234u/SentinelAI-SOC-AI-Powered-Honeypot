import httpx
import asyncio
import urllib.parse

async def trace_api():
    print("--- 2. Testing API /api/v1/attacks/live ---")
    url = "https://soc-backend-755420559974.us-central1.run.app/api/v1/attacks/live?page=1&page_size=10"
    
    auth_url = "https://soc-backend-755420559974.us-central1.run.app/api/v1/auth/login"
    password = "change-me-in-production"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(auth_url, data={"username":"admin", "password":password}, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if resp.status_code != 200:
            print("Failed to login", resp.status_code, resp.text)
            return
        token = resp.json()["access_token"]
        
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        print(f"API Response Status: {resp.status_code}")
        try:
            data = resp.json()
            print(f"Total attacks reported by API: {data.get('total')}")
            if data.get("items"):
                print("Latest Attack:")
                print(data["items"][0])
            else:
                print("No items returned from API.")
        except Exception as e:
            print("Failed to parse API JSON", e)

if __name__ == "__main__":
    asyncio.run(trace_api())
