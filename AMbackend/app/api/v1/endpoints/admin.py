"""Admin API Endpoints"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

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
from app.services.agents.agent_manager import agent_manager
from app.services.tools.tool_manager import tool_manager
from app.services.apis.api_manager import api_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# 响应模型
class AgentRegistryResponse(BaseModel):
    """Agent注册表响应"""
    id: int
    agent_name: str
    display_name: str
    description: Optional[str]
    agent_module: str
    agent_class: str
    available_tools: List[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class ToolRegistryResponse(BaseModel):
    """Tool注册表响应"""
    id: int
    tool_name: str
    display_name: str
    description: Optional[str]
    tool_module: str
    tool_function: str
    required_apis: List[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class APIConfigResponse(BaseModel):
    """API配置响应"""
    id: int
    api_name: str
    display_name: str
    description: Optional[str]
    base_url: Optional[str]
    api_key_masked: str  # 掩码后的密钥
    rate_limit: Optional[int]
    is_active: bool
    
    class Config:
        from_attributes = True


class APIConfigUpdateRequest(BaseModel):
    """API配置更新请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    api_key_encrypted: Optional[str] = None
    api_secret_encrypted: Optional[str] = None
    rate_limit: Optional[int] = None
    is_active: Optional[bool] = None


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


# ============ 基础模块配置管理 ============

@router.get("/agents", response_model=List[AgentRegistryResponse])
async def get_all_agents(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取所有注册的业务Agent（仅Admin）
    
    用于展示Agent注册表
    """
    try:
        agents = await agent_manager.list_all_agents(db, active_only=active_only)
        return [AgentRegistryResponse.from_orm(agent) for agent in agents]
    except Exception as e:
        logger.error(f"获取Agent注册表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")


@router.get("/tools", response_model=List[ToolRegistryResponse])
async def get_all_tools(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取所有注册的Tools（仅Admin）
    
    用于展示Tool注册表
    """
    try:
        tools = await tool_manager.list_all_tools(db, active_only=active_only)
        return [ToolRegistryResponse.from_orm(tool) for tool in tools]
    except Exception as e:
        logger.error(f"获取Tool注册表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")


@router.get("/apis", response_model=List[APIConfigResponse])
async def get_all_apis(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取所有API配置（仅Admin）
    
    用于展示API配置表，密钥会被掩码
    """
    try:
        apis = await api_manager.list_all_apis(db, active_only=active_only)
        
        return [
            APIConfigResponse(
                id=api.id,
                api_name=api.api_name,
                display_name=api.display_name,
                description=api.description,
                base_url=api.base_url,
                api_key_masked=api_manager.mask_api_key(api.api_key_encrypted),
                rate_limit=api.rate_limit,
                is_active=api.is_active,
            )
            for api in apis
        ]
    except Exception as e:
        logger.error(f"获取API配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get API configs: {str(e)}")


@router.patch("/apis/{api_name}", response_model=APIConfigResponse)
async def update_api_config(
    api_name: str,
    update_request: APIConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    更新API配置（仅Admin）
    
    - **api_name**: API名称
    - **update_request**: 更新数据（只更新提供的字段）
    
    可更新字段：
    - display_name: 显示名称
    - description: 描述
    - base_url: API基础URL
    - api_key_encrypted: API密钥（加密存储）
    - api_secret_encrypted: API密钥Secret（加密存储）
    - rate_limit: 速率限制
    - is_active: API状态
    """
    try:
        # 过滤None值
        update_data = {k: v for k, v in update_request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        api_config = await api_manager.update_api_config(
            db=db,
            api_name=api_name,
            update_data=update_data
        )
        
        return APIConfigResponse(
            id=api_config.id,
            api_name=api_config.api_name,
            display_name=api_config.display_name,
            description=api_config.description,
            base_url=api_config.base_url,
            api_key_masked=api_manager.mask_api_key(api_config.api_key_encrypted),
            rate_limit=api_config.rate_limit,
            is_active=api_config.is_active,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新API配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update API config: {str(e)}")
