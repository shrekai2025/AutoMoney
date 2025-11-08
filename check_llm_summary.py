"""检查最新执行记录的llm_summary字段"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.core.config import settings
from app.models.strategy_execution import StrategyExecution


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        print("=" * 100)
        print("检查最新策略执行的llm_summary字段")
        print("=" * 100)
        print()

        # 获取最新的3条执行记录
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.status == "completed")
            .order_by(StrategyExecution.execution_time.desc())
            .limit(3)
        )
        result = await db.execute(stmt)
        executions = result.scalars().all()

        for i, execution in enumerate(executions, 1):
            print(f"执行记录 #{i}:")
            print(f"  执行时间: {execution.execution_time}")
            print(f"  Conviction Score: {execution.conviction_score}")
            print(f"  Signal: {execution.signal}")
            print(f"  Status: {execution.status}")
            print(f"  llm_summary: {execution.llm_summary}")
            print()

        print("=" * 100)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
