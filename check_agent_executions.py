"""检查历史agent执行记录"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.models.strategy_execution import StrategyExecution
from app.models.agent_execution import AgentExecution

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def check_history():
    """检查历史agent执行"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        # 获取最近几次completed的strategy执行
        result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.status == "completed")
            .order_by(StrategyExecution.execution_time.desc())
            .limit(5)
        )
        strategies = result.scalars().all()

        print("=" * 100)
        print("最近5次completed执行的Agent记录")
        print("=" * 100)
        print()

        for i, strategy in enumerate(strategies, 1):
            print(f"{i}. Strategy Execution: {strategy.execution_time}")
            print(f"   ID: {strategy.id}")
            print(f"   Conviction: {strategy.conviction_score}")
            print(f"   Signal: {strategy.signal}")
            print()

            # 查询关联的agent executions
            agent_result = await db.execute(
                select(AgentExecution)
                .where(AgentExecution.strategy_execution_id == str(strategy.id))
                .order_by(AgentExecution.agent_name)
            )
            agents = agent_result.scalars().all()

            if agents:
                print(f"   Agent Executions ({len(agents)}个):")
                total_score = 0
                total_conf = 0
                for agent in agents:
                    print(f"     • {agent.agent_name}: signal={agent.signal}, score={agent.score}, conf={agent.confidence}")
                    total_score += agent.score * agent.confidence
                    total_conf += agent.confidence

                if total_conf > 0:
                    weighted = total_score / total_conf
                    conviction = 50 + (weighted / 2)
                    print(f"   计算: 加权分数={weighted:.2f}, Conviction={conviction:.2f}")
            else:
                print(f"   ❌ 无Agent执行记录")

            print()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_history())
