"""检查阈值修改历史"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.models.portfolio import Portfolio
from app.models.strategy_execution import StrategyExecution
from datetime import datetime

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def check_history():
    """检查阈值修改历史"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🕐 阈值修改历史分析")
    print("=" * 100)
    print()

    async with AsyncSessionLocal() as db:
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

        # 获取Portfolio
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        print(f"📊 当前Portfolio阈值配置:")
        print(f"   FG熔断阈值: {portfolio.fg_circuit_breaker_threshold}")
        print(f"   FG仓位调整阈值: {portfolio.fg_position_adjust_threshold}")
        print(f"   买入阈值: {portfolio.buy_threshold}")
        print(f"   部分减仓阈值: {portfolio.partial_sell_threshold}")
        print(f"   全部清仓阈值: {portfolio.full_sell_threshold}")
        print()

        # 获取最近的执行记录
        exec_result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.user_id == portfolio.user_id)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(20)
        )
        executions = exec_result.scalars().all()

        print(f"📜 最近20次执行记录:")
        print()

        for i, exe in enumerate(executions, 1):
            # 获取该执行时的市场快照
            market_snapshot = exe.market_snapshot or {}
            fg_data = market_snapshot.get("fear_greed", {})

            if isinstance(fg_data, dict):
                fg_value = fg_data.get("value", "N/A")
            else:
                fg_value = "N/A"

            print(f"{i}. {exe.execution_time}")
            print(f"   Conviction: {exe.conviction_score:.2f}")
            print(f"   Signal: {exe.signal}")
            print(f"   F&G: {fg_value}")
            print(f"   Status: {exe.status}")

            # 分析为什么是HOLD
            if exe.signal == "HOLD" and exe.conviction_score is not None:
                # 使用当前阈值分析
                if fg_value != "N/A" and fg_value < portfolio.fg_circuit_breaker_threshold:
                    print(f"   💡 分析: F&G({fg_value}) < 熔断阈值({portfolio.fg_circuit_breaker_threshold}) → 熔断触发")
                elif exe.conviction_score < portfolio.full_sell_threshold:
                    print(f"   ⚠️  疑问: Conviction({exe.conviction_score:.2f}) < 全部清仓阈值({portfolio.full_sell_threshold}) 应该是SELL，但是是HOLD")
                elif exe.conviction_score >= portfolio.buy_threshold:
                    print(f"   ⚠️  疑问: Conviction({exe.conviction_score:.2f}) >= 买入阈值({portfolio.buy_threshold}) 应该是BUY，但是是HOLD")
                else:
                    print(f"   ⚠️  疑问: Conviction({exe.conviction_score:.2f}) 在 {portfolio.full_sell_threshold}-{portfolio.partial_sell_threshold} 应该是SELL（部分减仓），但是是HOLD")

            print()

        print("=" * 100)
        print("🔍 关键发现:")
        print("=" * 100)
        print()

        # 统计F&G值分布
        fg_values = []
        for exe in executions:
            market_snapshot = exe.market_snapshot or {}
            fg_data = market_snapshot.get("fear_greed", {})
            if isinstance(fg_data, dict):
                fg_value = fg_data.get("value")
                if fg_value is not None:
                    fg_values.append(fg_value)

        if fg_values:
            avg_fg = sum(fg_values) / len(fg_values)
            min_fg = min(fg_values)
            max_fg = max(fg_values)

            print(f"最近{len(fg_values)}次执行的F&G统计:")
            print(f"  最小值: {min_fg}")
            print(f"  最大值: {max_fg}")
            print(f"  平均值: {avg_fg:.2f}")
            print()

            # 检查有多少次触发熔断
            circuit_breaker_count = sum(1 for v in fg_values if v < portfolio.fg_circuit_breaker_threshold)
            print(f"触发熔断次数 (F&G < {portfolio.fg_circuit_breaker_threshold}): {circuit_breaker_count}/{len(fg_values)}")
            print()

            if circuit_breaker_count == len(fg_values):
                print("💡 结论: **所有执行都触发了熔断**，这就是为什么都是HOLD信号！")
            elif circuit_breaker_count > 0:
                print(f"💡 结论: 有 {circuit_breaker_count} 次触发了熔断")
            else:
                print("💡 结论: 没有触发熔断，但信号仍然是HOLD - 需要进一步调查")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_history())
