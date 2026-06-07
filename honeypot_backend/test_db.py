import asyncio
from app.db.session import async_session_factory
from app.models.attack import Attack
from sqlalchemy import select, func

async def check_db():
    async with async_session_factory() as db:
        result = await db.execute(select(func.count(Attack.id)))
        count = result.scalar()
        print(f"Total attacks in DB: {count}")
        
        result = await db.execute(select(Attack).order_by(Attack.timestamp.desc()).limit(1))
        latest = result.scalars().first()
        if latest:
            print(f"Latest attack: {latest.timestamp} | {latest.src_ip} -> {latest.service}")

if __name__ == "__main__":
    asyncio.run(check_db())
