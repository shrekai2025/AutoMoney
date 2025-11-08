"""Test API Response for Strategy Detail"""

import sys
import asyncio
import json
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.services.strategy.marketplace_service import marketplace_service


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

        result = await marketplace_service.get_strategy_detail(db, portfolio_id)

        print("=" * 100)
        print("Recent Activities:")
        print("=" * 100)

        for i, activity in enumerate(result.recent_activities[:3], 1):
            print(f"\n{i}. Activity at {activity.date}")
            print(f"   Signal: {activity.signal}")
            print(f"   Conviction: {activity.conviction_score}")
            print(f"   Status: {activity.status}")
            print(f"   Agent Contributions: {len(activity.agent_contributions) if activity.agent_contributions else 0}")

            if activity.agent_contributions:
                for agent in activity.agent_contributions:
                    print(f"     - {agent.display_name}: {agent.signal}, Score: {agent.score}, Confidence: {agent.confidence}")
            else:
                print("     (No agent contributions)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
