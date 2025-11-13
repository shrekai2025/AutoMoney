"""
自动清理卡住的策略执行记录

此脚本应该通过cron或调度器定期运行（建议每小时一次）
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
import logging

from app.models.strategy_execution import StrategyExecution
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_stuck_executions():
    """清理超过1小时仍处于running状态的执行记录"""

    # 创建异步引擎
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        # 查找卡住的记录
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        stmt = select(StrategyExecution).where(
            StrategyExecution.status == "running",
            StrategyExecution.execution_time < one_hour_ago
        )

        result = await db.execute(stmt)
        stuck_executions = result.scalars().all()

        if not stuck_executions:
            logger.info("✓ 没有发现卡住的执行记录")
            return 0

        logger.warning(f"⚠️ 发现 {len(stuck_executions)} 条卡住的执行记录")

        # 更新状态为failed
        for execution in stuck_executions:
            execution.status = "failed"
            execution.error_message = "Execution stuck - auto-cleaned by system (exceeded 1 hour timeout)"

            stuck_for = datetime.utcnow() - execution.execution_time
            logger.info(
                f"  清理执行记录: ID={execution.id}, "
                f"卡住时长={stuck_for}, "
                f"执行时间={execution.execution_time}"
            )

        await db.commit()
        logger.info(f"✓ 已清理 {len(stuck_executions)} 条记录")

        return len(stuck_executions)


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始清理卡住的策略执行记录")
    logger.info(f"运行时间: {datetime.now()}")
    logger.info("=" * 60)

    try:
        cleaned_count = await cleanup_stuck_executions()

        logger.info("=" * 60)
        logger.info(f"清理完成: 共清理 {cleaned_count} 条记录")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ 清理失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
