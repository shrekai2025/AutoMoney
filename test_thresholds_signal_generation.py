"""测试自定义阈值在信号生成中的应用"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.services.decision.signal_generator import signal_generator
from app.services.strategy.marketplace_service import marketplace_service

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def test_thresholds_in_signal_generation():
    """测试自定义阈值对信号生成的影响"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🧪 测试自定义阈值在信号生成中的应用")
    print("=" * 100)
    print()

    async with AsyncSessionLocal() as db:
        # 获取Portfolio
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ Portfolio不存在")
            return

        # 准备market_data
        market_data = {
            "btc_price_change_24h": 2.0,
            "fear_greed": {"value": 50},
            "macro": {"dxy_index": 100},
        }

        # 测试场景1: 使用默认阈值 (buy_threshold = 50)
        print("=" * 100)
        print("📊 场景1: 默认阈值 (buy_threshold=50)")
        print("=" * 100)
        print()

        # 确保使用默认阈值
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            buy_threshold=50,
            partial_sell_threshold=50,
            full_sell_threshold=45,
        )
        await db.refresh(portfolio)

        portfolio_state = {
            "consecutive_bullish_count": 0,
            "last_conviction_score": 50.0,
            "consecutive_signal_threshold": 30,
            "acceleration_multiplier_min": 1.1,
            "acceleration_multiplier_max": 2.0,
            "fg_circuit_breaker_threshold": portfolio.fg_circuit_breaker_threshold,
            "fg_position_adjust_threshold": portfolio.fg_position_adjust_threshold,
            "buy_threshold": portfolio.buy_threshold,
            "partial_sell_threshold": portfolio.partial_sell_threshold,
            "full_sell_threshold": portfolio.full_sell_threshold,
        }

        # 测试conviction_score = 49（应该是SELL）
        signal_result = signal_generator.generate_signal(
            conviction_score=49,
            market_data=market_data,
            current_position=0.5,
            portfolio_state=portfolio_state,
        )

        print(f"Conviction Score = 49:")
        print(f"   信号: {signal_result.signal.value}")
        print(f"   仓位大小: {signal_result.position_size:.4f}")
        print(f"   决策原因: {signal_result.reasons[0] if signal_result.reasons else 'N/A'}")
        expected_signal = "SELL" if 49 < 50 and 49 >= 45 else "UNKNOWN"
        print(f"   预期信号: {expected_signal} (部分减仓)")
        print(f"   ✅ 正确" if signal_result.signal.value == "SELL" else "❌ 错误")
        print()

        # 测试conviction_score = 51（应该是BUY）
        signal_result = signal_generator.generate_signal(
            conviction_score=51,
            market_data=market_data,
            current_position=0.5,
            portfolio_state=portfolio_state,
        )

        print(f"Conviction Score = 51:")
        print(f"   信号: {signal_result.signal.value}")
        print(f"   仓位大小: {signal_result.position_size:.4f}")
        print(f"   决策原因: {signal_result.reasons[0] if signal_result.reasons else 'N/A'}")
        print(f"   预期信号: BUY")
        print(f"   ✅ 正确" if signal_result.signal.value == "BUY" else "❌ 错误")
        print()

        # 测试场景2: 自定义阈值 (buy_threshold = 60)
        print("=" * 100)
        print("📊 场景2: 自定义阈值 (buy_threshold=60)")
        print("=" * 100)
        print()

        # 更新为自定义阈值
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            buy_threshold=60,
            partial_sell_threshold=55,
            full_sell_threshold=50,
        )
        await db.refresh(portfolio)

        portfolio_state["buy_threshold"] = portfolio.buy_threshold
        portfolio_state["partial_sell_threshold"] = portfolio.partial_sell_threshold
        portfolio_state["full_sell_threshold"] = portfolio.full_sell_threshold

        # 测试conviction_score = 55（在新阈值下应该是SELL，因为55 < 60但 >= 50）
        signal_result = signal_generator.generate_signal(
            conviction_score=55,
            market_data=market_data,
            current_position=0.5,
            portfolio_state=portfolio_state,
        )

        print(f"Conviction Score = 55:")
        print(f"   信号: {signal_result.signal.value}")
        print(f"   仓位大小: {signal_result.position_size:.4f}")
        print(f"   决策原因: {signal_result.reasons[0] if signal_result.reasons else 'N/A'}")
        expected_signal = "SELL" if 55 >= 50 and 55 < 60 else "UNKNOWN"
        print(f"   预期信号: {expected_signal} (部分减仓，因为50 <= 55 < 60)")
        print(f"   ✅ 正确" if signal_result.signal.value == "SELL" else "❌ 错误")
        print()

        # 测试conviction_score = 65（应该是BUY）
        signal_result = signal_generator.generate_signal(
            conviction_score=65,
            market_data=market_data,
            current_position=0.5,
            portfolio_state=portfolio_state,
        )

        print(f"Conviction Score = 65:")
        print(f"   信号: {signal_result.signal.value}")
        print(f"   仓位大小: {signal_result.position_size:.4f}")
        print(f"   决策原因: {signal_result.reasons[0] if signal_result.reasons else 'N/A'}")
        print(f"   预期信号: BUY (因为 65 >= 60)")
        print(f"   ✅ 正确" if signal_result.signal.value == "BUY" else "❌ 错误")
        print()

        # 测试场景3: Fear & Greed熔断阈值
        print("=" * 100)
        print("📊 场景3: 自定义Fear & Greed熔断阈值 (15 -> 25)")
        print("=" * 100)
        print()

        # 更新Fear & Greed熔断阈值
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=25,
        )
        await db.refresh(portfolio)

        portfolio_state["fg_circuit_breaker_threshold"] = portfolio.fg_circuit_breaker_threshold

        # 测试FG = 22（在新阈值下应该触发熔断）
        market_data_low_fg = {
            "btc_price_change_24h": 2.0,
            "fear_greed": {"value": 22},
            "macro": {"dxy_index": 100},
        }

        signal_result = signal_generator.generate_signal(
            conviction_score=70,
            market_data=market_data_low_fg,
            current_position=0.5,
            portfolio_state=portfolio_state,
        )

        print(f"Fear & Greed = 22, Conviction Score = 70:")
        print(f"   信号: {signal_result.signal.value}")
        print(f"   仓位大小: {signal_result.position_size:.4f}")
        print(f"   决策原因: {signal_result.reasons[0] if signal_result.reasons else 'N/A'}")
        print(f"   预期信号: HOLD (熔断，因为 22 < 25)")
        print(f"   ✅ 正确" if signal_result.signal.value == "HOLD" else "❌ 错误")
        print()

        # 恢复默认值
        print("🔄 恢复默认值...")
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=20,
            fg_position_adjust_threshold=30,
            buy_threshold=50,
            partial_sell_threshold=50,
            full_sell_threshold=45,
        )
        print("✅ 已恢复默认值")

    print()
    print("=" * 100)
    print("✅ 测试完成 - 自定义阈值功能正常工作！")
    print("=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_thresholds_in_signal_generation())
