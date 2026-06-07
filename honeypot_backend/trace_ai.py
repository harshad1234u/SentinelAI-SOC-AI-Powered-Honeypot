import asyncio
import httpx

async def trace_ai():
    print("\n--- Testing AI Assistant Chat ---")
    BASE_URL = "https://soc-backend-755420559974.us-central1.run.app"
    
    # 1. Login
    auth_url = f"{BASE_URL}/api/v1/auth/login"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(auth_url, data={"username": "admin", "password": "change-me-in-production"})
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return
        
        token = resp.json().get("access_token")
        
        # 2. Get an attack ID
        live_url = f"{BASE_URL}/api/v1/attacks/live"
        resp = await client.get(live_url, headers={"Authorization": f"Bearer {token}"})
        data = resp.json()
        items = data.get("items", [])
        
        attack_id = None
        if items:
            attack_id = items[0]["id"]
            print(f"Found attack ID: {attack_id}")
            
        # 3. Test Investigation endpoint
        investigate_url = f"{BASE_URL}/api/v1/ai/investigate"
        if attack_id:
            print(f"Testing Investigation for attack {attack_id}...")
            payload = {"attack_id": attack_id}
            resp = await client.post(investigate_url, headers={"Authorization": f"Bearer {token}"}, json=payload)
            print(f"Investigation Status: {resp.status_code}")
            if resp.status_code != 200:
                print(resp.text)
            else:
                print("Investigation SUCCESS!")
                
        # 4. Test Chat endpoint
        print("Testing Chat...")
        payload = {"query": "Tell me about recent brute force attacks."}
        resp = await client.post(investigate_url, headers={"Authorization": f"Bearer {token}"}, json=payload)
        print(f"Chat Status: {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
        else:
            print("Chat SUCCESS!")

if __name__ == "__main__":
    asyncio.run(trace_ai())
