"""Admin API Endpoints"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db, get_current_admin_user
from app.models.user import User
from app.models.portfolio import Portfolio
from app.schemas.admin import (
    AdminStrategyListResponse,
    AdminStrategyItem,
    StrategyToggleRequest,
    StrategyToggleResponse,
)
from app.services.strategy.scheduler import strategy_scheduler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/strategies", response_model=AdminStrategyListResponse)
async def get_all_strategies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取所有策略列表（仅管理员）

    返回所有用户的所有策略，包括已激活和未激活的
    """
    try:
        # 查询所有策略
        result = await db.execute(
            select(Portfolio)
            .order_by(Portfolio.created_at.desc())
        )
        portfolios = result.scalars().all()

        # 转换为响应格式
        strategies = [
            AdminStrategyItem(
                id=str(portfolio.id),
                user_id=portfolio.user_id,
                name=portfolio.name,
                strategy_name=portfolio.strategy_name or "Unknown",
                is_active=portfolio.is_active,
                total_value=float(portfolio.total_value),
                total_pnl=float(portfolio.total_pnl),
                total_pnl_percent=portfolio.total_pnl_percent,
                rebalance_period_minutes=portfolio.rebalance_period_minutes,
                agent_weights=portfolio.agent_weights,
                consecutive_signal_threshold=portfolio.consecutive_signal_threshold,
                acceleration_multiplier_min=portfolio.acceleration_multiplier_min,
                acceleration_multiplier_max=portfolio.acceleration_multiplier_max,
                created_at=portfolio.created_at.isoformat(),
                updated_at=portfolio.updated_at.isoformat() if portfolio.updated_at else None,
            )
            for portfolio in portfolios
        ]

        return AdminStrategyListResponse(
            total=len(strategies),
            strategies=strategies,
        )

    except Exception as e:
        logger.error(f"获取所有策略列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get all strategies: {str(e)}")


@router.patch("/strategies/{portfolio_id}/toggle", response_model=StrategyToggleResponse)
async def toggle_strategy(
    portfolio_id: str,
    request: StrategyToggleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    切换策略的激活状态（仅管理员）

    - **portfolio_id**: Portfolio UUID
    - **is_active**: 目标状态（true=激活, false=停用）
    """
    try:
        # 查询策略
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Strategy {portfolio_id} not found")

        # 更新状态
        old_status = portfolio.is_active
        portfolio.is_active = request.is_active

        await db.commit()
        await db.refresh(portfolio)

        logger.info(
            f"Admin {current_user.email} toggled strategy {portfolio_id} "
            f"from {old_status} to {request.is_active}"
        )

        # 管理调度任务
        if request.is_active and not old_status:
            # 激活: 添加定时任务
            strategy_scheduler.add_portfolio_job(
                portfolio_id=str(portfolio.id),
                portfolio_name=portfolio.name,
                period_minutes=portfolio.rebalance_period_minutes,
            )
            logger.info(f"已为激活的策略添加定时任务: {portfolio.name}")

        elif not request.is_active and old_status:
            # 停用: 移除定时任务
            strategy_scheduler.remove_portfolio_job(str(portfolio.id))
            logger.info(f"已移除停用策略的定时任务: {portfolio.name}")

        return StrategyToggleResponse(
            success=True,
            portfolio_id=str(portfolio.id),
            is_active=portfolio.is_active,
            message=f"Strategy {portfolio.name} is now {'active' if portfolio.is_active else 'inactive'}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换策略状态失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle strategy: {str(e)}")
