"""分析交易记录和账户余额变化"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc, text
from app.core.config import settings
from app.models.portfolio import Trade


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

    async with SessionLocal() as db:
        print("=" * 120)
        print("分析交易记录和账户余额变化")
        print("=" * 120)
        print()

        # 获取所有交易
        result = await db.execute(
            select(Trade)
            .where(Trade.portfolio_id == portfolio_id)
            .order_by(Trade.executed_at)
        )
        trades = result.scalars().all()

        print(f"总交易数: {len(trades)}")
        print()

        total_realized = 0
        for i, trade in enumerate(trades, 1):
            print(f"交易 #{i}: {trade.trade_type} {trade.symbol}")
            print(f"  时间: {trade.executed_at}")
            print(f"  数量: {float(trade.amount):.8f}")
            print(f"  价格: ${float(trade.price):.2f}")
            print(f"  总价值: ${float(trade.total_value):.2f}")
            print(f"  手续费: ${float(trade.fee):.4f}")
            print(f"  余额变化: ${float(trade.balance_before or 0):.2f} → ${float(trade.balance_after or 0):.2f}")

            if trade.trade_type == "SELL" and trade.realized_pnl:
                print(f"  已实现盈亏: ${float(trade.realized_pnl):.2f} ({float(trade.realized_pnl_percent or 0):.2f}%)")
                total_realized += float(trade.realized_pnl)

            print()

        print("=" * 120)
        print("总结:")
        print(f"  累计已实现盈亏: ${total_realized:.2f}")
        print(f"  最终余额: ${float(trades[-1].balance_after or 0):.2f}")
        print(f"  初始余额: ${float(trades[0].balance_before or 0):.2f}")
        print(f"  余额增加: ${float(trades[-1].balance_after or 0) - float(trades[0].balance_before or 0):.2f}")
        print()

        if abs(total_realized - (float(trades[-1].balance_after or 0) - float(trades[0].balance_before or 0))) > 0.01:
            print("⚠️  注意：已实现盈亏与余额增加不匹配！")
            print(f"     差异: ${abs(total_realized - (float(trades[-1].balance_after or 0) - float(trades[0].balance_before or 0))):.2f}")
        else:
            print("✅ 已实现盈亏 = 余额增加（正确）")

        print("=" * 120)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
