"""全面诊断：为什么没有执行交易"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc, func
from app.models.portfolio import Portfolio, PortfolioHolding, Trade
from app.models.strategy_execution import StrategyExecution
from app.services.decision.signal_generator import signal_generator
from app.services.market.real_market_data import real_market_data_service
from datetime import datetime, timedelta

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def diagnose_no_trades():
    """全面诊断为什么没有执行交易"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 120)
    print("🔍 全面诊断：为什么没有执行交易")
    print("=" * 120)
    print()

    async with AsyncSessionLocal() as db:
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

        # ========================================
        # 1. Portfolio基本信息
        # ========================================
        print("=" * 120)
        print("📊 1. Portfolio基本信息")
        print("=" * 120)
        print()

        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ Portfolio不存在")
            return

        print(f"Portfolio名称: {portfolio.name}")
        print(f"用户ID: {portfolio.user_id}")
        print(f"当前余额: ${float(portfolio.current_balance):,.2f}")
        print(f"总价值: ${float(portfolio.total_value):,.2f}")
        print(f"是否激活: {portfolio.is_active}")
        print(f"初始BTC数量: {portfolio.initial_btc_amount}")
        print()

        if not portfolio.is_active:
            print("⚠️  Portfolio未激活 - 这可能是问题所在！")
            print()

        # ========================================
        # 2. 持仓情况
        # ========================================
        print("=" * 120)
        print("💰 2. 持仓情况")
        print("=" * 120)
        print()

        holdings_result = await db.execute(
            select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
        )
        holdings = holdings_result.scalars().all()

        if not holdings:
            print("📭 当前无持仓")
        else:
            for holding in holdings:
                print(f"  • {holding.symbol}:")
                print(f"    数量: {float(holding.amount):.8f}")
                print(f"    市值: ${float(holding.market_value):,.2f}")
                print(f"    平均买入价: ${float(holding.avg_buy_price):,.2f}")
                print(f"    当前价格: ${float(holding.current_price):,.2f}")
                print(f"    未实现盈亏: ${float(holding.unrealized_pnl):,.2f} ({float(holding.unrealized_pnl_percent):.2f}%)")
                print()

        # 计算BTC持仓比例
        total_value = float(portfolio.total_value)
        if total_value > 0:
            btc_value = sum(float(h.market_value) for h in holdings if h.symbol == "BTC")
            current_position = btc_value / total_value
            print(f"📈 BTC持仓比例: {current_position * 100:.2f}%")
        else:
            current_position = 0.0
            print(f"📈 BTC持仓比例: 0%")
        print()

        # ========================================
        # 3. 交易历史
        # ========================================
        print("=" * 120)
        print("📜 3. 交易历史")
        print("=" * 120)
        print()

        # 统计总交易数
        trade_count_result = await db.execute(
            select(func.count(Trade.id)).where(Trade.portfolio_id == portfolio_id)
        )
        total_trades = trade_count_result.scalar()

        print(f"总交易数: {total_trades}")
        print()

        if total_trades == 0:
            print("⚠️  从未执行过任何交易！")
            print()
        else:
            # 显示最近5笔交易
            recent_trades_result = await db.execute(
                select(Trade)
                .where(Trade.portfolio_id == portfolio_id)
                .order_by(Trade.executed_at.desc())
                .limit(5)
            )
            recent_trades = recent_trades_result.scalars().all()

            print("最近5笔交易:")
            for i, trade in enumerate(recent_trades, 1):
                print(f"{i}. {trade.executed_at}")
                print(f"   类型: {trade.trade_type}")
                print(f"   {trade.symbol}: {float(trade.amount):.8f} @ ${float(trade.price):,.2f}")
                print(f"   总额: ${float(trade.total_value):,.2f}")
                print()

        # ========================================
        # 4. 策略执行历史
        # ========================================
        print("=" * 120)
        print("⚙️  4. 策略执行历史")
        print("=" * 120)
        print()

        # 统计执行次数
        exec_count_result = await db.execute(
            select(func.count(StrategyExecution.id))
            .where(StrategyExecution.user_id == portfolio.user_id)
        )
        total_executions = exec_count_result.scalar()

        print(f"总执行次数: {total_executions}")
        print()

        # 统计各状态的执行
        status_result = await db.execute(
            select(
                StrategyExecution.status,
                func.count(StrategyExecution.id)
            )
            .where(StrategyExecution.user_id == portfolio.user_id)
            .group_by(StrategyExecution.status)
        )
        status_counts = status_result.all()

        print("执行状态统计:")
        for status, count in status_counts:
            print(f"  • {status}: {count}")
        print()

        # 最近10条执行记录
        recent_exec_result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.user_id == portfolio.user_id)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(10)
        )
        recent_execs = recent_exec_result.scalars().all()

        print("最近10条执行记录:")
        print("-" * 120)
        print()

        for i, exe in enumerate(recent_execs, 1):
            print(f"{i}. {exe.execution_time}")
            print(f"   状态: {exe.status}")

            if exe.conviction_score is not None:
                print(f"   Conviction Score: {exe.conviction_score:.2f}")
            else:
                print(f"   Conviction Score: N/A")

            print(f"   信号: {exe.signal}")

            if exe.signal_strength is not None:
                print(f"   信号强度: {exe.signal_strength:.4f}")

            if exe.position_size is not None:
                print(f"   仓位大小: {exe.position_size:.6f} ({exe.position_size * 100:.4f}%)")

            print(f"   风险等级: {exe.risk_level}")

            # 检查是否有关联的交易
            trade_result = await db.execute(
                select(Trade).where(Trade.execution_id == str(exe.id))
            )
            trades = trade_result.scalars().all()

            if trades:
                print(f"   ✅ 已执行 {len(trades)} 笔交易")
            else:
                print(f"   ❌ 无交易执行")

                # 分析为什么没有交易
                if exe.signal == "HOLD":
                    print(f"      → 原因: 信号为HOLD")
                elif exe.status == "failed":
                    print(f"      → 原因: 执行失败")
                    if exe.error_message:
                        print(f"      → 错误: {exe.error_message}")
                else:
                    print(f"      → ⚠️  疑似问题: 信号为{exe.signal}但未执行交易")

            print()

        # ========================================
        # 5. 当前市场数据
        # ========================================
        print("=" * 120)
        print("📡 5. 当前市场数据")
        print("=" * 120)
        print()

        try:
            market_data = await real_market_data_service.get_complete_market_snapshot()

            btc_price_obj = market_data.get("btc_price", {})
            if isinstance(btc_price_obj, dict):
                btc_price = btc_price_obj.get("price", 0)
                price_change = btc_price_obj.get("price_change_24h", 0)
            else:
                btc_price = btc_price_obj
                price_change = 0

            fg_data = market_data.get("fear_greed", {})
            fg_value = fg_data.get("value", "N/A")

            print(f"BTC价格: ${btc_price:,.2f}")
            print(f"24h变化: {price_change:.2f}%")
            print(f"Fear & Greed: {fg_value}")
            print()

        except Exception as e:
            print(f"❌ 获取市场数据失败: {e}")
            print()

        # ========================================
        # 6. 模拟信号生成
        # ========================================
        print("=" * 120)
        print("🧪 6. 模拟信号生成（基于当前配置）")
        print("=" * 120)
        print()

        print("当前阈值配置:")
        print(f"  • FG熔断阈值: {portfolio.fg_circuit_breaker_threshold}")
        print(f"  • FG仓位调整阈值: {portfolio.fg_position_adjust_threshold}")
        print(f"  • 买入阈值: {portfolio.buy_threshold}")
        print(f"  • 部分减仓阈值: {portfolio.partial_sell_threshold}")
        print(f"  • 全部清仓阈值: {portfolio.full_sell_threshold}")
        print()

        # 使用最近一次执行的conviction_score进行模拟
        if recent_execs and recent_execs[0].conviction_score is not None:
            latest_conviction = recent_execs[0].conviction_score

            print(f"使用最近一次的Conviction Score ({latest_conviction:.2f}) 进行模拟:")
            print()

            try:
                portfolio_state = {
                    "consecutive_bullish_count": portfolio.consecutive_bullish_count or 0,
                    "last_conviction_score": portfolio.last_conviction_score or 50,
                    "consecutive_signal_threshold": portfolio.consecutive_signal_threshold or 30,
                    "acceleration_multiplier_min": portfolio.acceleration_multiplier_min or 1.1,
                    "acceleration_multiplier_max": portfolio.acceleration_multiplier_max or 2.0,
                    "fg_circuit_breaker_threshold": portfolio.fg_circuit_breaker_threshold,
                    "fg_position_adjust_threshold": portfolio.fg_position_adjust_threshold,
                    "buy_threshold": portfolio.buy_threshold,
                    "partial_sell_threshold": portfolio.partial_sell_threshold,
                    "full_sell_threshold": portfolio.full_sell_threshold,
                }

                market_data_input = {
                    "btc_price_change_24h": price_change,
                    "fear_greed": fg_data,
                    "macro": market_data.get("macro", {}),
                }

                signal_result = signal_generator.generate_signal(
                    conviction_score=latest_conviction,
                    market_data=market_data_input,
                    current_position=current_position,
                    portfolio_state=portfolio_state,
                )

                print(f"生成的信号: {signal_result.signal.value}")
                print(f"信号强度: {signal_result.signal_strength:.4f}")
                print(f"仓位大小: {signal_result.position_size:.6f} ({signal_result.position_size * 100:.4f}%)")
                print(f"应该执行: {signal_result.should_execute}")
                print(f"风险等级: {signal_result.risk_level.value}")
                print()

                print("决策原因:")
                for reason in signal_result.reasons:
                    print(f"  • {reason}")
                print()

                if signal_result.warnings:
                    print("警告:")
                    for warning in signal_result.warnings:
                        print(f"  • {warning}")
                    print()

                if not signal_result.should_execute and signal_result.signal.value != "HOLD":
                    print("⚠️  信号不会执行的原因:")
                    if signal_result.signal.value == "BUY":
                        if current_position > 0.95:
                            print(f"  • 当前持仓 ({current_position*100:.2f}%) > 95%，接近满仓")
                        if signal_result.position_size < 0.002:
                            print(f"  • 仓位大小 ({signal_result.position_size:.6f}) < 0.002，仓位太小")
                    elif signal_result.signal.value == "SELL":
                        if current_position < 0.01:
                            print(f"  • 当前持仓 ({current_position*100:.2f}%) < 1%，几乎没有持仓")
                    print()

            except Exception as e:
                print(f"❌ 模拟信号生成失败: {e}")
                import traceback
                traceback.print_exc()
                print()

        # ========================================
        # 7. 问题总结
        # ========================================
        print("=" * 120)
        print("📋 7. 问题总结与建议")
        print("=" * 120)
        print()

        issues_found = []
        suggestions = []

        # 检查Portfolio是否激活
        if not portfolio.is_active:
            issues_found.append("Portfolio未激活")
            suggestions.append("在Admin Panel中激活该Portfolio")

        # 检查是否有执行记录
        if total_executions == 0:
            issues_found.append("从未执行过策略")
            suggestions.append("检查定时任务是否正常运行")
        else:
            # 检查最近执行是否都是HOLD
            recent_signals = [exe.signal for exe in recent_execs[:10]]
            if all(s == "HOLD" for s in recent_signals):
                issues_found.append("最近10次执行全部为HOLD信号")
                suggestions.append("检查阈值配置是否过于保守")
                suggestions.append(f"当前买入阈值为{portfolio.buy_threshold}，考虑降低")

        # 检查是否有执行但无交易
        executions_without_trades = 0
        for exe in recent_execs:
            if exe.signal != "HOLD" and exe.status == "completed":
                trade_result = await db.execute(
                    select(Trade).where(Trade.execution_id == str(exe.id))
                )
                if not trade_result.scalars().first():
                    executions_without_trades += 1

        if executions_without_trades > 0:
            issues_found.append(f"{executions_without_trades}条执行记录有信号但无交易")
            suggestions.append("检查交易执行逻辑")
            suggestions.append("检查should_execute判断条件")

        # 检查余额
        if float(portfolio.current_balance) < 100:
            issues_found.append(f"余额较低 (${float(portfolio.current_balance):.2f})")
            suggestions.append("考虑增加余额以支持更多交易")

        if issues_found:
            print("❌ 发现的问题:")
            for i, issue in enumerate(issues_found, 1):
                print(f"  {i}. {issue}")
            print()

            print("💡 建议:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
            print()
        else:
            print("✅ 未发现明显问题")
            print()
            print("可能的原因:")
            print("  • 市场条件不满足交易条件")
            print("  • 阈值配置导致信号都为HOLD")
            print("  • 仓位限制阻止了交易")
            print()

        print("=" * 120)
        print("✅ 诊断完成")
        print("=" * 120)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(diagnose_no_trades())
