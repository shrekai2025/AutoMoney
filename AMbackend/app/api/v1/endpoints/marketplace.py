"""Strategy Marketplace API Endpoints"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.strategy import (
    StrategyMarketplaceListResponse,
    StrategyDetailResponse,
    StrategyExecutionDetail,
)
from app.services.strategy.marketplace_service import marketplace_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=StrategyMarketplaceListResponse)
async def get_marketplace_strategies(
    risk_level: Optional[str] = Query(None, description="Risk level filter: low, medium, medium-high, high"),
    sort_by: str = Query("return", description="Sort by: return, risk, tvl, sharpe"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (optional)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取策略市场列表

    - **risk_level**: 可选，筛选风险等级 (low, medium, medium-high, high)
    - **sort_by**: 排序方式，默认return (return, risk, tvl, sharpe)
    - **user_id**: 可选，只显示指定用户的策略（默认显示所有）
    """
    try:
        # 如果没有指定user_id，则使用当前用户的ID
        filter_user_id = user_id if user_id else current_user.id

        result = await marketplace_service.get_marketplace_list(
            db=db,
            user_id=filter_user_id,
            risk_level=risk_level,
            sort_by=sort_by,
        )
        return result
    except Exception as e:
        logger.error(f"获取策略市场列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get marketplace strategies: {str(e)}")


@router.get("/{portfolio_id}", response_model=StrategyDetailResponse)
async def get_strategy_detail(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取策略详情

    - **portfolio_id**: Portfolio UUID
    """
    try:
        result = await marketplace_service.get_strategy_detail(
            db=db,
            portfolio_id=portfolio_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取策略详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get strategy detail: {str(e)}")


@router.post("/{portfolio_id}/deploy")
async def deploy_funds(
    portfolio_id: str,
    amount: float = Query(..., description="Amount to deploy", gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    部署资金到策略

    - **portfolio_id**: Portfolio UUID
    - **amount**: 部署金额（必须 > 0）

    注意：此功能将在未来版本中实现完整的资金管理逻辑
    """
    try:
        # TODO: 实现资金部署逻辑
        # 1. 验证用户余额
        # 2. 扣除用户账户资金
        # 3. 增加Portfolio余额
        # 4. 记录交易

        return {
            "success": True,
            "message": f"Successfully deployed ${amount} to strategy {portfolio_id}",
            "portfolio_id": portfolio_id,
            "amount": amount,
        }
    except Exception as e:
        logger.error(f"部署资金失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to deploy funds: {str(e)}")


@router.post("/{portfolio_id}/withdraw")
async def withdraw_funds(
    portfolio_id: str,
    amount: float = Query(..., description="Amount to withdraw", gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    从策略提现资金

    - **portfolio_id**: Portfolio UUID
    - **amount**: 提现金额（必须 > 0）

    注意：此功能将在未来版本中实现完整的资金管理逻辑
    """
    try:
        # TODO: 实现资金提现逻辑
        # 1. 验证Portfolio余额
        # 2. 扣除Portfolio余额
        # 3. 增加用户账户资金
        # 4. 记录交易

        return {
            "success": True,
            "message": f"Successfully withdrew ${amount} from strategy {portfolio_id}",
            "portfolio_id": portfolio_id,
            "amount": amount,
        }
    except Exception as e:
        logger.error(f"提现资金失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to withdraw funds: {str(e)}")


@router.patch("/{portfolio_id}/settings")
async def update_strategy_settings(
    portfolio_id: str,
    rebalance_period_minutes: int = Query(..., ge=1, le=1440, description="Rebalance period in minutes (1-1440)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新策略参数设置

    - **portfolio_id**: Portfolio UUID
    - **rebalance_period_minutes**: 策略执行周期（分钟），范围 1-1440
    """
    try:
        result = await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            rebalance_period_minutes=rebalance_period_minutes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新策略设置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update strategy settings: {str(e)}")


@router.get("/executions/{execution_id}", response_model=StrategyExecutionDetail)
async def get_execution_detail(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取策略执行详情，包括所有agent调用过程和LLM对话

    - **execution_id**: Strategy Execution UUID
    """
    try:
        result = await marketplace_service.get_execution_detail(
            db=db,
            execution_id=execution_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取策略执行详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get execution detail: {str(e)}")
