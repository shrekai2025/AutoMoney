"""手动更新Portfolio的total_pnl以使用正确的计算逻辑"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.services.trading.portfolio_service import portfolio_service
from app.services.market.real_market_data import real_market_data_service


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

    async with SessionLocal() as db:
        print("=" * 100)
        print("修复Portfolio的total_pnl计算")
        print("=" * 100)
        print()

        # 获取portfolio
        portfolio = await portfolio_service.get_portfolio(db, portfolio_id)
        if not portfolio:
            print(f"❌ Portfolio not found: {portfolio_id}")
            return

        print(f"Portfolio: {portfolio.name}")
        print(f"修复前的total_pnl: ${portfolio.total_pnl:.2f}")
        print()

        # 获取当前BTC价格
        btc_price = await real_market_data_service.get_btc_price()
        print(f"当前BTC价格: ${btc_price:.2f}")
        print()

        # 调用update_portfolio_value，这会使用新的计算逻辑
        print("正在重新计算total_pnl...")
        await portfolio_service.update_portfolio_value(db, portfolio, btc_price)

        # 刷新获取更新后的值
        await db.refresh(portfolio)

        print()
        print(f"修复后的total_pnl: ${portfolio.total_pnl:.2f}")
        print(f"修复后的total_pnl_percent: {portfolio.total_pnl_percent:.2f}%")
        print()
        print("=" * 100)
        print("✅ Total P&L已更新为正确的值（已实现盈亏 + 未实现盈亏）")
        print("=" * 100)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
