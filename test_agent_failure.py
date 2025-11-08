"""测试Agent失败场景"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.services.strategy.real_agent_executor import real_agent_executor, AgentExecutionError
from app.services.market.real_market_data import real_market_data_service

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def test_agent_failure():
    """测试Agent失败的情况"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        print("=" * 100)
        print("测试Agent失败场景")
        print("=" * 100)
        print()

        # 获取市场数据
        print("1️⃣ 获取市场数据...")
        market_data = await real_market_data_service.get_complete_market_snapshot()
        btc_price = market_data.get('btc_price', {})
        if isinstance(btc_price, dict):
            price = btc_price.get('price', btc_price)
        else:
            price = btc_price
        print(f"   ✅ BTC价格: ${price:,.2f}")
        print()

        # 测试1: 正常执行
        print("2️⃣ 测试正常执行（所有Agent都应该成功）...")
        try:
            agent_outputs, agent_errors = await real_agent_executor.execute_all_agents(
                market_data=market_data,
                db=db,
                user_id=1,
                strategy_execution_id=None,
            )
            print(f"   ✅ 所有Agent执行成功")
            print(f"   - Macro Agent: {agent_outputs.get('macro', {}).get('signal')}")
            print(f"   - TA Agent: {agent_outputs.get('ta', {}).get('signal')}")
            print(f"   - OnChain Agent: {agent_outputs.get('onchain', {}).get('signal')}")
        except AgentExecutionError as e:
            print(f"   ❌ Agent执行失败: {e}")
            print(f"   - Failed Agent: {e.agent_name}")
            print(f"   - Error Message: {e.error_message}")
            print(f"   - Retry Count: {e.retry_count}")
        print()

        # 测试2: 模拟超时（通过传入错误的市场数据）
        print("3️⃣ 测试Agent失败场景（传入空数据触发错误）...")
        try:
            # 传入空的market_data来触发错误
            agent_outputs, agent_errors = await real_agent_executor.execute_all_agents(
                market_data={},  # 空数据会导致Agent失败
                db=db,
                user_id=1,
                strategy_execution_id=None,
            )
            print(f"   ✅ 所有Agent执行成功（意外！）")
        except AgentExecutionError as e:
            print(f"   ✅ Agent执行失败（符合预期）")
            print(f"   - Failed Agent: {e.agent_name}")
            print(f"   - Error Message: {e.error_message}")
            print(f"   - Retry Count: {e.retry_count}")
        except Exception as e:
            print(f"   ⚠️ 其他错误: {e}")
        print()

        print("=" * 100)
        print("✅ 测试完成")
        print("=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_agent_failure())
