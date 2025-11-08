"""交易阈值功能演示"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.services.decision.signal_generator import signal_generator
from app.services.strategy.marketplace_service import marketplace_service

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100 + "\n")

async def demo_trading_thresholds():
    """演示交易阈值功能"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print_header("🎬 交易阈值功能演示")

    async with AsyncSessionLocal() as db:
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ Portfolio不存在")
            return

        print(f"Portfolio: {portfolio.name}")
        print(f"User ID: {portfolio.user_id}")
        print()

        # ========================================
        # 场景1: 默认阈值 - 保守策略
        # ========================================
        print_header("📊 场景1: 默认阈值 - 保守策略")

        print("配置默认阈值（保守策略）:")
        print("  - 买入阈值: 50 (信念分数达到50才买入)")
        print("  - 部分减仓阈值: 50")
        print("  - 全部清仓阈值: 45")
        print("  - Fear & Greed熔断: 20 (极度恐惧时停止交易)")
        print("  - Fear & Greed仓位调整: 30 (恐惧时减少仓位)")
        print()

        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            buy_threshold=50,
            partial_sell_threshold=50,
            full_sell_threshold=45,
            fg_circuit_breaker_threshold=20,
            fg_position_adjust_threshold=30,
        )
        await db.refresh(portfolio)

        market_data = {
            "btc_price_change_24h": 2.0,
            "fear_greed": {"value": 50},
            "macro": {"dxy_index": 100},
        }

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

        test_scores = [44, 47, 51, 55]
        print("测试不同的Conviction Score:")
        for score in test_scores:
            result = signal_generator.generate_signal(
                conviction_score=score,
                market_data=market_data,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )
            emoji = "🟢" if result.signal.value == "BUY" else "🔴" if result.signal.value == "SELL" else "🟡"
            print(f"  {emoji} Score={score}: {result.signal.value:4s} - {result.reasons[0]}")

        # ========================================
        # 场景2: 激进策略 - 降低买入门槛
        # ========================================
        print_header("🚀 场景2: 激进策略 - 降低买入门槛")

        print("调整为激进策略:")
        print("  - 买入阈值: 45 (降低门槛，更容易买入)")
        print("  - 部分减仓阈值: 48")
        print("  - 全部清仓阈值: 40")
        print()

        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            buy_threshold=45,
            partial_sell_threshold=48,
            full_sell_threshold=40,
        )
        await db.refresh(portfolio)

        portfolio_state["buy_threshold"] = 45
        portfolio_state["partial_sell_threshold"] = 48
        portfolio_state["full_sell_threshold"] = 40

        print("同样的Conviction Score，不同的交易决策:")
        for score in test_scores:
            result = signal_generator.generate_signal(
                conviction_score=score,
                market_data=market_data,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )
            emoji = "🟢" if result.signal.value == "BUY" else "🔴" if result.signal.value == "SELL" else "🟡"
            print(f"  {emoji} Score={score}: {result.signal.value:4s} - {result.reasons[0]}")

        print("\n💡 对比:")
        print("  - Score=47: 保守策略→SELL, 激进策略→BUY (差异明显)")
        print("  - Score=44: 两种策略都是SELL (低于买入阈值)")

        # ========================================
        # 场景3: 谨慎策略 - 提高买入门槛
        # ========================================
        print_header("🛡️  场景3: 谨慎策略 - 提高买入门槛")

        print("调整为谨慎策略:")
        print("  - 买入阈值: 60 (只在高信念时买入)")
        print("  - 部分减仓阈值: 55")
        print("  - 全部清仓阈值: 50")
        print()

        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            buy_threshold=60,
            partial_sell_threshold=55,
            full_sell_threshold=50,
        )
        await db.refresh(portfolio)

        portfolio_state["buy_threshold"] = 60
        portfolio_state["partial_sell_threshold"] = 55
        portfolio_state["full_sell_threshold"] = 50

        print("同样的Conviction Score，谨慎策略的决策:")
        for score in test_scores:
            result = signal_generator.generate_signal(
                conviction_score=score,
                market_data=market_data,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )
            emoji = "🟢" if result.signal.value == "BUY" else "🔴" if result.signal.value == "SELL" else "🟡"
            print(f"  {emoji} Score={score}: {result.signal.value:4s} - {result.reasons[0]}")

        print("\n💡 对比:")
        print("  - Score=55: 保守/激进策略→BUY, 谨慎策略→SELL")
        print("  - 谨慎策略需要Score≥60才会买入")

        # ========================================
        # 场景4: 熔断机制演示
        # ========================================
        print_header("⚠️  场景4: 熔断机制演示")

        print("市场恐慌时的保护机制:")
        print("  - Fear & Greed = 18 (极度恐惧)")
        print("  - 熔断阈值 = 20")
        print("  - 即使Conviction Score很高，也会停止交易")
        print()

        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=20,
            buy_threshold=50,
        )
        await db.refresh(portfolio)

        portfolio_state["fg_circuit_breaker_threshold"] = 20
        portfolio_state["buy_threshold"] = 50

        market_data_panic = {
            "btc_price_change_24h": 2.0,
            "fear_greed": {"value": 18},
            "macro": {"dxy_index": 100},
        }

        for score in [70, 80, 90]:
            result = signal_generator.generate_signal(
                conviction_score=score,
                market_data=market_data_panic,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )
            emoji = "⏸️"
            print(f"  {emoji} Score={score}: {result.signal.value:4s} - {result.reasons[0]}")

        print("\n💡 保护机制:")
        print("  ✅ 在市场极度恐慌时(FG<20)，自动停止所有交易")
        print("  ✅ 避免在恐慌抛售中盲目买入")

        # ========================================
        # 场景5: 灵活调整熔断阈值
        # ========================================
        print_header("🔧 场景5: 灵活调整熔断阈值")

        print("根据市场环境调整熔断阈值:")
        print("  - 牛市: 可以降低熔断阈值到15 (容忍更低的FG)")
        print("  - 熊市: 可以提高熔断阈值到30 (更谨慎)")
        print()

        # 测试提高到30
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=30,
        )
        await db.refresh(portfolio)

        portfolio_state["fg_circuit_breaker_threshold"] = 30

        print("熔断阈值=30时:")
        test_fg_values = [25, 30, 35]
        for fg in test_fg_values:
            market_data_test = {
                "btc_price_change_24h": 2.0,
                "fear_greed": {"value": fg},
                "macro": {"dxy_index": 100},
            }
            result = signal_generator.generate_signal(
                conviction_score=70,
                market_data=market_data_test,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )
            emoji = "⏸️" if result.signal.value == "HOLD" else "🟢"
            print(f"  {emoji} FG={fg}: {result.signal.value:4s} - {result.reasons[0]}")

        print("\n💡 灵活性:")
        print("  ✅ 可根据市场周期动态调整熔断阈值")
        print("  ✅ 熊市提高阈值，牛市降低阈值")

        # ========================================
        # 恢复默认值
        # ========================================
        print_header("🔄 恢复默认配置")

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

        print("✅ 已恢复为默认保守策略配置")
        print()

        # ========================================
        # 总结
        # ========================================
        print_header("📝 演示总结")

        print("🎯 核心优势:")
        print()
        print("1. 💰 策略灵活性")
        print("   - 保守策略: 高阈值，减少交易频率")
        print("   - 激进策略: 低阈值，增加交易机会")
        print("   - 谨慎策略: 超高阈值，只在极高信念时交易")
        print()
        print("2. 🛡️  风险控制")
        print("   - Fear & Greed熔断: 市场恐慌时自动停止")
        print("   - 动态仓位调整: 恐惧时自动减少仓位")
        print("   - 最小仓位保护: 防止仓位过小被拒绝")
        print()
        print("3. ⚡ 即时生效")
        print("   - 通过Admin Panel修改，下次执行立即生效")
        print("   - 无需重启服务器或修改代码")
        print()
        print("4. 🎛️  完全可控")
        print("   - 5个独立阈值，精细调控")
        print("   - 适应不同市场环境和投资风格")
        print()
        print("5. 📊 透明可见")
        print("   - 每次决策都显示使用的阈值")
        print("   - 决策原因清晰记录")
        print()

        print_header("✅ 演示完成")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(demo_trading_thresholds())
