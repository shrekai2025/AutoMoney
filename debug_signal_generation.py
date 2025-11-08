"""Debug信号生成逻辑"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.portfolio import Portfolio, PortfolioHolding
from app.services.decision.signal_generator import signal_generator
from app.services.market.real_market_data import real_market_data_service
from decimal import Decimal

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def debug_signal_generation():
    """Debug信号生成"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🔍 Debug信号生成逻辑")
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

        # 获取当前持仓
        holdings_result = await db.execute(
            select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
        )
        holdings = holdings_result.scalars().all()

        # 计算当前持仓比例
        total_value = float(portfolio.total_value)
        if total_value > 0:
            btc_value = sum(float(h.market_value) for h in holdings if h.symbol == "BTC")
            current_position = btc_value / total_value
        else:
            current_position = 0.0

        print(f"📊 Portfolio状态:")
        print(f"   总价值: ${total_value:.2f}")
        print(f"   当前余额: ${float(portfolio.current_balance):.2f}")
        print(f"   BTC持仓比例: {current_position * 100:.2f}%")
        print()

        # 获取市场数据
        print("📡 获取市场数据...")
        market_data = await real_market_data_service.get_complete_market_snapshot()
        btc_price_obj = market_data.get("btc_price", {})
        if isinstance(btc_price_obj, dict):
            btc_price = btc_price_obj.get("price", 0)
            price_change = btc_price_obj.get("price_change_24h", 0)
        else:
            btc_price = btc_price_obj
            price_change = 0

        print(f"   BTC价格: ${btc_price:,.2f}")
        print(f"   24h变化: {price_change:.2f}%")
        print()

        # 测试不同的conviction_score
        test_scores = [45, 50, 51.3, 55, 60, 70]

        print("=" * 100)
        print("🧪 测试不同Conviction Score的信号生成")
        print("=" * 100)
        print()

        for score in test_scores:
            print(f"📊 Conviction Score: {score:.1f}")
            print("-" * 80)

            # 准备market_data
            market_data_input = {
                "btc_price_change_24h": price_change,
                "fear_greed": market_data.get("fear_greed", {}),
                "macro": market_data.get("macro", {}),
            }

            # 准备portfolio_state
            portfolio_state = {
                "consecutive_bullish_count": portfolio.consecutive_bullish_count or 0,
                "last_conviction_score": 50.0,
                "consecutive_signal_threshold": portfolio.consecutive_signal_threshold or 30,
                "acceleration_multiplier_min": portfolio.acceleration_multiplier_min or 1.1,
                "acceleration_multiplier_max": portfolio.acceleration_multiplier_max or 2.0,
            }

            # 生成信号
            signal_result = signal_generator.generate_signal(
                conviction_score=score,
                market_data=market_data_input,
                current_position=current_position,
                portfolio_state=portfolio_state,
            )

            # 打印结果
            signal_icon = {
                "BUY": "🟢",
                "SELL": "🔴",
                "HOLD": "🟡"
            }.get(signal_result.signal.value, "⚪")

            print(f"   {signal_icon} 信号: {signal_result.signal.value}")
            print(f"   信号强度: {signal_result.signal_strength:.4f}")
            print(f"   仓位大小: {signal_result.position_size:.4f} ({signal_result.position_size * 100:.2f}%)")
            print(f"   风险等级: {signal_result.risk_level.value}")
            print(f"   应该执行: {'✅ YES' if signal_result.should_execute else '❌ NO'}")

            if not signal_result.should_execute and signal_result.signal.value != "HOLD":
                print(f"   ⚠️  为什么不执行?")
                if signal_result.signal.value == "BUY":
                    if current_position > 0.95:
                        print(f"      - 当前持仓 ({current_position*100:.2f}%) > 95%，接近满仓")
                    if signal_result.position_size < 0.002:
                        print(f"      - 仓位大小 ({signal_result.position_size:.4f}) < 0.002，仓位太小")
                elif signal_result.signal.value == "SELL":
                    if current_position < 0.01:
                        print(f"      - 当前持仓 ({current_position*100:.2f}%) < 1%，几乎没有持仓")

            print(f"   决策原因:")
            for reason in signal_result.reasons:
                print(f"      - {reason}")

            if signal_result.warnings:
                print(f"   警告:")
                for warning in signal_result.warnings:
                    print(f"      - {warning}")

            print()

        print("=" * 100)
        print("🎯 关键问题分析")
        print("=" * 100)
        print()

        # 重点分析51.3的情况（这是实际发生的情况）
        score = 51.3
        market_data_input = {
            "btc_price_change_24h": price_change,
            "fear_greed": market_data.get("fear_greed", {}),
            "macro": market_data.get("macro", {}),
        }

        portfolio_state = {
            "consecutive_bullish_count": portfolio.consecutive_bullish_count or 0,
            "last_conviction_score": 50.0,
            "consecutive_signal_threshold": portfolio.consecutive_signal_threshold or 30,
            "acceleration_multiplier_min": portfolio.acceleration_multiplier_min or 1.1,
            "acceleration_multiplier_max": portfolio.acceleration_multiplier_max or 2.0,
        }

        signal_result = signal_generator.generate_signal(
            conviction_score=score,
            market_data=market_data_input,
            current_position=current_position,
            portfolio_state=portfolio_state,
        )

        print(f"📋 详细分析 Conviction Score = {score}:")
        print()
        print(f"输入参数:")
        print(f"   - conviction_score: {score}")
        print(f"   - current_position: {current_position:.4f} ({current_position*100:.2f}%)")
        print(f"   - btc_price_change_24h: {price_change:.2f}%")
        print(f"   - fear_greed: {market_data.get('fear_greed', {}).get('value', 'N/A')}")
        print()

        print(f"信号生成结果:")
        print(f"   - signal: {signal_result.signal.value}")
        print(f"   - signal_strength: {signal_result.signal_strength:.4f}")
        print(f"   - position_size: {signal_result.position_size:.6f} ({signal_result.position_size * 100:.4f}%)")
        print(f"   - should_execute: {signal_result.should_execute}")
        print()

        # 分析为什么should_execute是False
        if not signal_result.should_execute:
            print(f"⚠️  should_execute = False 的原因:")
            print()

            if signal_result.signal.value == "HOLD":
                print(f"   ✓ 信号是HOLD，不执行交易")
            elif signal_result.signal.value == "BUY":
                print(f"   检查BUY信号的执行条件:")
                print(f"   1. 是否接近满仓? current_position ({current_position:.4f}) > 0.95?")
                if current_position > 0.95:
                    print(f"      ❌ YES - 已经接近满仓，不买入")
                else:
                    print(f"      ✅ NO - 还有空间买入")

                print(f"   2. 仓位是否太小? position_size ({signal_result.position_size:.6f}) < 0.002?")
                if signal_result.position_size < 0.002:
                    print(f"      ❌ YES - 仓位太小，不值得买入")
                    print(f"      📊 分析position_size计算:")
                    print(f"         - BUY_THRESHOLD = 50")
                    print(f"         - signal_strength = (conviction_score - 50) / 50 = ({score} - 50) / 50 = {signal_result.signal_strength:.4f}")
                    print(f"         - MIN_POSITION_SIZE = 0.002")
                    print(f"         - MAX_POSITION_SIZE = 0.005")
                    print(f"         - base_position = 0.002 + {signal_result.signal_strength:.4f} * (0.005 - 0.002) = {0.002 + signal_result.signal_strength * 0.003:.6f}")

                    # 检查波动率调整
                    if abs(price_change) > 10:
                        print(f"         - 波动率调整: * 0.5 (24h变化 > 10%)")
                    elif abs(price_change) > 5:
                        print(f"         - 波动率调整: * 0.75 (24h变化 > 5%)")

                    # 检查恐惧指数调整
                    fg_value = market_data.get("fear_greed", {}).get("value", 50)
                    if fg_value < 30:
                        print(f"         - 恐惧指数调整: * 0.8 (FG < 30)")

                    print(f"         - 最终position_size = {signal_result.position_size:.6f}")
                else:
                    print(f"      ✅ NO - 仓位大小合适")

            elif signal_result.signal.value == "SELL":
                print(f"   检查SELL信号的执行条件:")
                print(f"   1. 是否有持仓? current_position ({current_position:.4f}) < 0.01?")
                if current_position < 0.01:
                    print(f"      ❌ YES - 几乎没有持仓，无需卖出")
                else:
                    print(f"      ✅ NO - 有持仓可以卖出")

        print()
        print("=" * 100)
        print("✅ Debug完成")
        print("=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_signal_generation())
