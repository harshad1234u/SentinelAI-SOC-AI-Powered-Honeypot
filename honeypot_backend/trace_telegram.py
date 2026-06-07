import asyncio
import httpx
from app.core.config import get_settings

settings = get_settings()

async def test_telegram():
    print(f"Testing Telegram Bot... (Token: {settings.TELEGRAM_BOT_TOKEN[:10]}... Chat ID: {settings.TELEGRAM_CHAT_ID})")
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print("Missing tokens in env!")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": "<b>Test Alert</b>\nBackend Telegram verification is working!",
        "parse_mode": "HTML"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        print(f"Status: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(test_telegram())
