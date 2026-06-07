import asyncio
from qdrant_client import AsyncQdrantClient

async def main():
    client = AsyncQdrantClient(url="http://34.93.77.93:6333")
    collections = await client.get_collections()
    print([c.name for c in collections.collections])

asyncio.run(main())
