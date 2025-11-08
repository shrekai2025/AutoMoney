"""检查最近为什么没有减仓操作"""

import sys
import asyncio
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.core.config import settings
from app.models.portfolio import Portfolio
from app.models.strategy_execution import StrategyExecution


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        # 获取活跃的Portfolio
        portfolio_result = await db.execute(
            select(Portfolio).where(Portfolio.is_active == True).limit(1)
        )
        portfolio = portfolio_result.scalar_one_or_none()

        if not portfolio:
            print("❌ 没有找到活跃的Portfolio")
            return

        print("=" * 100)
        print(f"📊 Portfolio: {portfolio.name}")
        print(f"   ID: {portfolio.id}")
        print(f"   当前BTC持仓比例: {(portfolio.current_btc_amount / portfolio.total_value * 100) if portfolio.total_value > 0 else 0:.2f}%")
        print("=" * 100)
        print()

        # 获取Portfolio的阈值配置
        print("🎯 Portfolio阈值配置:")
        print(f"   FG熔断阈值: {portfolio.fg_circuit_breaker_threshold}")
        print(f"   FG仓位调整阈值: {portfolio.fg_position_adjust_threshold}")
        print(f"   买入阈值: {portfolio.buy_threshold}")
        print(f"   部分卖出阈值: {portfolio.partial_sell_threshold}")
        print(f"   全部卖出阈值: {portfolio.full_sell_threshold}")
        print(f"   连续信号阈值: {portfolio.consecutive_signal_threshold}")
        print()

        # 获取最近10次执行记录
        exec_result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.portfolio_id == portfolio.id)
            .order_by(desc(StrategyExecution.execution_time))
            .limit(10)
        )
        executions = exec_result.scalars().all()

        print(f"📋 最近10次执行记录:")
        print("=" * 100)
        print()

        for i, exe in enumerate(executions, 1):
            market_snapshot = exe.market_snapshot or {}
            fg_data = market_snapshot.get("fear_greed", {})
            fg_value = fg_data.get("value", "N/A") if isinstance(fg_data, dict) else "N/A"

            conviction = exe.conviction_score if exe.conviction_score is not None else 0
            signal = exe.signal or "N/A"
            status = exe.status

            print(f"{i}. {exe.execution_time}")
            print(f"   Conviction: {conviction:.2f}")
            print(f"   Signal: {signal}")
            print(f"   F&G: {fg_value}")
            print(f"   Status: {status}")

            # 分析为什么没有SELL
            if conviction < portfolio.full_sell_threshold and signal != "SELL":
                print(f"   ⚠️ 问题: Conviction({conviction:.2f}) < 全部卖出阈值({portfolio.full_sell_threshold}), 但Signal={signal}")

                # 检查是否触发了熔断
                if isinstance(fg_value, (int, float)) and fg_value < portfolio.fg_circuit_breaker_threshold:
                    print(f"   ✓ 触发熔断: F&G({fg_value}) < 熔断阈值({portfolio.fg_circuit_breaker_threshold})")
                else:
                    print(f"   ❌ 未触发熔断: F&G({fg_value}) >= 熔断阈值({portfolio.fg_circuit_breaker_threshold})")

                # 检查连续信号
                print(f"   Portfolio连续看跌计数: {portfolio.consecutive_bearish_count}")

            elif conviction >= portfolio.partial_sell_threshold and conviction < portfolio.buy_threshold and signal != "SELL":
                print(f"   ⚠️ 问题: Conviction在部分卖出区间 [{portfolio.full_sell_threshold}, {portfolio.partial_sell_threshold}), 但Signal={signal}")

                # 检查是否触发了熔断
                if isinstance(fg_value, (int, float)) and fg_value < portfolio.fg_circuit_breaker_threshold:
                    print(f"   ✓ 触发熔断: F&G({fg_value}) < 熔断阈值({portfolio.fg_circuit_breaker_threshold})")
                else:
                    print(f"   ❌ 未触发熔断: F&G({fg_value}) >= 熔断阈值({portfolio.fg_circuit_breaker_threshold})")

            print()

        print("=" * 100)
        print("🔍 问题总结:")
        print()

        # 检查最新的执行
        if executions:
            latest = executions[0]
            conv = latest.conviction_score if latest.conviction_score is not None else 0

            if conv < portfolio.full_sell_threshold:
                print(f"最新执行: Conviction={conv:.2f} < 全部卖出阈值({portfolio.full_sell_threshold})")
                print(f"但Signal={latest.signal}")
                print()
                print("可能的原因:")
                print("1. F&G触发熔断 (检查上面的分析)")
                print("2. 连续信号计数不足 (检查consecutive_bearish_count)")
                print("3. signal_generator逻辑有问题")
                print("4. 执行时使用的阈值配置与当前不同")


if __name__ == "__main__":
    asyncio.run(main())
