"""深入诊断最新的HOLD信号"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text
from app.models.strategy_execution import StrategyExecution
from app.models.agent_execution import AgentExecution
from app.models.portfolio import Portfolio
from app.services.decision.signal_generator import signal_generator
from app.services.decision.conviction_calculator import conviction_calculator, ConvictionInput

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def diagnose():
    """诊断最新的HOLD信号"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 120)
    print("🔬 深入诊断：为什么最新执行产生HOLD信号")
    print("=" * 120)
    print()

    async with AsyncSessionLocal() as db:
        # 获取最新的completed执行且signal=HOLD
        result = await db.execute(
            select(StrategyExecution)
            .where(
                StrategyExecution.status == "completed",
                StrategyExecution.signal == "HOLD"
            )
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()

        if not latest:
            print("未找到HOLD信号的执行")
            return

        print(f"📊 执行详情:")
        print(f"   ID: {latest.id}")
        print(f"   时间: {latest.execution_time}")
        print(f"   Conviction Score: {latest.conviction_score}")
        print(f"   Signal: {latest.signal}")
        print(f"   Signal Strength: {latest.signal_strength}")
        print(f"   Status: {latest.status}")
        print()

        # 获取该执行使用的Portfolio配置 (使用具体的portfolio_id)
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"
        portfolio_result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = portfolio_result.scalar_one_or_none()

        if portfolio:
            print(f"📋 执行时的Portfolio阈值配置:")
            print(f"   FG熔断阈值: {portfolio.fg_circuit_breaker_threshold}")
            print(f"   FG仓位调整阈值: {portfolio.fg_position_adjust_threshold}")
            print(f"   买入阈值: {portfolio.buy_threshold}")
            print(f"   部分减仓阈值: {portfolio.partial_sell_threshold}")
            print(f"   全部清仓阈值: {portfolio.full_sell_threshold}")
            print()

        # 获取market snapshot
        market_snapshot = latest.market_snapshot or {}
        fg_data = market_snapshot.get("fear_greed", {})
        fg_value = fg_data.get("value", "N/A")

        print(f"🌍 市场快照:")
        print(f"   Fear & Greed: {fg_value}")

        btc_price_obj = market_snapshot.get("btc_price", {})
        if isinstance(btc_price_obj, dict):
            btc_price = btc_price_obj.get("price", 0)
            price_change = btc_price_obj.get("price_change_24h", 0)
        else:
            btc_price = btc_price_obj
            price_change = 0

        print(f"   BTC价格: ${btc_price:,.2f}")
        print(f"   24h变化: {price_change:.2f}%")
        print()

        # 获取Agent执行记录
        agent_result = await db.execute(
            select(AgentExecution)
            .where(AgentExecution.strategy_execution_id == str(latest.id))
            .order_by(AgentExecution.agent_name)
        )
        agents = agent_result.scalars().all()

        if agents:
            print(f"🤖 Agent执行记录 ({len(agents)}个):")
            agent_outputs = {}
            for agent in agents:
                agent_key = agent.agent_name.replace("_agent", "")
                agent_outputs[agent_key] = {
                    "score": agent.score,
                    "confidence": agent.confidence,
                    "signal": agent.signal,
                }
                print(f"   • {agent.agent_name}: signal={agent.signal}, score={agent.score}, confidence={agent.confidence}")
            print()

            # 重新计算Conviction Score
            print("🧮 重新计算Conviction Score:")
            conviction_input = ConvictionInput(
                macro_output=agent_outputs.get("macro", {}),
                ta_output=agent_outputs.get("ta", {}),
                onchain_output=agent_outputs.get("onchain", {}),
                market_data=market_snapshot,
            )

            conviction_result = conviction_calculator.calculate(
                conviction_input,
                custom_weights=portfolio.agent_weights if portfolio else None
            )

            print(f"   计算得到: {conviction_result.score:.2f}")
            print(f"   数据库中: {latest.conviction_score:.2f}")

            if abs(conviction_result.score - latest.conviction_score) > 0.5:
                print(f"   ⚠️  不匹配！差异: {abs(conviction_result.score - latest.conviction_score):.2f}")
            else:
                print(f"   ✅ 匹配")
            print()

            # 重新生成Signal
            print("🔄 重新生成Signal (使用当前Portfolio配置):")

            portfolio_state = {
                "consecutive_bullish_count": 0,
                "last_conviction_score": 50,
                "consecutive_signal_threshold": 30,
                "acceleration_multiplier_min": 1.1,
                "acceleration_multiplier_max": 2.0,
                "fg_circuit_breaker_threshold": portfolio.fg_circuit_breaker_threshold,
                "fg_position_adjust_threshold": portfolio.fg_position_adjust_threshold,
                "buy_threshold": portfolio.buy_threshold,
                "partial_sell_threshold": portfolio.partial_sell_threshold,
                "full_sell_threshold": portfolio.full_sell_threshold,
            }

            signal_result = signal_generator.generate_signal(
                conviction_score=latest.conviction_score,
                market_data=market_snapshot,
                current_position=0.05,  # 假设5%持仓
                portfolio_state=portfolio_state,
            )

            print(f"   使用当前阈值生成: {signal_result.signal.value}")
            print(f"   数据库中: {latest.signal}")
            print()

            if signal_result.signal.value != latest.signal:
                print("   ❌ 信号不一致！")
                print()
                print("   可能的原因:")
                print("   1. 执行时使用的阈值配置与当前不同")
                print("   2. 执行时的F&G值触发了熔断")
                print("   3. signal_generator的逻辑在执行后被修改")
                print()

                # 检查是否是熔断
                if fg_value < portfolio.fg_circuit_breaker_threshold:
                    print(f"   ✅ 确认: F&G({fg_value}) < 熔断阈值({portfolio.fg_circuit_breaker_threshold}) → 熔断触发")
                else:
                    print(f"   ⚠️  F&G({fg_value}) >= 熔断阈值({portfolio.fg_circuit_breaker_threshold})，不应触发熔断")
                    print()

                    # 尝试使用旧的默认阈值
                    print("   🔍 尝试使用旧的硬编码阈值 (熔断=20):")
                    old_portfolio_state = portfolio_state.copy()
                    old_portfolio_state["fg_circuit_breaker_threshold"] = 20

                    old_signal_result = signal_generator.generate_signal(
                        conviction_score=latest.conviction_score,
                        market_data=market_snapshot,
                        current_position=0.05,
                        portfolio_state=old_portfolio_state,
                    )

                    print(f"   使用旧阈值(熔断=20)生成: {old_signal_result.signal.value}")

                    if old_signal_result.signal.value == latest.signal:
                        print(f"   ✅ 匹配！这证明执行时使用的是旧的硬编码阈值(20)")
                        print(f"   F&G({fg_value}) 不小于20，但可能在判断时有浮点精度问题")
                        print()
                        print("   🔍 检查原始F&G数据:")
                        print(f"   {fg_data}")

        else:
            print("❌ 该执行没有Agent记录")
            print("   这可能意味着agent执行失败，但策略仍然completed（不应该发生）")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(diagnose())
