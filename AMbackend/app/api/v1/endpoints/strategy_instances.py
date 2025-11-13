"""Strategy Instances API Endpoints - 策略实例管理

提供策略实例的CRUD操作，支持按角色权限控制
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user, get_current_trader_or_admin
from app.models.user import User
from app.services.strategy.definition_service import definition_service
from app.services.strategy.instance_service import instance_service
from app.services.strategy.marketplace_service import marketplace_service  # 复用详情查询

logger = logging.getLogger(__name__)

router = APIRouter(redirect_slashes=False)


# ========== Request/Response Models ==========

class CreateInstanceRequest(BaseModel):
    """创建策略实例请求"""
    strategy_definition_id: int = Field(..., description="策略模板ID")
    instance_name: Optional[str] = Field(None, description="实例名称（可选，不提供则自动生成）")
    instance_description: Optional[str] = Field(None, description="实例描述（可选）")
    initial_balance: float = Field(..., gt=0, description="初始资金（必须>0）")
    instance_params: Optional[Dict[str, Any]] = Field(None, description="实例参数（可选，不提供则使用模板默认值）")
    tags: Optional[List[str]] = Field(None, description="策略标签（可选）")
    risk_level: Optional[str] = Field("medium", description="风险程度：low, medium, high")


class UpdateInstanceRequest(BaseModel):
    """更新策略实例请求"""
    instance_name: Optional[str] = None
    instance_description: Optional[str] = None
    instance_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class InstanceListItemResponse(BaseModel):
    """实例列表项响应"""
    id: str
    instance_name: str
    instance_description: Optional[str]
    strategy_definition_id: int
    strategy_display_name: str  # 从模板获取
    user_id: int
    user_name: str
    is_active: bool
    total_value: float
    total_pnl: float
    total_pnl_percent: float
    created_at: str
    
    class Config:
        from_attributes = True


class InstanceListResponse(BaseModel):
    """实例列表响应"""
    instances: List[InstanceListItemResponse]
    total: int


class CreateInstanceResponse(BaseModel):
    """创建实例响应"""
    success: bool
    portfolio_id: str
    instance_name: str
    strategy_definition_id: int
    initial_balance: float
    created_at: str


# ========== API Endpoints ==========

@router.get("/")
async def get_strategy_instances(
    risk_level: Optional[str] = Query(None, description="Risk level filter: low, medium, medium-high, high"),
    sort_by: str = Query("return", description="Sort by: return, risk, tvl, sharpe"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (optional)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取策略市场列表（兼容旧接口）

    返回 marketplace 格式的数据，与前端期望的格式一致

    参数：
    - **risk_level**: 可选，筛选风险等级 (low, medium, medium-high, high)
    - **sort_by**: 排序方式，默认return (return, risk, tvl, sharpe)
    - **user_id**: 可选，只显示指定用户的策略（默认显示所有）
    """
    try:
        # 如果没有指定user_id，显示所有用户的策略（策略市场是公开的）
        filter_user_id = user_id  # None表示显示所有

        result = await marketplace_service.get_marketplace_list(
            db=db,
            user_id=filter_user_id,
            risk_level=risk_level,
            sort_by=sort_by,
            current_user_id=current_user.id,
        )
        return result
    except Exception as e:
        logger.error(f"获取策略市场列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get marketplace strategies: {str(e)}")


@router.post("/", response_model=CreateInstanceResponse)
async def create_strategy_instance(
    create_request: CreateInstanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trader_or_admin),
):
    """
    创建策略实例（仅交易员/Admin）
    
    从策略模板创建一个新的可运行实例
    
    参数：
    - **strategy_definition_id**: 策略模板ID
    - **instance_name**: 实例名称（可选，不提供则自动生成）
    - **instance_description**: 实例描述（可选）
    - **initial_balance**: 初始资金
    - **instance_params**: 实例参数（可选，不提供则使用模板默认值）
    """
    try:
        portfolio = await definition_service.create_instance_from_definition(
            db=db,
            definition_id=create_request.strategy_definition_id,
            user_id=current_user.id,
            initial_balance=create_request.initial_balance,
            instance_name=create_request.instance_name,
            instance_description=create_request.instance_description,
            instance_params=create_request.instance_params,
            tags=create_request.tags,
            risk_level=create_request.risk_level,
        )
        
        logger.info(
            f"用户 {current_user.email} 创建策略实例: {portfolio.instance_name} "
            f"(ID: {portfolio.id}, 资金: {create_request.initial_balance})"
        )
        
        return CreateInstanceResponse(
            success=True,
            portfolio_id=str(portfolio.id),
            instance_name=portfolio.instance_name,
            strategy_definition_id=portfolio.strategy_definition_id,
            initial_balance=create_request.initial_balance,
            created_at=portfolio.created_at.isoformat(),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建策略实例失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create instance: {str(e)}")


@router.get("/{portfolio_id}")
async def get_strategy_instance_detail(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取策略实例详情
    
    复用原有的marketplace_service.get_strategy_detail()方法
    """
    try:
        # 复用现有的详情查询逻辑
        result = await marketplace_service.get_strategy_detail(
            db=db,
            portfolio_id=portfolio_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取策略实例详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get instance detail: {str(e)}")


@router.patch("/{portfolio_id}")
async def update_strategy_instance(
    portfolio_id: str,
    update_request: UpdateInstanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trader_or_admin),
):
    """
    更新策略实例（仅交易员/Admin）
    
    可更新：
    - instance_name: 实例名称
    - instance_description: 实例描述
    - instance_params: 实例参数
    - is_active: 实例开关
    """
    try:
        # 权限检查：只能修改自己的实例，除非是Admin
        instance = await instance_service.get_instance_by_id(db, portfolio_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance {portfolio_id} not found")
        
        if current_user.role != "admin" and instance.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Can only update your own instances")
        
        # 过滤None值
        update_data = {k: v for k, v in update_request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        updated_instance = await instance_service.update_instance(
            db=db,
            portfolio_id=portfolio_id,
            update_data=update_data
        )
        
        return {
            "success": True,
            "portfolio_id": str(updated_instance.id),
            "instance_name": updated_instance.instance_name,
            "message": "Instance updated successfully"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新策略实例失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update instance: {str(e)}")


@router.delete("/{portfolio_id}")
async def delete_strategy_instance(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trader_or_admin),
):
    """
    删除策略实例（仅交易员/Admin）
    
    停用并删除策略实例及其所有关联数据
    """
    try:
        # 权限检查
        instance = await instance_service.get_instance_by_id(db, portfolio_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance {portfolio_id} not found")
        
        if current_user.role != "admin" and instance.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Can only delete your own instances")
        
        await instance_service.delete_instance(db, portfolio_id)
        
        return {
            "success": True,
            "portfolio_id": portfolio_id,
            "message": "Instance deleted successfully"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除策略实例失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete instance: {str(e)}")


# ========== 复用原有功能的端点 ==========

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
    更新策略参数设置（复用原有逻辑）

    可更新参数：
    - rebalance_period_minutes: 策略执行周期
    - agent_weights: Agent权重配置（通过request body传递）
    - consecutive_signal_threshold: 连续信号阈值
    - acceleration_multiplier_min/max: 加速乘数范围
    - fg_circuit_breaker_threshold: Fear & Greed熔断阈值
    - fg_position_adjust_threshold: Fear & Greed仓位调整阈值
    - buy_threshold: 买入阈值
    - partial_sell_threshold: 部分减仓阈值
    - full_sell_threshold: 全部清仓阈值
    """
    try:
        from fastapi import Request
        from app.schemas.strategy import AgentWeights

        logger.info(f"[API] 收到更新策略设置请求 - portfolio_id={portfolio_id}, rebalance_period={rebalance_period_minutes}")

        # 手动解析请求体获取agent_weights
        agent_weights = None
        try:
            body = await request.json()
            logger.info(f"[API] 请求体: {body}")
            if body and "agent_weights" in body:
                agent_weights = body["agent_weights"]
                logger.info(f"[API] Agent权重: {agent_weights}")
        except Exception as e:
            logger.warning(f"[API] 解析请求体失败: {e}")

        # 验证agent_weights格式
        if agent_weights is not None:
            try:
                AgentWeights(**agent_weights)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid agent_weights: {str(e)}")

        # 验证乘数范围
        if acceleration_multiplier_min is not None and acceleration_multiplier_max is not None:
            if acceleration_multiplier_min > acceleration_multiplier_max:
                raise HTTPException(status_code=400, detail="acceleration_multiplier_min must be <= acceleration_multiplier_max")

        # 检查用户是否是管理员
        is_admin = current_user.role == "admin"

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
            is_admin=is_admin,
        )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新策略设置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update strategy settings: {str(e)}")


@router.get("/{portfolio_id}/executions")
async def get_strategy_executions(
    portfolio_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取策略执行历史（复用原有逻辑）"""
    try:
        result = await marketplace_service.get_strategy_executions(
            db=db,
            portfolio_id=portfolio_id,
            page=page,
            page_size=page_size,
        )
        return result
    except Exception as e:
        logger.error(f"获取执行历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}")
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


@router.get("/{portfolio_id}/trades")
async def get_portfolio_trades(
    portfolio_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取交易记录（复用原有逻辑）"""
    try:
        result = await marketplace_service.get_portfolio_trades(
            db=db,
            portfolio_id=portfolio_id,
            page=page,
            page_size=page_size,
        )
        return result
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))





