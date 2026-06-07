import asyncio
import httpx

BASE_URL = "https://soc-backend-755420559974.us-central1.run.app"
password = "change-me-in-production"

async def trace_live():
    print("\n--- Testing Live Feed ---")
    auth_url = f"{BASE_URL}/api/v1/auth/login"
    test_url = f"{BASE_URL}/api/v1/alerts/test"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(auth_url, data={"username":"admin", "password":password}, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if resp.status_code != 200:
            print("Failed to login", resp.status_code, resp.text)
            return
            
        token = resp.json()["access_token"]
        print(f"Logged in, testing Telegram from {test_url}...")
        
        resp = await client.post(test_url, headers={"Authorization": f"Bearer {token}"}, json={"message": "System verification completed."})
        print(f"Status: {resp.status_code}")
        
        data = resp.json()
        print(f"Telegram test result: {data}")

if __name__ == "__main__":
    asyncio.run(trace_live())
