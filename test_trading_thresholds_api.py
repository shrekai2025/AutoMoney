"""测试交易阈值API功能"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.services.strategy.marketplace_service import marketplace_service

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def test_trading_thresholds():
    """测试交易阈值配置功能"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🧪 测试交易阈值配置功能")
    print("=" * 100)
    print()

    async with AsyncSessionLocal() as db:
        # 获取一个Portfolio
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ Portfolio不存在")
            return

        print(f"📊 当前Portfolio配置:")
        print(f"   名称: {portfolio.name}")
        print(f"   用户ID: {portfolio.user_id}")
        print()

        print(f"🔧 当前交易阈值:")
        print(f"   Fear & Greed 熔断阈值: {portfolio.fg_circuit_breaker_threshold}")
        print(f"   Fear & Greed 仓位调整阈值: {portfolio.fg_position_adjust_threshold}")
        print(f"   买入阈值: {portfolio.buy_threshold}")
        print(f"   部分减仓阈值: {portfolio.partial_sell_threshold}")
        print(f"   全部清仓阈值: {portfolio.full_sell_threshold}")
        print()

        # 测试更新阈值
        print("📝 测试更新阈值...")
        new_thresholds = {
            "fg_circuit_breaker_threshold": 15,
            "fg_position_adjust_threshold": 25,
            "buy_threshold": 55,
            "partial_sell_threshold": 52,
            "full_sell_threshold": 40,
        }

        print(f"   新阈值:")
        for key, value in new_thresholds.items():
            print(f"      {key}: {value}")
        print()

        try:
            result = await marketplace_service.update_strategy_settings(
                db=db,
                portfolio_id=portfolio_id,
                user_id=portfolio.user_id,
                **new_thresholds
            )

            print("✅ 更新成功!")
            print(f"   返回值: {result}")
            print()

            # 验证更新
            await db.refresh(portfolio)

            print(f"🔍 验证更新后的阈值:")
            print(f"   Fear & Greed 熔断阈值: {portfolio.fg_circuit_breaker_threshold}")
            print(f"   Fear & Greed 仓位调整阈值: {portfolio.fg_position_adjust_threshold}")
            print(f"   买入阈值: {portfolio.buy_threshold}")
            print(f"   部分减仓阈值: {portfolio.partial_sell_threshold}")
            print(f"   全部清仓阈值: {portfolio.full_sell_threshold}")
            print()

            # 验证值是否正确
            all_correct = (
                portfolio.fg_circuit_breaker_threshold == 15 and
                portfolio.fg_position_adjust_threshold == 25 and
                portfolio.buy_threshold == 55 and
                portfolio.partial_sell_threshold == 52 and
                portfolio.full_sell_threshold == 40
            )

            if all_correct:
                print("✅ 所有阈值更新正确!")
            else:
                print("❌ 部分阈值更新不正确")

            # 恢复默认值
            print()
            print("🔄 恢复默认值...")
            default_thresholds = {
                "fg_circuit_breaker_threshold": 20,
                "fg_position_adjust_threshold": 30,
                "buy_threshold": 50,
                "partial_sell_threshold": 50,
                "full_sell_threshold": 45,
            }

            result = await marketplace_service.update_strategy_settings(
                db=db,
                portfolio_id=portfolio_id,
                user_id=portfolio.user_id,
                **default_thresholds
            )

            await db.refresh(portfolio)
            print("✅ 已恢复默认值")

        except Exception as e:
            print(f"❌ 更新失败: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 100)
    print("✅ 测试完成")
    print("=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_trading_thresholds())
