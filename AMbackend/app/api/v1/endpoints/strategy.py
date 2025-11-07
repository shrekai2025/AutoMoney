"""Strategy Execution API endpoints

提供策略执行相关的 REST API
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.core.deps import get_current_user
from app.models import User, StrategyExecution, Portfolio, Trade
from app.schemas.strategy import (
    StrategyExecutionResponse,
    TradeResponse,
)
from app.services.strategy.strategy_orchestrator import strategy_orchestrator
from app.services.market.real_market_data import real_market_data_service
from app.services.strategy.real_agent_executor import real_agent_executor
from app.services.indicators.calculator import IndicatorCalculator
from app.services.data_collectors.manager import data_manager

router = APIRouter()


@router.get("/", response_model=List[StrategyExecutionResponse])
async def list_strategy_executions(
    portfolio_id: Optional[str] = Query(None, description="按投资组合ID筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取策略执行历史记录
    """
    # 构建查询
    query = select(StrategyExecution).where(
        StrategyExecution.user_id == current_user.id
    )

    # 如果指定了 portfolio_id，需要通过 trades 关联查询
    if portfolio_id:
        # 验证组合所有权
        result = await db.execute(
            select(Portfolio).where(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == current_user.id,
            )
        )
        portfolio = result.scalar_one_or_none()
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        # 通过 Trade 表关联查询
        query = query.join(Trade, Trade.execution_id == StrategyExecution.id).where(
            Trade.portfolio_id == portfolio_id
        )

    if status:
        query = query.where(StrategyExecution.status == status)

    # 排序和分页
    query = query.order_by(StrategyExecution.execution_time.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    executions = result.scalars().all()

    return [StrategyExecutionResponse.from_orm(e) for e in executions]


@router.get("/{execution_id}", response_model=StrategyExecutionResponse)
async def get_strategy_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取单个策略执行详情
    """
    result = await db.execute(
        select(StrategyExecution).where(
            StrategyExecution.id == execution_id,
            StrategyExecution.user_id == current_user.id,
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy execution not found"
        )

    return StrategyExecutionResponse.from_orm(execution)


@router.get("/{execution_id}/trades", response_model=List[TradeResponse])
async def get_execution_trades(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取策略执行相关的交易记录
    """
    # 验证策略执行所有权
    result = await db.execute(
        select(StrategyExecution).where(
            StrategyExecution.id == execution_id,
            StrategyExecution.user_id == current_user.id,
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy execution not found"
        )

    # 查询交易记录
    result = await db.execute(
        select(Trade).where(Trade.execution_id == execution_id)
    )
    trades = result.scalars().all()

    return [TradeResponse.from_orm(t) for t in trades]


@router.post("/manual-trigger", response_model=StrategyExecutionResponse)
async def manual_trigger_strategy(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    手动触发策略执行

    用于测试或立即执行策略（不等待定时任务）
    """
    # 验证组合所有权
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.holdings))
        .where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id,
            Portfolio.is_active == True,
        )
    )
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active portfolio not found"
        )

    # 执行策略
    try:
        # 1. 获取真实市场数据
        market_data = await real_market_data_service.get_complete_market_snapshot()

        # 2. 添加技术指标
        all_data = await data_manager.collect_all()
        if hasattr(all_data, 'btc_ohlcv') and all_data.btc_ohlcv:
            indicators = IndicatorCalculator.calculate_all(all_data.btc_ohlcv)
            market_data["indicators"] = indicators

        # 3. 执行真实 Agent 分析
        agent_outputs = await real_agent_executor.execute_all_agents(
            market_data=market_data,
            db=db,
            user_id=current_user.id,
            strategy_execution_id=None,  # Will be set after execution record created
        )

        # 4. 执行策略
        execution = await strategy_orchestrator.execute_strategy(
            db=db,
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            market_data=market_data,
            agent_outputs=agent_outputs,
        )

        return StrategyExecutionResponse.from_orm(execution)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy execution failed: {str(e)}"
        )
