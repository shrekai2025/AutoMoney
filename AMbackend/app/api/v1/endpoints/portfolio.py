"""Portfolio API endpoints

提供投资组合相关的 RESTful API
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.core.deps import get_current_user
from app.models import User, Portfolio, PortfolioHolding, PortfolioSnapshot
from app.schemas.strategy import (
    PortfolioCreate,
    PortfolioResponse,
    PortfolioDetailResponse,
    PortfolioHoldingResponse,
    PortfolioSnapshotResponse,
)
from app.services.trading.portfolio_service import portfolio_service

router = APIRouter()


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的投资组合
    """
    portfolio = await portfolio_service.create_portfolio(
        db=db,
        user_id=current_user.id,
        portfolio_data=portfolio_data,
    )

    return PortfolioResponse.from_orm(portfolio)


@router.get("/", response_model=List[PortfolioResponse])
async def list_portfolios(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户的所有投资组合列表
    """
    portfolios = await portfolio_service.get_user_portfolios(
        db=db,
        user_id=current_user.id,
        active_only=active_only,
    )

    return [PortfolioResponse.from_orm(p) for p in portfolios]


@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
async def get_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取投资组合详情（包含持仓信息）
    """
    # 查询组合（with eager loading）
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.holdings))
        .where(
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

    # 构建响应
    holdings = [PortfolioHoldingResponse.from_orm(h) for h in portfolio.holdings]

    return PortfolioDetailResponse(
        **PortfolioResponse.from_orm(portfolio).dict(),
        holdings=holdings,
    )


@router.get("/{portfolio_id}/snapshots", response_model=List[PortfolioSnapshotResponse])
async def get_portfolio_snapshots(
    portfolio_id: str,
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取投资组合历史快照

    Args:
        portfolio_id: 投资组合ID
        limit: 返回数量限制（默认30天）
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

    # 查询快照
    result = await db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.portfolio_id == portfolio_id)
        .order_by(PortfolioSnapshot.snapshot_time.desc())
        .limit(limit)
    )
    snapshots = result.scalars().all()

    return [PortfolioSnapshotResponse.from_orm(s) for s in snapshots]


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除投资组合（软删除，设置为不活跃）
    """
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

    # 软删除
    portfolio.is_active = False
    await db.commit()

    return None
