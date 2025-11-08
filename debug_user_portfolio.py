"""
诊断脚本：排查用户 yeheai9906@gmail.com 的 Portfolio 为什么没有触发卖出
"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, desc
from app.models import User, Portfolio, PortfolioHolding, StrategyExecution, Trade
from decimal import Decimal

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def diagnose_user_portfolio():
    """诊断用户的Portfolio"""

    # 创建数据库连接
    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        print("=" * 100)
        print("诊断报告: 用户 yeheai9906@gmail.com 的 Portfolio")
        print("=" * 100)
        print()

        # 1. 查找用户
        print("📧 Step 1: 查找用户...")
        result = await db.execute(
            select(User).where(User.email == "yeheai9906@gmail.com")
        )
        user = result.scalar_one_or_none()

        if not user:
            print("❌ 错误: 未找到该用户！")
            return

        print(f"✅ 找到用户:")
        print(f"   - ID: {user.id}")
        print(f"   - Email: {user.email}")
        print(f"   - 全名: {user.full_name}")
        print(f"   - 角色: {user.role}")
        print(f"   - 是否激活: {user.is_active}")
        print()

        # 2. 查找用户的Portfolio
        print("💼 Step 2: 查找用户的 Portfolio...")
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user.id)
            .order_by(desc(Portfolio.created_at))
        )
        portfolios = result.scalars().all()

        if not portfolios:
            print("❌ 错误: 该用户没有任何 Portfolio！")
            return

        print(f"✅ 找到 {len(portfolios)} 个 Portfolio:")
        print()

        for idx, portfolio in enumerate(portfolios, 1):
            print(f"   Portfolio #{idx}:")
            print(f"   - ID: {portfolio.id}")
            print(f"   - 名称: {portfolio.name}")
            print(f"   - 策略: {portfolio.strategy_name}")
            print(f"   - 是否激活: {'✅ 是' if portfolio.is_active else '❌ 否'}")
            print(f"   - 初始余额: ${portfolio.initial_balance:,.2f}")
            print(f"   - 当前余额: ${portfolio.current_balance:,.2f}")
            print(f"   - 总价值: ${portfolio.total_value:,.2f}")
            print(f"   - 总盈亏: ${portfolio.total_pnl:,.2f} ({portfolio.total_pnl_percent:.2f}%)")
            print(f"   - 执行周期: {portfolio.rebalance_period_minutes} 分钟")
            print(f"   - 上次执行时间: {portfolio.last_execution_time}")
            print(f"   - 上次信念分数: {portfolio.last_conviction_score}")
            print(f"   - 连续看涨次数: {portfolio.consecutive_bullish_count}")
            print(f"   - 连续看跌次数: {portfolio.consecutive_bearish_count}")

            # Agent 权重配置
            if portfolio.agent_weights:
                print(f"   - Agent权重: {portfolio.agent_weights}")

            # 连续信号配置
            print(f"   - 连续信号阈值: {portfolio.consecutive_signal_threshold}")
            print(f"   - 加速乘数范围: {portfolio.acceleration_multiplier_min} - {portfolio.acceleration_multiplier_max}")
            print()

        # 3. 查看持仓情况
        print("🪙 Step 3: 查看持仓情况...")

        for portfolio in portfolios:
            result = await db.execute(
                select(PortfolioHolding)
                .where(PortfolioHolding.portfolio_id == portfolio.id)
            )
            holdings = result.scalars().all()

            print(f"\n   Portfolio '{portfolio.name}' 的持仓:")

            if not holdings:
                print("      ❌ 无持仓")
            else:
                total_value = Decimal("0")
                for holding in holdings:
                    print(f"      - {holding.symbol}: {holding.amount:.8f} 枚")
                    print(f"        市场价值: ${holding.market_value:,.2f}")
                    print(f"        平均买价: ${holding.avg_buy_price:,.2f}")
                    print(f"        当前价格: ${holding.current_price:,.2f}")
                    print(f"        成本基础: ${holding.cost_basis:,.2f}")
                    print(f"        未实现盈亏: ${holding.unrealized_pnl:,.2f} ({holding.unrealized_pnl_percent:.2f}%)")
                    total_value += holding.market_value

                # 计算持仓比例
                if portfolio.total_value > 0:
                    position_ratio = (total_value / portfolio.total_value) * 100
                    print(f"\n      📊 持仓比例: {position_ratio:.2f}%")
                    print(f"      💵 现金比例: {100 - position_ratio:.2f}%")

                    if position_ratio < 1:
                        print(f"      ⚠️  警告: 持仓比例 < 1%，可能无法触发卖出！")
                    elif position_ratio >= 1:
                        print(f"      ✅ 持仓比例 ≥ 1%，满足卖出条件")

        print()

        # 4. 查看策略执行记录
        print("📋 Step 4: 查看最近的策略执行记录...")

        for portfolio in portfolios:
            # 查找与该Portfolio相关的执行记录
            result = await db.execute(
                select(StrategyExecution)
                .join(Trade, Trade.execution_id == StrategyExecution.id, isouter=True)
                .where(Trade.portfolio_id == portfolio.id)
                .order_by(desc(StrategyExecution.execution_time))
                .limit(5)
            )
            executions = result.scalars().all()

            print(f"\n   Portfolio '{portfolio.name}' 的最近5次执行:")

            if not executions:
                print("      ❌ 没有执行记录")
            else:
                for exec in executions:
                    print(f"\n      执行时间: {exec.execution_time}")
                    print(f"      - 执行ID: {exec.id}")
                    print(f"      - 状态: {exec.status}")
                    print(f"      - 信念分数: {exec.conviction_score:.2f}")
                    print(f"      - 信号: {exec.signal}")
                    print(f"      - 信号强度: {exec.signal_strength:.4f}")
                    print(f"      - 仓位大小: {exec.position_size:.4f} ({exec.position_size * 100:.2f}%)")
                    print(f"      - 风险等级: {exec.risk_level}")

                    if exec.error_message:
                        print(f"      - ❌ 错误: {exec.error_message}")

                    if exec.llm_summary:
                        print(f"      - 总结: {exec.llm_summary[:150]}...")

        print()

        # 5. 查看交易记录
        print("💰 Step 5: 查看最近的交易记录...")

        for portfolio in portfolios:
            result = await db.execute(
                select(Trade)
                .where(Trade.portfolio_id == portfolio.id)
                .order_by(desc(Trade.executed_at))
                .limit(10)
            )
            trades = result.scalars().all()

            print(f"\n   Portfolio '{portfolio.name}' 的最近10笔交易:")

            if not trades:
                print("      ❌ 没有交易记录")
            else:
                for trade in trades:
                    trade_type_emoji = "📈" if trade.trade_type == "BUY" else "📉"
                    print(f"\n      {trade_type_emoji} {trade.trade_type} - {trade.executed_at}")
                    print(f"      - 交易ID: {trade.id}")
                    print(f"      - 币种: {trade.symbol}")
                    print(f"      - 数量: {trade.amount:.8f}")
                    print(f"      - 价格: ${trade.price:,.2f}")
                    print(f"      - 总值: ${trade.total_value:,.2f}")
                    print(f"      - 手续费: ${trade.fee:.2f}")
                    if trade.conviction_score is not None:
                        print(f"      - 信念分数: {trade.conviction_score:.2f}")
                    print(f"      - 原因: {trade.reason}")

                    if trade.realized_pnl:
                        pnl_emoji = "✅" if trade.realized_pnl > 0 else "❌"
                        print(f"      - {pnl_emoji} 已实现盈亏: ${trade.realized_pnl:,.2f} ({trade.realized_pnl_percent:.2f}%)")

        print()
        print("=" * 100)
        print("🔍 诊断结论:")
        print("=" * 100)

        # 分析诊断结果
        active_portfolios = [p for p in portfolios if p.is_active]

        if not active_portfolios:
            print("\n❌ 问题: 用户的所有 Portfolio 都未激活！")
            print("   解决方案: 需要激活 Portfolio 才能执行策略")
        else:
            print(f"\n✅ 有 {len(active_portfolios)} 个激活的 Portfolio")

            # 检查是否有执行记录
            for portfolio in active_portfolios:
                result = await db.execute(
                    select(StrategyExecution)
                    .join(Trade, Trade.execution_id == StrategyExecution.id, isouter=True)
                    .where(Trade.portfolio_id == portfolio.id)
                    .order_by(desc(StrategyExecution.execution_time))
                    .limit(1)
                )
                last_exec = result.scalar_one_or_none()

                if not last_exec:
                    print(f"\n⚠️  Portfolio '{portfolio.name}': 从未执行过策略")
                    print(f"   可能原因: ")
                    print(f"   1. 调度器未启动")
                    print(f"   2. 从未手动触发")
                elif last_exec.conviction_score and last_exec.conviction_score < 40:
                    print(f"\n✅ Portfolio '{portfolio.name}': 最近信念分数 {last_exec.conviction_score:.2f} < 40")
                    print(f"   信号: {last_exec.signal}")

                    if last_exec.signal == "SELL":
                        # 检查持仓
                        result = await db.execute(
                            select(PortfolioHolding)
                            .where(PortfolioHolding.portfolio_id == portfolio.id)
                        )
                        holdings = result.scalars().all()

                        total_holding_value = sum(h.market_value for h in holdings)
                        if portfolio.total_value > 0:
                            position_ratio = float(total_holding_value / portfolio.total_value)

                            if position_ratio < 0.01:
                                print(f"   ❌ 问题: 持仓比例 {position_ratio * 100:.2f}% < 1%，不满足卖出条件！")
                                print(f"   📍 代码位置: signal_generator.py:394")
                            else:
                                print(f"   ✅ 持仓比例 {position_ratio * 100:.2f}% ≥ 1%")

                                # 检查是否有交易记录
                                result = await db.execute(
                                    select(Trade)
                                    .where(
                                        Trade.portfolio_id == portfolio.id,
                                        Trade.execution_id == last_exec.id
                                    )
                                )
                                trades = result.scalars().all()

                                if trades:
                                    print(f"   ✅ 已执行交易: {len(trades)} 笔")
                                else:
                                    print(f"   ❌ 问题: 生成了SELL信号但没有执行交易！")
                                    print(f"   可能原因: ")
                                    print(f"   1. should_execute = False (检查熔断机制)")
                                    print(f"   2. 交易执行时出错")
                                    if last_exec.error_message:
                                        print(f"   3. 错误信息: {last_exec.error_message}")
                    else:
                        print(f"   ℹ️  信号为 {last_exec.signal}，非 SELL")

        print("\n" + "=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(diagnose_user_portfolio())
