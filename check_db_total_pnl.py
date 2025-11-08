"""直接查询数据库中的total_pnl值"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text
from app.core.config import settings
from app.models.portfolio import Portfolio


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

    async with SessionLocal() as db:
        print("=" * 100)
        print("查询数据库中的total_pnl值")
        print("=" * 100)
        print()

        # 直接查询数据库
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if portfolio:
            print(f"Portfolio: {portfolio.name}")
            print(f"ID: {portfolio.id}")
            print()
            print(f"total_pnl (数据库值): ${float(portfolio.total_pnl):.2f}")
            print(f"total_pnl_percent: {portfolio.total_pnl_percent:.2f}%")
            print(f"total_value: ${float(portfolio.total_value):.2f}")
            print(f"current_balance: ${float(portfolio.current_balance):.2f}")
            print(f"initial_balance: ${float(portfolio.initial_balance):.2f}")
            print()

            # 也查一下trades表
            trades_result = await db.execute(
                text("""
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN trade_type = 'SELL' THEN COALESCE(realized_pnl, 0) ELSE 0 END) as total_realized_pnl
                FROM trades
                WHERE portfolio_id = :pid
                """),
                {"pid": portfolio_id}
            )
            trade_stats = trades_result.fetchone()
            if trade_stats:
                print(f"交易统计:")
                print(f"  总交易数: {trade_stats[0]}")
                print(f"  已实现盈亏(来自SELL): ${float(trade_stats[1] or 0):.2f}")

        print()
        print("=" * 100)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
