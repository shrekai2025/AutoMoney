"""
更新旧策略的business_agents配置

确保旧策略(multi_agent_btc_v1)也有正确的business_agents定义,
以便Scheduler能够正确选择Agent执行器
"""

import asyncio
from app.db.session import AsyncSessionLocal
from app.models.strategy_definition import StrategyDefinition
from sqlalchemy import select


async def update_old_strategy():
    """更新旧策略模板的business_agents"""
    async with AsyncSessionLocal() as db:
        # 查询旧策略模板
        result = await db.execute(
            select(StrategyDefinition).where(
                StrategyDefinition.name == 'multi_agent_btc_v1'
            )
        )
        strategy = result.scalar_one_or_none()
        
        if not strategy:
            print("❌ 未找到multi_agent_btc_v1策略模板")
            return
        
        print(f"找到策略: {strategy.display_name}")
        print(f"当前business_agents: {strategy.business_agents}")
        
        # 如果没有配置business_agents,则配置
        if not strategy.business_agents or len(strategy.business_agents) == 0:
            strategy.business_agents = ['macro', 'ta', 'onchain']
            await db.commit()
            print(f"✅ 已更新旧策略的business_agents: {strategy.business_agents}")
        else:
            print(f"✅ 旧策略已有business_agents配置: {strategy.business_agents}")


async def verify_all_strategies():
    """验证所有策略模板的配置"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(StrategyDefinition))
        strategies = result.scalars().all()
        
        print(f"\n所有策略模板配置:")
        print("=" * 80)
        for s in strategies:
            print(f"ID: {s.id}")
            print(f"  Name: {s.name}")
            print(f"  Display: {s.display_name}")
            print(f"  Business Agents: {s.business_agents}")
            print(f"  Decision Agent: {s.decision_agent_class}")
            print(f"  Rebalance Period: {s.rebalance_period_minutes} min")
            print("-" * 80)


if __name__ == "__main__":
    print("更新旧策略的business_agents配置...")
    asyncio.run(update_old_strategy())
    
    print("\n验证所有策略配置...")
    asyncio.run(verify_all_strategies())
    
    print("\n✅ 完成!")

