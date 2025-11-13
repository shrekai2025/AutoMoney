import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.strategy_definition import StrategyDefinition
from app.models.portfolio import Portfolio
from datetime import datetime
import os

async def check_scheduler():
    # 数据库连接
    DATABASE_URL = "postgresql+asyncpg://automoney_user:your_secure_password_here@localhost:5432/automoney_db"
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # 查询所有激活的策略定义
        result = await db.execute(
            select(StrategyDefinition).where(StrategyDefinition.is_active == True)
        )
        definitions = result.scalars().all()
        
        print("=" * 80)
        print("策略调度状态 - {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        print("=" * 80)
        
        for definition in definitions:
            # 查询使用此模板的激活实例
            result = await db.execute(
                select(Portfolio).where(
                    Portfolio.strategy_definition_id == definition.id,
                    Portfolio.is_active == True
                )
            )
            portfolios = result.scalars().all()
            
            # 获取执行周期
            period_minutes = definition.default_params.get("rebalance_period_minutes", 10) if definition.default_params else 10
            
            print(f"\n策略模板: {definition.display_name} (ID={definition.id})")
            print(f"  执行周期: {period_minutes} 分钟")
            print(f"  激活实例数: {len(portfolios)}")
            
            if portfolios:
                print(f"  实例列表:")
                for p in portfolios:
                    print(f"    - {p.instance_name} (ID={p.id})")
                    
        # 查询最近的执行记录
        from app.models.strategy_execution import StrategyExecution
        result = await db.execute(
            select(StrategyExecution)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        last_execution = result.scalar_one_or_none()
        
        if last_execution:
            print(f"\n最近一次执行:")
            print(f"  时间: {last_execution.execution_time}")
            print(f"  策略: {last_execution.strategy_name}")
            print(f"  状态: {last_execution.status}")
            print(f"  Portfolio ID: {last_execution.portfolio_id}")
            
            # 计算下次执行时间（基于最短周期）
            if definitions:
                min_period = min(
                    d.default_params.get("rebalance_period_minutes", 10) if d.default_params else 10
                    for d in definitions
                )
                from datetime import timedelta
                next_execution = last_execution.execution_time + timedelta(minutes=min_period)
                
                now = datetime.now()
                time_until = next_execution - now.replace(tzinfo=None)
                
                print(f"\n预计下次执行:")
                print(f"  时间: {next_execution} ({time_until.total_seconds() / 60:.1f} 分钟后)")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(check_scheduler())
