"""测试实际信号生成 - 模拟最近一次执行"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.models.portfolio import Portfolio, PortfolioHolding
from app.models.strategy_execution import StrategyExecution
from app.services.decision.signal_generator import signal_generator
from datetime import datetime

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def test_live_signal():
    """测试实际信号生成"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🧪 测试实际信号生成 - 模拟最近一次执行")
    print("=" * 100)
    print()

    async with AsyncSessionLocal() as db:
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

        # 获取Portfolio
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ Portfolio不存在")
            return

        # 获取最近一次执行
        exec_result = await db.execute(
            select(StrategyExecution)
            .where(StrategyExecution.user_id == portfolio.user_id)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        latest_exec = exec_result.scalar_one_or_none()

        if not latest_exec:
            print("❌ 没有执行记录")
            return

        print("📊 最近一次执行记录:")
        print(f"   时间: {latest_exec.execution_time}")
        print(f"   Conviction Score: {latest_exec.conviction_score:.2f}")
        print(f"   数据库中的信号: {latest_exec.signal}")
        print(f"   信号强度: {latest_exec.signal_strength:.4f}")
        print()

        # 获取当前持仓比例
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

        print(f"📈 当前持仓状态:")
        print(f"   BTC持仓比例: {current_position * 100:.2f}%")
        print(f"   总价值: ${total_value:,.2f}")
        print()

        # 构造portfolio_state（使用当前阈值）
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

        print(f"⚙️  当前阈值配置:")
        print(f"   FG熔断阈值: {portfolio.fg_circuit_breaker_threshold}")
        print(f"   FG仓位调整阈值: {portfolio.fg_position_adjust_threshold}")
        print(f"   买入阈值: {portfolio.buy_threshold}")
        print(f"   部分减仓阈值: {portfolio.partial_sell_threshold}")
        print(f"   全部清仓阈值: {portfolio.full_sell_threshold}")
        print()

        # 模拟市场数据（使用合理的默认值）
        # 注意：真实执行时的F&G值我们不知道，使用一个中性值
        market_data = {
            "btc_price_change_24h": 0.0,
            "fear_greed": {"value": 50},  # 假设中性值
            "macro": {"dxy_index": 100},
        }

        print(f"📡 模拟市场数据 (使用中性值):")
        print(f"   BTC 24h变化: 0.0%")
        print(f"   Fear & Greed: 50")
        print()

        # 重新生成信号
        print("🔄 重新生成信号...")
        print()

        signal_result = signal_generator.generate_signal(
            conviction_score=latest_exec.conviction_score,
            market_data=market_data,
            current_position=current_position,
            portfolio_state=portfolio_state,
        )

        print(f"✅ 信号生成结果:")
        print(f"   信号: {signal_result.signal.value}")
        print(f"   信号强度: {signal_result.signal_strength:.4f}")
        print(f"   仓位大小: {signal_result.position_size:.6f}")
        print(f"   应该执行: {signal_result.should_execute}")
        print(f"   风险等级: {signal_result.risk_level.value}")
        print()

        print(f"📝 决策原因:")
        for reason in signal_result.reasons:
            print(f"   • {reason}")
        print()

        if signal_result.warnings:
            print(f"⚠️  警告:")
            for warning in signal_result.warnings:
                print(f"   • {warning}")
            print()

        # 对比
        print("=" * 100)
        print("🔍 对比分析:")
        print("=" * 100)
        print()

        print(f"数据库中的信号: {latest_exec.signal}")
        print(f"重新生成的信号: {signal_result.signal.value}")
        print()

        if latest_exec.signal == signal_result.signal.value:
            print("✅ 信号一致！")
        else:
            print("❌ 信号不一致！")
            print()
            print("可能的原因:")
            print("1. 真实执行时的Fear & Greed值可能触发了熔断")
            print("2. 真实执行时的市场数据不同")
            print("3. 执行时使用的阈值配置不同")
            print()

            # 测试不同的F&G值
            print("🧪 测试不同的Fear & Greed值:")
            print()

            for fg_value in [5, 10, 15, 20, 25, 30, 50]:
                test_market_data = {
                    "btc_price_change_24h": 0.0,
                    "fear_greed": {"value": fg_value},
                    "macro": {"dxy_index": 100},
                }

                test_result = signal_generator.generate_signal(
                    conviction_score=latest_exec.conviction_score,
                    market_data=test_market_data,
                    current_position=current_position,
                    portfolio_state=portfolio_state,
                )

                match_indicator = "✅" if test_result.signal.value == latest_exec.signal else "  "
                print(f"{match_indicator} FG={fg_value:2d}: {test_result.signal.value:4s} - {test_result.reasons[0][:80]}")

            print()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_live_signal())
