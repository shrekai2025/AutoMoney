"""
检查卡住的策略执行记录

可以指定时间阈值（默认10分钟）来检查卡住的执行记录
"""

import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import logging

from app.models.strategy_execution import StrategyExecution
from app.models.portfolio import Portfolio
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_stuck_executions(minutes_threshold: int = 10, portfolio_id: str = None):
    """检查卡住的执行记录
    
    Args:
        minutes_threshold: 时间阈值（分钟），超过这个时间的running记录会被标记为卡住
        portfolio_id: 可选的portfolio_id，只检查特定portfolio的记录
    """
    # 创建异步引擎
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        # 查找卡住的记录
        threshold_time = datetime.utcnow() - timedelta(minutes=minutes_threshold)

        stmt = select(StrategyExecution).where(
            StrategyExecution.status == "running",
            StrategyExecution.execution_time < threshold_time
        )
        
        # 如果指定了portfolio_id，添加过滤条件
        if portfolio_id:
            stmt = stmt.where(StrategyExecution.portfolio_id == portfolio_id)

        result = await db.execute(stmt)
        stuck_executions = result.scalars().all()

        if not stuck_executions:
            logger.info(f"✓ 没有发现超过{minutes_threshold}分钟的running状态执行记录")
            return []

        logger.warning(f"⚠️ 发现 {len(stuck_executions)} 条卡住的执行记录（超过{minutes_threshold}分钟）")
        
        # 显示详细信息
        for execution in stuck_executions:
            stuck_for = datetime.utcnow() - execution.execution_time
            stuck_minutes = stuck_for.total_seconds() / 60
            
            # 获取portfolio信息
            portfolio_name = "Unknown"
            if execution.portfolio_id:
                portfolio_result = await db.execute(
                    select(Portfolio).where(Portfolio.id == execution.portfolio_id)
                )
                portfolio = portfolio_result.scalar_one_or_none()
                if portfolio:
                    portfolio_name = portfolio.instance_name or portfolio.name or "Unknown"
            
            logger.info(
                f"\n  执行ID: {execution.id}\n"
                f"  Portfolio: {portfolio_name} ({execution.portfolio_id})\n"
                f"  执行时间: {execution.execution_time}\n"
                f"  卡住时长: {stuck_minutes:.1f}分钟 ({stuck_for})\n"
                f"  用户ID: {execution.user_id}"
            )

        return stuck_executions


async def cleanup_stuck_executions(minutes_threshold: int = 10, portfolio_id: str = None, dry_run: bool = True):
    """清理卡住的执行记录
    
    Args:
        minutes_threshold: 时间阈值（分钟）
        portfolio_id: 可选的portfolio_id
        dry_run: 如果为True，只显示不实际清理
    """
    stuck_executions = await check_stuck_executions(minutes_threshold, portfolio_id)
    
    if not stuck_executions:
        return 0
    
    if dry_run:
        logger.info("\n⚠️ 这是dry-run模式，不会实际更新数据库")
        logger.info("如果要实际清理，请使用 --cleanup 参数")
        return len(stuck_executions)
    
    # 实际清理
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        threshold_time = datetime.utcnow() - timedelta(minutes=minutes_threshold)
        
        stmt = select(StrategyExecution).where(
            StrategyExecution.status == "running",
            StrategyExecution.execution_time < threshold_time
        )
        
        if portfolio_id:
            stmt = stmt.where(StrategyExecution.portfolio_id == portfolio_id)

        result = await db.execute(stmt)
        stuck_executions = result.scalars().all()

        for execution in stuck_executions:
            execution.status = "failed"
            execution.error_message = f"Execution stuck - auto-cleaned by system (exceeded {minutes_threshold} minutes timeout)"
            execution.error_details = {
                "error_type": "execution_stuck",
                "stuck_minutes": (datetime.utcnow() - execution.execution_time).total_seconds() / 60,
                "cleaned_at": datetime.utcnow().isoformat(),
            }

        await db.commit()
        logger.info(f"✓ 已清理 {len(stuck_executions)} 条记录")
        return len(stuck_executions)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="检查并清理卡住的策略执行记录")
    parser.add_argument("--minutes", type=int, default=10, help="时间阈值（分钟），默认10分钟")
    parser.add_argument("--portfolio-id", type=str, help="只检查特定portfolio的记录")
    parser.add_argument("--cleanup", action="store_true", help="实际清理记录（默认只检查）")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("检查卡住的策略执行记录")
    logger.info(f"时间阈值: {args.minutes}分钟")
    if args.portfolio_id:
        logger.info(f"Portfolio ID: {args.portfolio_id}")
    logger.info(f"模式: {'清理' if args.cleanup else '检查（dry-run）'}")
    logger.info(f"运行时间: {datetime.now()}")
    logger.info("=" * 60)

    try:
        if args.cleanup:
            cleaned_count = await cleanup_stuck_executions(
                minutes_threshold=args.minutes,
                portfolio_id=args.portfolio_id,
                dry_run=False
            )
            logger.info("=" * 60)
            logger.info(f"清理完成: 共清理 {cleaned_count} 条记录")
        else:
            stuck_count = await check_stuck_executions(
                minutes_threshold=args.minutes,
                portfolio_id=args.portfolio_id
            )
            logger.info("=" * 60)
            logger.info(f"检查完成: 发现 {len(stuck_count)} 条卡住的记录")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ 操作失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

