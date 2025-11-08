"""测试详情页API返回的total_pnl字段"""

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
        print("测试详情页API返回值")
        print("=" * 100)
        print()

        # 直接调用service方法（绕过HTTP认证）
        detail = await marketplace_service.get_strategy_detail(db, portfolio_id)

        print(f"Portfolio: {detail.name}")
        print()
        print("返回的字段值:")
        print(f"  total_unrealized_pnl: {detail.total_unrealized_pnl}")
        print(f"  total_realized_pnl: {detail.total_realized_pnl}")
        print(f"  total_pnl: {detail.total_pnl}")
        print(f"  total_pnl_percent: {detail.total_pnl_percent}%")
        print()

        if detail.total_pnl == 0.95:
            print("✅ total_pnl 正确！")
        else:
            print(f"❌ total_pnl 不正确！期望: 0.95, 实际: {detail.total_pnl}")

        print("=" * 100)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
