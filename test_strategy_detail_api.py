"""测试策略详情API是否正确返回成功的执行和错误信息"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.services.strategy.marketplace_service import marketplace_service

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def test_strategy_detail():
    """测试策略详情API"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

        print("=" * 100)
        print("测试策略详情API")
        print("=" * 100)
        print()

        # 获取策略详情
        detail = await marketplace_service.get_strategy_detail(db, portfolio_id)

        print("📊 Conviction Summary:")
        print(f"   Score: {detail.conviction_summary.score}")
        print(f"   Message: {detail.conviction_summary.message[:100]}...")
        print(f"   Updated At: {detail.conviction_summary.updated_at}")
        print()

        print("📋 Recent Activities:")
        for i, activity in enumerate(detail.recent_activities, 1):
            print(f"\n   Activity {i}:")
            print(f"   - Date: {activity.date}")
            print(f"   - Signal: {activity.signal}")
            print(f"   - Status: {activity.status}")
            print(f"   - Conviction Score: {activity.conviction_score}")

            if activity.status == "failed":
                print(f"   - ⚠️ ERROR DETAILS:")
                if activity.error_details:
                    print(f"     - Error Type: {activity.error_details.get('error_type')}")
                    print(f"     - Failed Agent: {activity.error_details.get('failed_agent')}")
                    print(f"     - Error Message: {activity.error_details.get('error_message')}")
                    print(f"     - Retry Count: {activity.error_details.get('retry_count')}")
            else:
                print(f"   - Action: {activity.action}")
                print(f"   - Result: {activity.result}")
                if activity.agent_contributions:
                    print(f"   - Agent Contributions: {len(activity.agent_contributions)} agents")

        print()
        print("=" * 100)
        print("✅ 测试完成")
        print("=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_strategy_detail())
