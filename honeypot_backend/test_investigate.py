import asyncio
import os
from app.core.config import get_settings
from app.db.session import create_engine_and_session
from app.services.rag_service import rag_service

async def test():
    settings = get_settings()
    engine, async_session_factory = create_engine_and_session(settings)
    async with async_session_factory() as db:
        try:
            res = await rag_service.investigate(db, query="hi")
            print("SUCCESS:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
