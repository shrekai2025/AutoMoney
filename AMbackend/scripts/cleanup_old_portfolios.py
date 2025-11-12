"""清理旧的Portfolio数据

删除所有现有Portfolio及关联数据（Trades, StrategyExecutions等）
保留User数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.models import Portfolio, PortfolioHolding, Trade, PortfolioSnapshot, StrategyExecution, AgentExecution


async def cleanup_old_data():
    """清理旧数据"""
    print("🧹 开始清理旧数据...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 删除AgentExecutions
            result = await db.execute(delete(AgentExecution))
            print(f"✓ 删除了 {result.rowcount} 条 AgentExecution 记录")
            
            # 2. 删除StrategyExecutions
            result = await db.execute(delete(StrategyExecution))
            print(f"✓ 删除了 {result.rowcount} 条 StrategyExecution 记录")
            
            # 3. 删除Trades
            result = await db.execute(delete(Trade))
            print(f"✓ 删除了 {result.rowcount} 条 Trade 记录")
            
            # 4. 删除PortfolioSnapshots
            result = await db.execute(delete(PortfolioSnapshot))
            print(f"✓ 删除了 {result.rowcount} 条 PortfolioSnapshot 记录")
            
            # 5. 删除PortfolioHoldings
            result = await db.execute(delete(PortfolioHolding))
            print(f"✓ 删除了 {result.rowcount} 条 PortfolioHolding 记录")
            
            # 6. 删除Portfolios
            result = await db.execute(delete(Portfolio))
            print(f"✓ 删除了 {result.rowcount} 条 Portfolio 记录")
            
            await db.commit()
            print("\n✅ 数据清理完成!")
            print("保留了所有User数据")
            
        except Exception as e:
            print(f"\n❌ 清理失败: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("清理旧Portfolio数据")
    print("=" * 60)
    print("\n警告: 此操作将删除所有Portfolio及其关联数据!")
    print("User数据将被保留\n")
    
    response = input("确认继续? (yes/no): ")
    if response.lower() != "yes":
        print("已取消操作")
        sys.exit(0)
    
    asyncio.run(cleanup_old_data())

