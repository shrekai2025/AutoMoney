"""测试Trade API"""

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
        print("测试 get_portfolio_trades API")
        print("=" * 100)
        print()

        # 测试第1页（3条记录）
        print("1. 获取第1页（page_size=3）:")
        result = await marketplace_service.get_portfolio_trades(
            db=db,
            portfolio_id=portfolio_id,
            page=1,
            page_size=3
        )

        print(f"   总记录数: {result['total']}")
        print(f"   当前页: {result['page']}")
        print(f"   每页数量: {result['page_size']}")
        print(f"   总页数: {result['total_pages']}")
        print(f"   返回记录数: {len(result['items'])}")
        print()

        print("   最近3条交易:")
        for i, trade in enumerate(result['items'], 1):
            print(f"   {i}. {trade.trade_type} {trade.symbol}")
            print(f"      Amount: {trade.amount}")
            print(f"      Price: ${trade.price}")
            print(f"      Time: {trade.executed_at}")
            if trade.realized_pnl is not None:
                print(f"      PnL: ${trade.realized_pnl}")
            print()

        # 测试第2页
        if result['total_pages'] > 1:
            print("2. 获取第2页:")
            result2 = await marketplace_service.get_portfolio_trades(
                db=db,
                portfolio_id=portfolio_id,
                page=2,
                page_size=3
            )
            print(f"   返回记录数: {len(result2['items'])}")
            for i, trade in enumerate(result2['items'], 1):
                print(f"   {i}. {trade.trade_type} {trade.symbol} at {trade.executed_at}")

        print()
        print("=" * 100)
        print("✅ 测试完成！")
        print("=" * 100)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
