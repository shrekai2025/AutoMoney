"""检查signal列的数据库定义"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def check_signal_column():
    """检查signal列的定义"""

    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # 查询strategy_executions表的signal列定义
        result = await conn.execute(text("""
            SELECT
                column_name,
                data_type,
                column_default,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'strategy_executions'
            AND column_name IN ('signal', 'signal_strength', 'position_size')
            ORDER BY ordinal_position;
        """))

        rows = result.fetchall()

        print("=" * 100)
        print("📊 strategy_executions表的相关列定义")
        print("=" * 100)
        print()

        for row in rows:
            print(f"列名: {row[0]}")
            print(f"  类型: {row[1]}")
            print(f"  默认值: {row[2] if row[2] else 'NULL'}")
            print(f"  可为空: {row[3]}")
            print()

        # 查询最近10条记录的signal值
        print("=" * 100)
        print("📜 最近10条记录的signal值")
        print("=" * 100)
        print()

        result2 = await conn.execute(text("""
            SELECT
                id,
                execution_time,
                signal,
                signal_strength,
                conviction_score,
                status
            FROM strategy_executions
            ORDER BY execution_time DESC
            LIMIT 10;
        """))

        rows2 = result2.fetchall()

        for row in rows2:
            print(f"ID: {str(row[0])[:8]}...")
            print(f"  时间: {row[1]}")
            print(f"  signal: '{row[2]}' (类型: {type(row[2]).__name__})")
            print(f"  signal_strength: {row[3]}")
            print(f"  conviction_score: {row[4]}")
            print(f"  status: {row[5]}")
            print()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_signal_column())
