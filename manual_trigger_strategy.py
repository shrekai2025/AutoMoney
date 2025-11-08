"""
手动触发策略执行以测试
"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models import Portfolio
from app.services.strategy.scheduler import strategy_scheduler

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def manual_trigger():
    """手动触发一次策略执行"""

    print("=" * 100)
    print("手动触发策略执行")
    print("=" * 100)
    print()

    # 初始化调度器
    await strategy_scheduler.initialize()

    # 执行Portfolio
    portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"  # Paper Trading 测试组合

    print(f"正在执行 Portfolio: {portfolio_id}")
    print()

    try:
        await strategy_scheduler.execute_single_portfolio(portfolio_id)
        print()
        print("=" * 100)
        print("✅ 策略执行完成！")
        print("=" * 100)
    except Exception as e:
        print()
        print("=" * 100)
        print(f"❌ 策略执行失败: {e}")
        print("=" * 100)
        import traceback
        traceback.print_exc()

    await strategy_scheduler.engine.dispose()

if __name__ == "__main__":
    asyncio.run(manual_trigger())
