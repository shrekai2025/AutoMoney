"""测试Total P&L计算是否包含已实现和未实现盈亏"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.services.strategy.marketplace_service import marketplace_service


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

    async with SessionLocal() as db:
        print("=" * 100)
        print("测试 Total P&L 计算")
        print("=" * 100)
        print()

        # 获取策略详情
        detail = await marketplace_service.get_strategy_detail(db, portfolio_id)

        print(f"Portfolio: {detail.name}")
        print(f"ID: {detail.id}")
        print()

        print("持仓情况:")
        if detail.holdings:
            for holding in detail.holdings:
                print(f"  {holding['symbol']}:")
                print(f"    Amount: {holding['amount']}")
                print(f"    Cost Basis: ${holding['cost_basis']:.2f}")
                print(f"    Market Value: ${holding['market_value']:.2f}")
                print(f"    Unrealized P&L: ${holding['unrealized_pnl']:.2f} ({holding['unrealized_pnl_percent']:.2f}%)")
        else:
            print("  无持仓")
        print()

        print("盈亏统计:")
        print(f"  已实现盈亏 (Realized P&L):   ${detail.total_realized_pnl:.2f}")
        print(f"  未实现盈亏 (Unrealized P&L): ${detail.total_unrealized_pnl:.2f}")
        print(f"  ─────────────────────────────────────")
        print(f"  总盈亏 (Total P&L):          ${detail.total_pnl:.2f} ({detail.total_pnl_percent:.2f}%)")
        print()

        print("验证:")
        calculated_total = detail.total_realized_pnl + detail.total_unrealized_pnl
        print(f"  计算验证: {detail.total_realized_pnl:.2f} + {detail.total_unrealized_pnl:.2f} = {calculated_total:.2f}")
        print(f"  返回值:   {detail.total_pnl:.2f}")

        if abs(calculated_total - detail.total_pnl) < 0.01:
            print("  ✅ 验证通过！Total P&L = Realized P&L + Unrealized P&L")
        else:
            print("  ❌ 验证失败！数值不匹配")

        print()
        print("=" * 100)

        if detail.total_realized_pnl != 0:
            print("✅ 测试通过！已实现盈亏已正确包含在Total P&L中")
        elif detail.total_unrealized_pnl != 0:
            print("⚠️  警告：有未实现盈亏但无已实现盈亏（可能正常，取决于是否有卖出）")
        else:
            print("⚠️  警告：总盈亏为0（可能正常，取决于实际交易情况）")

        print("=" * 100)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
