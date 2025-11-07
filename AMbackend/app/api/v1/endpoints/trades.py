"""Trade API endpoints

提供交易记录相关的 REST API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.deps import get_db
from app.core.deps import get_current_user
from app.models import User, Trade, Portfolio
from app.schemas.strategy import TradeResponse

router = APIRouter()


@router.get("/", response_model=List[TradeResponse])
async def list_trades(
    portfolio_id: str,
    symbol: Optional[str] = Query(None, description="按币种筛选 (BTC/ETH)"),
    trade_type: Optional[str] = Query(None, description="按交易类型筛选 (BUY/SELL)"),
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取交易历史记录
    """
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

    # 构建查询
    query = select(Trade).where(Trade.portfolio_id == portfolio_id)

    if symbol:
        query = query.where(Trade.symbol == symbol.upper())

    if trade_type:
        query = query.where(Trade.trade_type == trade_type.upper())

    # 排序和分页
    query = query.order_by(Trade.executed_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    trades = result.scalars().all()

    return [TradeResponse.from_orm(t) for t in trades]


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取单个交易详情
    """
    # 查询交易
    result = await db.execute(
        select(Trade).where(Trade.id == trade_id)
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )

    # 验证所有权（通过 portfolio）
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == trade.portfolio_id,
            Portfolio.user_id == current_user.id,
        )
    )
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return TradeResponse.from_orm(trade)
