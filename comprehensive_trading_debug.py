"""全面Debug自动交易功能"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.portfolio import Portfolio, PortfolioHolding
from app.models.strategy_execution import StrategyExecution
from app.services.decision.signal_generator import signal_generator
from app.services.decision.conviction_calculator import conviction_calculator, ConvictionInput
from app.services.market.real_market_data import real_market_data_service
from datetime import datetime

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

def print_section(title):
    print("\n" + "=" * 120)
    print(f"  {title}")
    print("=" * 120 + "\n")

async def comprehensive_debug():
    """全面Debug"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print_section("🔍 全面Debug：自动交易功能")

    async with AsyncSessionLocal() as db:
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

        # ========================================
        # 1. Portfolio状态检查
        # ========================================
        print_section("1️⃣ Portfolio状态检查")

        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ Portfolio不存在")
            return

        print(f"Portfolio: {portfolio.name}")
        print(f"User ID: {portfolio.user_id}")
        print(f"是否激活: {'✅ 是' if portfolio.is_active else '❌ 否'}")
        print(f"当前余额: ${float(portfolio.current_balance):,.2f}")
        print(f"总价值: ${float(portfolio.total_value):,.2f}")
        print()

        if not portfolio.is_active:
            print("⚠️  警告: Portfolio未激活，策略不会执行交易！")
            print()

        # 持仓检查
        holdings_result = await db.execute(
            select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
        )
        holdings = holdings_result.scalars().all()

        total_value = float(portfolio.total_value)
        if total_value > 0:
            btc_value = sum(float(h.market_value) for h in holdings if h.symbol == "BTC")
            current_position = btc_value / total_value
        else:
            current_position = 0.0

        print(f"BTC持仓比例: {current_position * 100:.2f}%")
        print(f"现金比例: {(1 - current_position) * 100:.2f}%")
        print()

        # ========================================
        # 2. 交易阈值配置检查
        # ========================================
        print_section("2️⃣ 交易阈值配置检查")

        print("Fear & Greed 阈值:")
        print(f"  • 熔断阈值: {portfolio.fg_circuit_breaker_threshold} (F&G < {portfolio.fg_circuit_breaker_threshold} 时停止所有交易)")
        print(f"  • 仓位调整阈值: {portfolio.fg_position_adjust_threshold} (F&G < {portfolio.fg_position_adjust_threshold} 时减少仓位20%)")
        print()

        print("Conviction Score 阈值:")
        print(f"  • 买入阈值: {portfolio.buy_threshold} (>= {portfolio.buy_threshold} 时买入)")
        print(f"  • 部分减仓阈值: {portfolio.partial_sell_threshold} ({portfolio.full_sell_threshold}-{portfolio.partial_sell_threshold} 时部分减仓)")
        print(f"  • 全部清仓阈值: {portfolio.full_sell_threshold} (< {portfolio.full_sell_threshold} 时全部清仓)")
        print()

        # ========================================
        # 3. 获取当前市场数据
        # ========================================
        print_section("3️⃣ 当前市场数据")

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
            fg_classification = fg_data.get("value_classification", "N/A")

            print(f"BTC价格: ${btc_price:,.2f}")
            print(f"24h变化: {price_change:+.2f}%")
            print(f"Fear & Greed: {fg_value} ({fg_classification})")
            print()

            # 检查是否会触发熔断
            if fg_value < portfolio.fg_circuit_breaker_threshold:
                print(f"⚠️  警告: 当前F&G({fg_value}) < 熔断阈值({portfolio.fg_circuit_breaker_threshold})")
                print(f"   → 会触发熔断，停止所有交易！")
                print()
            else:
                print(f"✅ F&G({fg_value}) >= 熔断阈值({portfolio.fg_circuit_breaker_threshold})，不会触发熔断")
                print()

        except Exception as e:
            print(f"❌ 获取市场数据失败: {e}")
            return

        # ========================================
        # 4. 模拟Agent输出 & 计算Conviction Score
        # ========================================
        print_section("4️⃣ 模拟Agent输出 & Conviction Score计算")

        # 使用最近一次执行的agent数据
        latest_exec_result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.user_id == portfolio.user_id)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        latest_exec = latest_exec_result.scalar_one_or_none()

        # 模拟典型的bearish agent输出
        mock_agent_outputs = {
            "macro": {"score": -35.0, "confidence": 0.65, "signal": "BEARISH"},
            "ta": {"score": -38.5, "confidence": 0.72, "signal": "BEARISH"},
            "onchain": {"score": 15.0, "confidence": 0.68, "signal": "NEUTRAL"},
        }

        print("模拟Agent输出:")
        for agent_name, output in mock_agent_outputs.items():
            print(f"  • {agent_name}: signal={output['signal']}, score={output['score']}, confidence={output['confidence']}")
        print()

        # 计算Conviction Score
        conviction_input = ConvictionInput(
            macro_output=mock_agent_outputs["macro"],
            ta_output=mock_agent_outputs["ta"],
            onchain_output=mock_agent_outputs["onchain"],
            market_data=market_data,
        )

        conviction_result = conviction_calculator.calculate(
            conviction_input,
            custom_weights=portfolio.agent_weights
        )

        print(f"Conviction Score计算:")
        print(f"  • 加权分数: {conviction_result.raw_weighted_score:.2f}")
        print(f"  • 风险调整系数: {conviction_result.risk_adjustment:.2f}")
        print(f"  • 最终Conviction Score: {conviction_result.score:.2f}")
        print()

        # ========================================
        # 5. 信号生成测试
        # ========================================
        print_section("5️⃣ 信号生成测试")

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

        signal_result = signal_generator.generate_signal(
            conviction_score=conviction_result.score,
            market_data=market_data,
            current_position=current_position,
            portfolio_state=portfolio_state,
        )

        print(f"生成的交易信号:")
        print(f"  • Signal: {signal_result.signal.value}")
        print(f"  • Signal Strength: {signal_result.signal_strength:.4f}")
        print(f"  • Position Size: {signal_result.position_size:.6f} ({signal_result.position_size * 100:.4f}%)")
        print(f"  • Should Execute: {'✅ 是' if signal_result.should_execute else '❌ 否'}")
        print(f"  • Risk Level: {signal_result.risk_level.value}")
        print()

        print("决策原因:")
        for reason in signal_result.reasons:
            print(f"  • {reason}")
        print()

        if signal_result.warnings:
            print("警告:")
            for warning in signal_result.warnings:
                print(f"  ⚠️  {warning}")
            print()

        # ========================================
        # 6. 执行检查
        # ========================================
        print_section("6️⃣ 交易执行检查")

        if not signal_result.should_execute:
            print("❌ 信号不会被执行")
            print()
            print("可能的原因:")

            if signal_result.signal.value == "HOLD":
                print("  • 信号为HOLD（可能是熔断触发）")
            elif signal_result.signal.value == "BUY":
                if current_position > 0.95:
                    print(f"  • 当前持仓({current_position*100:.2f}%) > 95%，接近满仓")
                if signal_result.position_size < 0.002:
                    print(f"  • 仓位大小({signal_result.position_size:.6f}) < 最小仓位(0.002)")
            elif signal_result.signal.value == "SELL":
                if current_position < 0.01:
                    print(f"  • 当前持仓({current_position*100:.2f}%) < 1%，几乎没有持仓")
        else:
            print("✅ 信号会被执行")
            print()

            if signal_result.signal.value == "BUY":
                # 计算买入金额
                available_cash = float(portfolio.current_balance)
                buy_amount_usd = available_cash * signal_result.position_size
                btc_amount = buy_amount_usd / btc_price if btc_price > 0 else 0

                print(f"预期交易:")
                print(f"  • 类型: 买入BTC")
                print(f"  • 使用资金: ${buy_amount_usd:,.2f} ({signal_result.position_size*100:.4f}% of ${available_cash:,.2f})")
                print(f"  • 买入数量: {btc_amount:.8f} BTC @ ${btc_price:,.2f}")
                print()

            elif signal_result.signal.value == "SELL":
                # 计算卖出金额
                if holdings:
                    btc_holding = next((h for h in holdings if h.symbol == "BTC"), None)
                    if btc_holding:
                        sell_amount = float(btc_holding.amount) * signal_result.position_size
                        sell_value = sell_amount * btc_price

                        print(f"预期交易:")
                        print(f"  • 类型: 卖出BTC")
                        print(f"  • 卖出比例: {signal_result.position_size*100:.2f}%")
                        print(f"  • 卖出数量: {sell_amount:.8f} BTC (持有 {float(btc_holding.amount):.8f})")
                        print(f"  • 卖出价值: ${sell_value:,.2f} @ ${btc_price:,.2f}")
                        print()

        # ========================================
        # 7. 不同场景测试
        # ========================================
        print_section("7️⃣ 不同Conviction Score场景测试")

        test_scores = [35, 40, 45, 50, 55, 60, 65]

        print("测试不同的Conviction Score会产生什么信号:")
        print()
        print(f"{'Score':<8} {'Signal':<6} {'Strength':<10} {'Position':<10} {'Execute':<8} {'Reason'}")
        print("-" * 100)

        for score in test_scores:
            result = signal_generator.generate_signal(
                conviction_score=score,
                market_data=market_data,
                current_position=current_position,
                portfolio_state=portfolio_state,
            )

            emoji = "🟢" if result.signal.value == "BUY" else "🔴" if result.signal.value == "SELL" else "🟡"
            execute_emoji = "✅" if result.should_execute else "❌"

            print(f"{emoji} {score:<5.1f}  {result.signal.value:<6} {result.signal_strength:<10.4f} {result.position_size:<10.6f} {execute_emoji:<8} {result.reasons[0][:60]}")

        print()

        # ========================================
        # 8. 最近执行历史
        # ========================================
        print_section("8️⃣ 最近执行历史")

        recent_execs_result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.user_id == portfolio.user_id)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(5)
        )
        recent_execs = recent_execs_result.scalars().all()

        print(f"最近5次执行:")
        print()

        for i, exe in enumerate(recent_execs, 1):
            market_snapshot = exe.market_snapshot or {}
            fg_data_snapshot = market_snapshot.get("fear_greed", {})
            fg_value_snapshot = fg_data_snapshot.get("value", "N/A") if isinstance(fg_data_snapshot, dict) else "N/A"

            print(f"{i}. {exe.execution_time}")
            conviction_str = f"{exe.conviction_score:.2f}" if exe.conviction_score is not None else "N/A"
            print(f"   Conviction: {conviction_str}, Signal: {exe.signal}, F&G: {fg_value_snapshot}, Status: {exe.status}")
            print()

        # ========================================
        # 9. 总结与建议
        # ========================================
        print_section("9️⃣ 总结与建议")

        issues = []
        recommendations = []

        # 检查Portfolio激活状态
        if not portfolio.is_active:
            issues.append("Portfolio未激活")
            recommendations.append("在Admin Panel中激活Portfolio")

        # 检查余额
        if float(portfolio.current_balance) < 100:
            issues.append(f"余额较低 (${float(portfolio.current_balance):.2f})")
            recommendations.append("考虑增加余额以支持交易")

        # 检查当前信号
        if signal_result.signal.value == "HOLD" and conviction_result.score < portfolio.full_sell_threshold:
            if fg_value < portfolio.fg_circuit_breaker_threshold:
                issues.append(f"熔断触发阻止了交易 (F&G={fg_value} < {portfolio.fg_circuit_breaker_threshold})")
                recommendations.append(f"如果想在当前市场条件下交易，可以降低熔断阈值到{fg_value - 5}以下")
            else:
                issues.append("信号生成异常：Conviction < 全部清仓阈值但信号为HOLD")
                recommendations.append("检查signal_generator逻辑")

        if signal_result.signal.value != "HOLD" and not signal_result.should_execute:
            issues.append(f"有信号({signal_result.signal.value})但不执行")
            if signal_result.signal.value == "BUY" and signal_result.position_size < 0.002:
                recommendations.append("仓位太小，考虑调整仓位计算逻辑")
            elif signal_result.signal.value == "SELL" and current_position < 0.01:
                recommendations.append("持仓太少，无法卖出")

        if issues:
            print("❌ 发现的问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            print()

        if recommendations:
            print("💡 建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
            print()

        if not issues:
            print("✅ 所有检查通过！")
            print()
            print("系统状态:")
            print(f"  • Portfolio激活: ✅")
            print(f"  • 阈值配置: ✅")
            print(f"  • 市场数据: ✅")
            print(f"  • 信号生成: ✅")
            print()

            if signal_result.should_execute:
                print(f"🎯 下次执行时，预期会执行 {signal_result.signal.value} 交易")
            else:
                print(f"🎯 下次执行时，会生成 {signal_result.signal.value} 信号但暂不执行")

        print()
        print("=" * 120)
        print("✅ Debug完成")
        print("=" * 120)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(comprehensive_debug())
