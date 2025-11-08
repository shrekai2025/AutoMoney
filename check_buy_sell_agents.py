"""检查BUY/SELL信号的执行是否有agent记录"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.strategy_execution import StrategyExecution
from app.models.agent_execution import AgentExecution

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def check():
    """检查BUY/SELL信号的agent记录"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("检查BUY/SELL信号执行的Agent记录")
    print("=" * 100)
    print()

    async with AsyncSessionLocal() as db:
        # 查找所有BUY或SELL信号的执行
        result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.signal.in_(['BUY', 'SELL']))
            .order_by(StrategyExecution.execution_time.desc())
            .limit(10)
        )
        executions = result.scalars().all()

        print(f"找到{len(executions)}个BUY/SELL信号的执行:")
        print()

        for exe in executions:
            # 查询agent executions
            agent_result = await db.execute(
                select(AgentExecution)
                .where(AgentExecution.strategy_execution_id == str(exe.id))
            )
            agents = agent_result.scalars().all()

            print(f"ID: {exe.id}")
            print(f"  时间: {exe.execution_time}")
            print(f"  Signal: {exe.signal}")
            print(f"  Conviction: {exe.conviction_score}")
            print(f"  Status: {exe.status}")
            print(f"  Agent Executions: {len(agents)}")

            if agents:
                for agent in agents:
                    print(f"    - {agent.agent_name}: {agent.signal}, score={agent.score}")
            else:
                print(f"    ❌ 无Agent执行记录")

            print()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
