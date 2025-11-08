"""手动触发一次策略执行并详细记录"""

import asyncio
import sys
import logging
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.services.strategy.strategy_orchestrator import strategy_orchestrator
from app.services.market.real_market_data import real_market_data_service

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def trigger_execution():
    """手动触发一次策略执行"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🚀 手动触发策略执行")
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

        print(f"📊 Portfolio: {portfolio.name}")
        print(f"   User ID: {portfolio.user_id}")
        print()

        print(f"⚙️  当前阈值配置:")
        print(f"   FG熔断阈值: {portfolio.fg_circuit_breaker_threshold}")
        print(f"   FG仓位调整阈值: {portfolio.fg_position_adjust_threshold}")
        print(f"   买入阈值: {portfolio.buy_threshold}")
        print(f"   部分减仓阈值: {portfolio.partial_sell_threshold}")
        print(f"   全部清仓阈值: {portfolio.full_sell_threshold}")
        print()

        # 获取市场数据
        print("📡 获取市场数据...")
        market_data = await real_market_data_service.get_complete_market_snapshot()

        btc_price_obj = market_data.get("btc_price", {})
        if isinstance(btc_price_obj, dict):
            btc_price = btc_price_obj.get("price", 0)
        else:
            btc_price = btc_price_obj

        fg_data = market_data.get("fear_greed", {})
        fg_value = fg_data.get("value", "N/A")

        print(f"   BTC价格: ${btc_price:,.2f}")
        print(f"   Fear & Greed: {fg_value}")
        print()

        # 准备模拟的agent输出（因为OpenRouter未配置）
        from app.schemas.agents import AgentOutput, SignalType, ConfidenceLevel
        from datetime import datetime

        mock_agent_outputs = {
            "macro_agent": AgentOutput(
                agent_name="macro_agent",
                signal=SignalType.BEARISH,
                score=-35.0,
                confidence=0.65,
                confidence_level=ConfidenceLevel.MEDIUM,
                reasoning="Market showing bearish sentiment",
                timestamp=datetime.utcnow(),
            ),
            "ta_agent": AgentOutput(
                agent_name="ta_agent",
                signal=SignalType.BEARISH,
                score=-38.5,
                confidence=0.72,
                confidence_level=ConfidenceLevel.HIGH,
                reasoning="Technical indicators bearish",
                timestamp=datetime.utcnow(),
            ),
            "onchain_agent": AgentOutput(
                agent_name="onchain_agent",
                signal=SignalType.NEUTRAL,
                score=15.0,
                confidence=0.68,
                confidence_level=ConfidenceLevel.HIGH,
                reasoning="Onchain metrics neutral",
                timestamp=datetime.utcnow(),
            ),
        }

        # 执行策略
        print("🔄 执行策略（使用模拟agent输出）...")
        print("=" * 100)
        print()

        try:
            result = await strategy_orchestrator.execute_strategy(
                db=db,
                user_id=portfolio.user_id,
                portfolio_id=portfolio_id,
                market_data=market_data,
                agent_outputs=mock_agent_outputs,  # 使用模拟agent输出
            )

            print()
            print("=" * 100)
            print("✅ 策略执行完成")
            print("=" * 100)
            print()

            print(f"📊 执行结果:")
            print(f"   ID: {result.id}")
            print(f"   Conviction Score: {result.conviction_score:.2f}")
            print(f"   Signal: {result.signal}")
            print(f"   Signal Strength: {result.signal_strength:.4f}")
            print(f"   Position Size: {result.position_size:.6f if result.position_size else 'N/A'}")
            print(f"   Risk Level: {result.risk_level}")
            print(f"   Status: {result.status}")
            print()

            # 分析结果
            print("🔍 结果分析:")
            print()

            if result.signal == "HOLD":
                print("⚠️  信号为HOLD")
                if fg_value < portfolio.fg_circuit_breaker_threshold:
                    print(f"   ✅ 原因: F&G({fg_value}) < 熔断阈值({portfolio.fg_circuit_breaker_threshold})")
                else:
                    print(f"   ❌ 疑问: F&G({fg_value}) >= 熔断阈值({portfolio.fg_circuit_breaker_threshold})，不应触发熔断")
                    print(f"   Conviction({result.conviction_score:.2f}) vs 买入阈值({portfolio.buy_threshold})")
                    print(f"   Conviction({result.conviction_score:.2f}) vs 全部清仓阈值({portfolio.full_sell_threshold})")

            elif result.signal == "SELL":
                if result.conviction_score < portfolio.full_sell_threshold:
                    print(f"   ✅ 正确: Conviction({result.conviction_score:.2f}) < 全部清仓阈值({portfolio.full_sell_threshold})")
                else:
                    print(f"   ✅ 正确: 部分减仓 (Conviction在{portfolio.full_sell_threshold}-{portfolio.partial_sell_threshold}之间)")

            elif result.signal == "BUY":
                if result.conviction_score >= portfolio.buy_threshold:
                    print(f"   ✅ 正确: Conviction({result.conviction_score:.2f}) >= 买入阈值({portfolio.buy_threshold})")
                else:
                    print(f"   ❌ 疑问: Conviction({result.conviction_score:.2f}) < 买入阈值({portfolio.buy_threshold})")

        except Exception as e:
            print()
            print(f"❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(trigger_execution())
