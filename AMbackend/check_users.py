import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f'Found {len(users)} users:')
        for u in users:
            print(f'  {u.id}: {u.email}')

asyncio.run(check())
