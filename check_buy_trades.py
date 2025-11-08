"""检查BUY执行是否有交易记录"""

import sys
import asyncio
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.core.config import settings
from app.models.strategy_execution import StrategyExecution
from app.models.trade import Trade


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        # 查找BUY信号的执行
        exec_result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.signal == 'BUY')
            .order_by(desc(StrategyExecution.execution_time))
            .limit(1)
        )
        buy_exec = exec_result.scalar_one_or_none()

        if buy_exec:
            print('=' * 100)
            print(f'BUY执行记录:')
            print(f'  ID: {buy_exec.id}')
            print(f'  时间: {buy_exec.execution_time}')
            print(f'  Signal: {buy_exec.signal}')
            print(f'  Conviction: {buy_exec.conviction_score}')
            print('=' * 100)
            print()

            # 查找该执行的交易记录
            trade_result = await db.execute(
                select(Trade)
                .where(Trade.strategy_execution_id == str(buy_exec.id))
            )
            trades = trade_result.scalars().all()

            print(f'关联的交易记录: {len(trades)}')
            if trades:
                for trade in trades:
                    print(f'  - Trade ID: {trade.id}')
                    print(f'    类型: {trade.trade_type}')
                    print(f'    数量: {trade.amount} {trade.symbol}')
                    print(f'    价格: ${trade.price}')
                    print(f'    总价值: ${trade.total_value}')
                    print()
            else:
                print('  ❌ 没有交易记录!')
                print()
                print('问题: BUY信号执行了，但没有创建交易记录')
                print('需要检查: strategy_orchestrator 是否在BUY/SELL时创建Trade记录')

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
