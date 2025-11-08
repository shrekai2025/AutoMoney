"""验证列表页和详情页的Total P&L是否一致"""

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
        print("验证列表页 vs 详情页 Total P&L 一致性")
        print("=" * 100)
        print()

        # 获取列表页数据
        list_response = await marketplace_service.get_marketplace_list(db, user_id=1)
        list_strategy = None
        for strategy in list_response.strategies:
            if strategy.id == portfolio_id:
                list_strategy = strategy
                break

        if not list_strategy:
            print("❌ 在列表页中未找到该策略")
            return

        # 获取详情页数据
        detail = await marketplace_service.get_strategy_detail(db, portfolio_id)

        print(f"Portfolio: {detail.name}")
        print()

        print("列表页显示:")
        print(f"  Total P&L: ${list_strategy.total_pnl:.2f}")
        print()

        print("详情页显示:")
        print(f"  Realized P&L:   ${detail.total_realized_pnl:.2f}")
        print(f"  Unrealized P&L: ${detail.total_unrealized_pnl:.2f}")
        print(f"  ─────────────────────────────")
        print(f"  Total P&L:      ${detail.total_pnl:.2f} ({detail.total_pnl_percent:.2f}%)")
        print()

        print("对比验证:")
        diff = abs(list_strategy.total_pnl - detail.total_pnl)
        print(f"  列表页: ${list_strategy.total_pnl:.2f}")
        print(f"  详情页: ${detail.total_pnl:.2f}")
        print(f"  差异:   ${diff:.2f}")
        print()

        if diff < 0.01:
            print("  ✅ 验证通过！列表页和详情页的Total P&L一致")
        else:
            print(f"  ❌ 验证失败！存在差异: ${diff:.2f}")

        print()
        print("=" * 100)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
