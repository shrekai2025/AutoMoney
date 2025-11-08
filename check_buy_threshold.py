"""检查购买阈值逻辑"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.models.strategy_execution import StrategyExecution
from app.models.portfolio import Portfolio, Trade
from decimal import Decimal

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def check_buy_threshold():
    """检查购买阈值逻辑"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🔍 检查购买阈值逻辑")
    print("=" * 100)
    print()

    async with AsyncSessionLocal() as db:
        # 1. 获取Portfolio信息
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ Portfolio不存在")
            return

        print(f"📊 Portfolio信息:")
        print(f"   名称: {portfolio.name}")
        print(f"   当前余额: ${float(portfolio.current_balance):.2f}")
        print(f"   总价值: ${float(portfolio.total_value):.2f}")
        print(f"   活跃状态: {portfolio.is_active}")
        print()

        # 2. 查询最近10条执行记录
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == portfolio.user_id)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(10)
        )
        result = await db.execute(stmt)
        executions = result.scalars().all()

        print(f"📋 最近10条执行记录:")
        print("-" * 100)

        buy_threshold = 50.0  # 购买阈值

        for i, exe in enumerate(executions, 1):
            status_icon = "✅" if exe.status == "completed" else "❌"
            conviction = exe.conviction_score if exe.conviction_score is not None else 0

            # 判断是否应该触发购买
            should_buy = conviction >= buy_threshold and exe.status == "completed"
            buy_icon = "🟢" if should_buy else "⚪"

            print(f"\n{buy_icon} {status_icon} 执行 {i}:")
            print(f"   时间: {exe.execution_time}")
            print(f"   状态: {exe.status}")
            print(f"   Conviction Score: {conviction:.2f}")
            print(f"   Signal: {exe.signal}")
            print(f"   Position Size: {exe.position_size}")

            if should_buy:
                print(f"   ✅ 满足购买条件 (>= {buy_threshold})")
            else:
                if exe.status != "completed":
                    print(f"   ⚠️ 执行失败，未触发购买")
                elif conviction < buy_threshold:
                    print(f"   ⚠️ Conviction Score < {buy_threshold}，未满足购买阈值")

            # 查询是否有对应的交易
            trade_result = await db.execute(
                select(Trade)
                .where(Trade.execution_id == str(exe.id))
                .order_by(Trade.executed_at.desc())
            )
            trades = trade_result.scalars().all()

            if trades:
                print(f"   📈 交易记录 ({len(trades)}条):")
                for trade in trades:
                    print(f"      - {trade.trade_type}: {float(trade.amount):.8f} {trade.symbol} @ ${float(trade.price):.2f}")
                    print(f"        总额: ${float(trade.total_value):.2f}")
            else:
                print(f"   📭 无交易记录")

                # 分析为什么没有交易
                if should_buy:
                    print(f"   ⚠️ 警告: 满足购买条件但没有生成交易！")
                    print(f"   需要检查:")
                    print(f"      1. 信号生成逻辑")
                    print(f"      2. 交易执行逻辑")
                    print(f"      3. position_size计算")

        print()
        print("=" * 100)
        print("📊 阈值逻辑分析")
        print("=" * 100)
        print()

        # 统计满足购买条件但没有交易的情况
        no_trade_count = 0
        should_buy_count = 0

        for exe in executions:
            if exe.status == "completed":
                conviction = exe.conviction_score if exe.conviction_score is not None else 0

                if conviction >= buy_threshold:
                    should_buy_count += 1

                    # 检查是否有交易
                    trade_result = await db.execute(
                        select(Trade).where(Trade.execution_id == str(exe.id))
                    )
                    trades = trade_result.scalars().all()

                    if not trades:
                        no_trade_count += 1

        print(f"统计结果:")
        print(f"   满足购买条件的执行: {should_buy_count}条")
        print(f"   其中没有生成交易: {no_trade_count}条")

        if no_trade_count > 0:
            print(f"\n⚠️ 发现问题: {no_trade_count}条满足购买条件的执行没有生成交易！")
        else:
            print(f"\n✅ 所有满足条件的执行都生成了交易")

        print()
        print("=" * 100)
        print("🔍 深入分析: 检查信号生成逻辑")
        print("=" * 100)
        print()

        # 查看最近一条满足购买条件但没有交易的执行
        for exe in executions:
            if exe.status == "completed":
                conviction = exe.conviction_score if exe.conviction_score is not None else 0

                if conviction >= buy_threshold:
                    # 检查是否有交易
                    trade_result = await db.execute(
                        select(Trade).where(Trade.execution_id == str(exe.id))
                    )
                    trades = trade_result.scalars().all()

                    if not trades:
                        print(f"📋 详细分析执行 {exe.id}:")
                        print(f"   时间: {exe.execution_time}")
                        print(f"   Conviction Score: {conviction:.2f} (>= {buy_threshold} ✅)")
                        print(f"   Signal: {exe.signal}")
                        print(f"   Signal Strength: {exe.signal_strength}")
                        print(f"   Position Size: {exe.position_size}")
                        print(f"   Risk Level: {exe.risk_level}")
                        print()

                        print(f"   分析:")
                        print(f"   1. Signal是什么? {exe.signal}")

                        if exe.signal == "HOLD":
                            print(f"      ⚠️ Signal是HOLD - 这是问题所在！")
                            print(f"      即使Conviction Score >= 50，如果Signal是HOLD，就不会买入")
                            print()
                            print(f"   2. 为什么Signal是HOLD?")
                            print(f"      可能原因:")
                            print(f"      - Signal生成逻辑有问题")
                            print(f"      - 信号强度(signal_strength)太低")
                            print(f"      - 其他条件未满足")
                        elif exe.signal == "BUY":
                            print(f"      ✅ Signal是BUY，应该会买入")
                            print(f"      ⚠️ 但是没有交易记录 - 检查交易执行逻辑")
                            if exe.position_size is None or exe.position_size == 0:
                                print(f"      ⚠️ Position Size是 {exe.position_size} - 可能因此没有交易")
                        elif exe.signal == "SELL":
                            print(f"      Signal是SELL - 不会买入")

                        print()
                        break  # 只分析第一条

        print()
        print("=" * 100)
        print("📝 检查完成")
        print("=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_buy_threshold())
