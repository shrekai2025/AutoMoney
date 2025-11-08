"""检查最近执行的详细市场数据"""

import sys
import asyncio
import json
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.core.config import settings
from app.models.strategy_execution import StrategyExecution
from app.models.portfolio import Portfolio


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        # 获取Portfolio
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"
        portfolio_result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = portfolio_result.scalar_one()

        print("=" * 100)
        print(f"Portfolio阈值配置:")
        print(f"  FG熔断阈值: {portfolio.fg_circuit_breaker_threshold}")
        print(f"  全部卖出阈值: {portfolio.full_sell_threshold}")
        print("=" * 100)
        print()

        # 获取最近5次执行 (使用user_id)
        exec_result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.user_id == portfolio.user_id)
            .order_by(desc(StrategyExecution.execution_time))
            .limit(5)
        )
        executions = exec_result.scalars().all()

        for i, exe in enumerate(executions, 1):
            print(f"\n{'='*100}")
            print(f"执行 #{i}: {exe.execution_time}")
            print(f"{'='*100}")
            print(f"Conviction Score: {exe.conviction_score}")
            print(f"Signal: {exe.signal}")
            print(f"Status: {exe.status}")
            print()

            # 详细检查market_snapshot
            if exe.market_snapshot:
                fg_data = exe.market_snapshot.get("fear_greed", {})
                fg_value = fg_data.get("value") if isinstance(fg_data, dict) else None

                print(f"Market Snapshot:")
                print(f"  Fear & Greed: {fg_value}")
                print(f"  BTC Price Change 24h: {exe.market_snapshot.get('btc_price_change_24h', 'N/A')}")

                macro = exe.market_snapshot.get("macro", {})
                if isinstance(macro, dict):
                    print(f"  DXY Index: {macro.get('dxy_index', 'N/A')}")

                print()
                print(f"熔断检查:")
                print(f"  F&G({fg_value}) < 熔断阈值({portfolio.fg_circuit_breaker_threshold})? {fg_value < portfolio.fg_circuit_breaker_threshold if fg_value is not None else 'N/A'}")

                if fg_value is not None and fg_value < portfolio.fg_circuit_breaker_threshold:
                    print(f"  ✅ 熔断触发 → Signal=HOLD")
                else:
                    print(f"  ❌ 熔断未触发")

                    # 如果熔断未触发,检查为什么Signal是HOLD
                    if exe.conviction_score and exe.conviction_score < portfolio.full_sell_threshold:
                        print(f"  ⚠️ Conviction({exe.conviction_score:.2f}) < 全部卖出阈值({portfolio.full_sell_threshold})")
                        print(f"  预期Signal: SELL")
                        print(f"  实际Signal: {exe.signal}")
                        print(f"  ❌ 不匹配!")

            else:
                print("Market Snapshot: None")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
