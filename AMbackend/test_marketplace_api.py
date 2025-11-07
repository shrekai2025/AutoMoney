"""测试Strategy Marketplace API端点"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services.strategy.marketplace_service import marketplace_service


async def test_marketplace_endpoints():
    """测试Marketplace端点"""
    print("\n" + "=" * 80)
    print("Strategy Marketplace API测试")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        try:
            # 1. 获取测试用户
            print("\n1. 获取测试用户...")
            stmt = select(User).where(User.email == "yeheai9906@gmail.com")
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                print("❌ 未找到测试用户")
                return

            print(f"✅ 找到测试用户: {user.email} (ID: {user.id})")

            # 2. 测试获取策略市场列表
            print("\n2. 测试获取策略市场列表...")
            print("-" * 80)

            marketplace_list = await marketplace_service.get_marketplace_list(
                db=db,
                user_id=user.id,
                risk_level=None,
                sort_by="return",
            )

            print(f"✅ 获取到 {len(marketplace_list.strategies)} 个策略")

            for idx, strategy in enumerate(marketplace_list.strategies, 1):
                print(f"\n  策略 #{idx}:")
                print(f"    名称: {strategy.name}")
                print(f"    副标题: {strategy.subtitle}")
                print(f"    ID: {strategy.id}")
                print(f"    标签: {', '.join(strategy.tags)}")
                print(f"    年化收益: {strategy.annualized_return:.2f}%")
                print(f"    最大回撤: {strategy.max_drawdown:.2f}%")
                print(f"    夏普比率: {strategy.sharpe_ratio:.2f}")
                print(f"    资金池规模: ${strategy.pool_size:,.2f}")
                print(f"    Squad大小: {strategy.squad_size} Agents")
                print(f"    风险等级: {strategy.risk_level}")
                print(f"    历史数据点: {len(strategy.history)} 个")

            # 3. 测试获取策略详情
            if marketplace_list.strategies:
                print("\n3. 测试获取策略详情...")
                print("-" * 80)

                first_strategy_id = marketplace_list.strategies[0].id
                detail = await marketplace_service.get_strategy_detail(
                    db=db, portfolio_id=first_strategy_id
                )

                print(f"✅ 获取策略详情成功: {detail.name}")
                print(f"\n  基本信息:")
                print(f"    描述: {detail.description}")
                print(f"    标签: {', '.join(detail.tags)}")

                print(f"\n  性能指标:")
                print(f"    年化收益: {detail.performance_metrics.annualized_return:.2f}%")
                print(f"    最大回撤: {detail.performance_metrics.max_drawdown:.2f}%")
                print(f"    夏普比率: {detail.performance_metrics.sharpe_ratio:.2f}")
                print(f"    Sortino比率: {detail.performance_metrics.sortino_ratio or 'N/A'}")

                print(f"\n  Conviction摘要:")
                print(f"    分数: {detail.conviction_summary.score:.1f}")
                print(f"    消息: {detail.conviction_summary.message[:100]}...")
                print(f"    更新时间: {detail.conviction_summary.updated_at}")

                print(f"\n  Squad Agents: {len(detail.squad_agents)} 个")
                for agent in detail.squad_agents:
                    print(f"    - {agent.name} ({agent.role}): {agent.weight}")

                print(f"\n  性能历史:")
                print(f"    策略数据点: {len(detail.performance_history.strategy)} 个")
                print(f"    BTC基准数据点: {len(detail.performance_history.btc_benchmark)} 个")
                print(f"    ETH基准数据点: {len(detail.performance_history.eth_benchmark)} 个")
                print(f"    日期: {len(detail.performance_history.dates)} 个")

                print(f"\n  最近操作: {len(detail.recent_activities)} 条")
                for idx, activity in enumerate(detail.recent_activities[:3], 1):
                    print(f"    #{idx}: {activity.date}")
                    print(f"       信号: {activity.signal[:50]}")
                    print(f"       动作: {activity.action}")
                    print(f"       结果: {activity.result}")
                    print(f"       Agent: {activity.agent}")

                print(f"\n  策略参数:")
                print(f"    资产配置: {detail.parameters.assets}")
                print(f"    调仓周期: {detail.parameters.rebalance_period}")
                print(f"    风险等级: {detail.parameters.risk_level}")
                print(f"    最小投资: {detail.parameters.min_investment}")
                print(f"    锁定期: {detail.parameters.lockup_period}")
                print(f"    管理费: {detail.parameters.management_fee}")
                print(f"    业绩费: {detail.parameters.performance_fee}")

                print(f"\n  策略哲学:")
                print(f"    {detail.philosophy[:150]}...")

            # 4. 测试风险等级过滤
            print("\n4. 测试风险等级过滤...")
            print("-" * 80)

            for risk in ["low", "medium", "high"]:
                filtered_list = await marketplace_service.get_marketplace_list(
                    db=db, user_id=user.id, risk_level=risk, sort_by="return"
                )
                print(f"  风险等级 '{risk}': {len(filtered_list.strategies)} 个策略")

            # 5. 测试排序
            print("\n5. 测试不同排序方式...")
            print("-" * 80)

            for sort_method in ["return", "risk", "tvl", "sharpe"]:
                sorted_list = await marketplace_service.get_marketplace_list(
                    db=db, user_id=user.id, risk_level=None, sort_by=sort_method
                )
                print(f"  按 '{sort_method}' 排序: {len(sorted_list.strategies)} 个策略")

            print("\n" + "=" * 80)
            print("✅ 所有测试通过！")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(test_marketplace_endpoints())
