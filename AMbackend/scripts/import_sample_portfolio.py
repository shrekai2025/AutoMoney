"""
导入示例策略数据到数据库
在远程服务器上运行此脚本来创建测试策略
"""
import asyncio
import json
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal
from app.models.portfolio import Portfolio
from sqlalchemy import select


async def import_portfolios(user_id: int, json_file: str = "sample_portfolios.json"):
    """
    导入策略数据

    Args:
        user_id: 用户ID（必须先创建用户）
        json_file: JSON文件路径
    """
    # 读取JSON数据
    json_path = Path(__file__).parent / json_file
    if not json_path.exists():
        print(f"❌ 文件不存在: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        portfolios_data = json.load(f)

    async with AsyncSessionLocal() as db:
        # 检查用户是否存在
        from app.models.user import User
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ 用户ID {user_id} 不存在")
            print("   请先登录创建用户，或检查user_id")
            return

        print(f"✅ 找到用户: {user.email or user.firebase_uid}")
        print(f"   开始导入 {len(portfolios_data)} 个策略...\n")

        created_count = 0
        for idx, data in enumerate(portfolios_data, 1):
            # 检查是否已存在同名策略
            result = await db.execute(
                select(Portfolio).where(
                    Portfolio.user_id == user_id,
                    Portfolio.name == data['name']
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"⚠️  策略 #{idx}: '{data['name']}' 已存在，跳过")
                continue

            # 创建策略
            portfolio = Portfolio(
                user_id=user_id,
                name=data['name'],
                strategy_name=data.get('strategy_name'),
                initial_balance=Decimal(data['initial_balance']),
                current_balance=Decimal(data['current_balance']),
                total_value=Decimal(data['total_value']),
                initial_btc_amount=Decimal(data.get('initial_btc_amount', '0.1')),
                is_active=data.get('is_active', True),
                rebalance_period_minutes=data.get('rebalance_period_minutes', 30),
                agent_weights=data.get('agent_weights'),
                consecutive_signal_threshold=data.get('consecutive_signal_threshold', 30),
                acceleration_multiplier_min=data.get('acceleration_multiplier_min', 1.1),
                acceleration_multiplier_max=data.get('acceleration_multiplier_max', 2.0),
                fg_circuit_breaker_threshold=data.get('fg_circuit_breaker_threshold', 20),
                fg_position_adjust_threshold=data.get('fg_position_adjust_threshold', 30),
                buy_threshold=data.get('buy_threshold', 50.0),
                partial_sell_threshold=data.get('partial_sell_threshold', 50.0),
                full_sell_threshold=data.get('full_sell_threshold', 45.0),
            )

            db.add(portfolio)
            created_count += 1
            print(f"✅ 策略 #{idx}: '{data['name']}' 创建成功")
            print(f"   - 执行周期: {portfolio.rebalance_period_minutes}分钟")
            print(f"   - 买入阈值: {portfolio.buy_threshold}")
            print(f"   - 状态: {'激活' if portfolio.is_active else '未激活'}\n")

        await db.commit()

        print(f"\n{'='*50}")
        print(f"✅ 导入完成!")
        print(f"   成功创建: {created_count} 个策略")
        print(f"   跳过重复: {len(portfolios_data) - created_count} 个策略")
        print(f"{'='*50}\n")


async def get_user_id():
    """获取第一个用户的ID"""
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if user:
            print(f"✅ 找到用户: {user.email or user.firebase_uid}")
            print(f"   User ID: {user.id}\n")
            return user.id
        else:
            print("❌ 数据库中没有用户")
            print("   请先登录应用创建用户\n")
            return None


if __name__ == "__main__":
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
        except ValueError:
            print("❌ 无效的user_id，必须是数字")
            print("\n使用方法:")
            print("  python scripts/import_sample_portfolio.py [user_id]")
            print("\n或自动使用第一个用户:")
            print("  python scripts/import_sample_portfolio.py")
            sys.exit(1)
    else:
        # 自动获取第一个用户ID
        user_id = asyncio.run(get_user_id())
        if not user_id:
            sys.exit(1)

    # 执行导入
    asyncio.run(import_portfolios(user_id))
