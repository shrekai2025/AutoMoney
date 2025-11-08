#!/usr/bin/env python3
"""验证 agent_weights 修复"""

import sys
sys.path.append('/Users/uniteyoo/Documents/AutoMoney/AMbackend')

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.portfolio import Portfolio

async def verify_fix():
    """验证修复是否成功"""

    # 创建数据库连接
    DATABASE_URL = "postgresql+asyncpg://localhost/automoney"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 查询所有 portfolio
        result = await session.execute(
            select(Portfolio).order_by(Portfolio.created_at.desc())
        )
        portfolios = result.scalars().all()

        print(f"Total portfolios: {len(portfolios)}\n")

        for portfolio in portfolios:
            print(f"{'='*70}")
            print(f"Portfolio: {portfolio.name}")
            print(f"ID: {portfolio.id}")
            print(f"User ID: {portfolio.user_id}")
            print(f"Active: {portfolio.is_active}")
            print(f"Rebalance Period: {portfolio.rebalance_period_minutes} minutes")
            print(f"\nAgent Weights:")
            print(f"  {portfolio.agent_weights}")
            print(f"\nConsecutive Signal Config:")
            print(f"  Threshold: {portfolio.consecutive_signal_threshold}")
            print(f"  Min Multiplier: {portfolio.acceleration_multiplier_min}")
            print(f"  Max Multiplier: {portfolio.acceleration_multiplier_max}")
            print()

if __name__ == "__main__":
    asyncio.run(verify_fix())
