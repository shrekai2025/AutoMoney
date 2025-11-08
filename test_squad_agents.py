#!/usr/bin/env python3
"""测试squad_agents是否使用了正确的agent_weights"""

import sys
sys.path.append('/Users/uniteyoo/Documents/AutoMoney/AMbackend')

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.strategy.marketplace_service import marketplace_service

async def test_squad_agents():
    """测试squad_agents"""

    # 创建数据库连接
    DATABASE_URL = "postgresql+asyncpg://localhost/automoney"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

        try:
            result = await marketplace_service.get_strategy_detail(
                db=session,
                portfolio_id=portfolio_id
            )

            print(f"Portfolio: {result.name}")
            print(f"\nSquad Agents:")
            for agent in result.squad_agents:
                print(f"  {agent.name} ({agent.role}): {agent.weight}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_squad_agents())
