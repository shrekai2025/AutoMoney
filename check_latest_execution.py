"""检查最新一次执行"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc, text
from app.models.strategy_execution import StrategyExecution
from app.models.agent_execution import AgentExecution

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def check_latest():
    """检查最新一次执行"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        # 获取最新一次执行
        result = await db.execute(
            select(StrategyExecution)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()

        if not latest:
            print("No executions found")
            return

        print("=" * 100)
        print(f"最新策略执行 (ID: {latest.id})")
        print("=" * 100)
        print()

        print(f"执行时间: {latest.execution_time}")
        print(f"Conviction Score: {latest.conviction_score}")
        print(f"Signal: {latest.signal}")
        print(f"Signal Strength: {latest.signal_strength}")
        print(f"Position Size: {latest.position_size}")
        print(f"Status: {latest.status}")
        print()

        # 获取关联的agent executions
        agent_result = await db.execute(
            select(AgentExecution)
            .where(AgentExecution.strategy_execution_id == str(latest.id))
            .order_by(AgentExecution.agent_name)
        )
        agents = agent_result.scalars().all()

        if agents:
            print(f"Agent执行 ({len(agents)}个):")
            print()

            total_score = 0
            total_confidence = 0
            for agent in agents:
                print(f"  • {agent.agent_name}:")
                print(f"      Signal: {agent.signal}")
                print(f"      Score: {agent.score}")
                print(f"      Confidence: {agent.confidence}")
                print()

                total_score += agent.score * agent.confidence
                total_confidence += agent.confidence

            if total_confidence > 0:
                weighted_score = total_score / total_confidence
                conviction = 50 + (weighted_score / 2)

                print(f"📊 手动计算:")
                print(f"   加权分数: {weighted_score:.2f}")
                print(f"   预期Conviction: {conviction:.2f}")
                print(f"   实际Conviction: {latest.conviction_score}")
                print()

                if abs(conviction - latest.conviction_score) > 0.1:
                    print(f"⚠️  警告: 计算结果不匹配！")
                else:
                    print(f"✅ 计算结果匹配")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_latest())
