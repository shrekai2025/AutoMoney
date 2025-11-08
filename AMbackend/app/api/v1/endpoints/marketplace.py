"""Strategy Marketplace API Endpoints"""

import logging
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.strategy import (
    StrategyMarketplaceListResponse,
    StrategyDetailResponse,
    StrategyExecutionDetail,
    AgentWeights,
    TradeListResponse,
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
        # 如果没有指定user_id，显示所有用户的策略（策略市场是公开的）
        # 只有明确指定user_id时才进行过滤
        filter_user_id = user_id  # None表示显示所有

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
    部署资金到策略（激活策略）

    - **portfolio_id**: Portfolio UUID
    - **amount**: 部署金额（必须 > 0）

    注意：当前为模拟盘功能，未来将实现真实资金划转
    """
    try:
        result = await marketplace_service.deploy_strategy(
            db=db,
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            initial_balance=amount,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    request: Request,
    rebalance_period_minutes: Optional[int] = Query(None, ge=1, le=1440, description="Rebalance period in minutes (1-1440)"),
    consecutive_signal_threshold: Optional[int] = Query(None, ge=1, le=1000, description="Consecutive signal threshold"),
    acceleration_multiplier_min: Optional[float] = Query(None, ge=1.0, le=5.0, description="Acceleration multiplier min"),
    acceleration_multiplier_max: Optional[float] = Query(None, ge=1.0, le=5.0, description="Acceleration multiplier max"),
    fg_circuit_breaker_threshold: Optional[int] = Query(None, ge=0, le=100, description="Fear & Greed circuit breaker threshold (0-100)"),
    fg_position_adjust_threshold: Optional[int] = Query(None, ge=0, le=100, description="Fear & Greed position adjust threshold (0-100)"),
    buy_threshold: Optional[float] = Query(None, ge=0, le=100, description="Buy threshold for conviction score (0-100)"),
    partial_sell_threshold: Optional[float] = Query(None, ge=0, le=100, description="Partial sell threshold for conviction score (0-100)"),
    full_sell_threshold: Optional[float] = Query(None, ge=0, le=100, description="Full sell threshold for conviction score (0-100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新策略参数设置

    - **portfolio_id**: Portfolio UUID
    - **rebalance_period_minutes**: 策略执行周期（分钟），范围 1-1440 (可选)
    - **agent_weights**: Agent权重配置 (可选)，格式: {"agent_weights": {"macro": 0.4, "onchain": 0.4, "ta": 0.2}}
    - **consecutive_signal_threshold**: 连续信号阈值，范围 1-1000 (可选)
    - **acceleration_multiplier_min**: 加速乘数最小值，范围 1.0-5.0 (可选)
    - **acceleration_multiplier_max**: 加速乘数最大值，范围 1.0-5.0 (可选)
    - **fg_circuit_breaker_threshold**: Fear & Greed熔断阈值，范围 0-100 (可选)
    - **fg_position_adjust_threshold**: Fear & Greed仓位调整阈值，范围 0-100 (可选)
    - **buy_threshold**: 买入阈值（Conviction Score），范围 0-100 (可选)
    - **partial_sell_threshold**: 部分减仓阈值（Conviction Score），范围 0-100 (可选)
    - **full_sell_threshold**: 全部清仓阈值（Conviction Score），范围 0-100 (可选)
    """
    try:
        # 手动解析请求体
        agent_weights = None
        try:
            body = await request.json()
            if body and "agent_weights" in body:
                agent_weights = body["agent_weights"]
        except Exception:
            # 如果没有body或解析失败，agent_weights保持None
            pass

        # 验证agent_weights格式（如果提供）
        if agent_weights is not None:
            try:
                AgentWeights(**agent_weights)  # 使用Pydantic模型验证
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid agent_weights: {str(e)}")

        # 验证乘数范围
        if acceleration_multiplier_min is not None and acceleration_multiplier_max is not None:
            if acceleration_multiplier_min > acceleration_multiplier_max:
                raise HTTPException(status_code=400, detail="acceleration_multiplier_min must be <= acceleration_multiplier_max")

        result = await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            rebalance_period_minutes=rebalance_period_minutes,
            agent_weights=agent_weights,
            consecutive_signal_threshold=consecutive_signal_threshold,
            acceleration_multiplier_min=acceleration_multiplier_min,
            acceleration_multiplier_max=acceleration_multiplier_max,
            fg_circuit_breaker_threshold=fg_circuit_breaker_threshold,
            fg_position_adjust_threshold=fg_position_adjust_threshold,
            buy_threshold=buy_threshold,
            partial_sell_threshold=partial_sell_threshold,
            full_sell_threshold=full_sell_threshold,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新策略设置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update strategy settings: {str(e)}")


@router.get("/{portfolio_id}/executions")
async def get_strategy_executions(
    portfolio_id: str,
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(50, ge=1, le=100, description="Page size (1-100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取策略执行历史列表（分页）

    - **portfolio_id**: Portfolio UUID
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（1-100）
    """
    try:
        result = await marketplace_service.get_strategy_executions(
            db=db,
            portfolio_id=portfolio_id,
            page=page,
            page_size=page_size,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取策略执行历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get strategy executions: {str(e)}")


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


@router.get("/{portfolio_id}/trades", response_model=TradeListResponse)
async def get_portfolio_trades(
    portfolio_id: str,
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (1-100)"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取投资组合的交易记录（分页）- 公开接口，无需认证

    - **portfolio_id**: Portfolio UUID
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（1-100）
    """
    try:
        result = await marketplace_service.get_portfolio_trades(
            db=db,
            portfolio_id=portfolio_id,
            page=page,
            page_size=page_size,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get trades: {str(e)}")
