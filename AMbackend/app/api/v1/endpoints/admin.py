"""Admin API Endpoints"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from apscheduler.triggers.interval import IntervalTrigger

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
        # 查询所有策略（eager load strategy_definition）
        from sqlalchemy.orm import selectinload
        from app.models.strategy_definition import StrategyDefinition

        result = await db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.strategy_definition))
            .order_by(Portfolio.created_at.desc())
        )
        portfolios = result.scalars().all()

        # 转换为响应格式
        strategies = [
            AdminStrategyItem(
                id=str(portfolio.id),
                user_id=portfolio.user_id,
                name=portfolio.name,
                strategy_name=portfolio.instance_name or "Unknown",
                is_active=portfolio.is_active,
                total_value=float(portfolio.total_value),
                total_pnl=float(portfolio.total_pnl),
                total_pnl_percent=portfolio.total_pnl_percent,
                # 从策略模板读取执行周期
                rebalance_period_minutes=portfolio.strategy_definition.default_params.get("rebalance_period_minutes", 10) if portfolio.strategy_definition and portfolio.strategy_definition.default_params else 10,
                agent_weights=portfolio.instance_params.get("agent_weights", {}) if portfolio.instance_params else {},
                consecutive_signal_threshold=portfolio.instance_params.get("consecutive_signal_threshold", 30) if portfolio.instance_params else 30,
                acceleration_multiplier_min=portfolio.instance_params.get("acceleration_multiplier_min", 1.1) if portfolio.instance_params else 1.1,
                acceleration_multiplier_max=portfolio.instance_params.get("acceleration_multiplier_max", 2.0) if portfolio.instance_params else 2.0,
                fg_circuit_breaker_threshold=portfolio.instance_params.get("fg_circuit_breaker_threshold", 20) if portfolio.instance_params else 20,
                fg_position_adjust_threshold=portfolio.instance_params.get("fg_position_adjust_threshold", 30) if portfolio.instance_params else 30,
                buy_threshold=portfolio.instance_params.get("buy_threshold", 50) if portfolio.instance_params else 50,
                partial_sell_threshold=portfolio.instance_params.get("partial_sell_threshold", 50) if portfolio.instance_params else 50,
                full_sell_threshold=portfolio.instance_params.get("full_sell_threshold", 45) if portfolio.instance_params else 45,
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
                portfolio_name=portfolio.instance_name or portfolio.name or "Unknown",
                period_minutes=portfolio.instance_params.get("rebalance_period_minutes", 10) if portfolio.instance_params else 10,
            )
            logger.info(f"已为激活的策略添加定时任务: {portfolio.instance_name or portfolio.name}")

        elif not request.is_active and old_status:
            # 停用: 移除定时任务
            strategy_scheduler.remove_portfolio_job(str(portfolio.id))
            logger.info(f"已移除停用策略的定时任务: {portfolio.instance_name or portfolio.name}")

        return StrategyToggleResponse(
            success=True,
            portfolio_id=str(portfolio.id),
            is_active=portfolio.is_active,
            message=f"Strategy {portfolio.instance_name or portfolio.name} is now {'active' if portfolio.is_active else 'inactive'}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换策略状态失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle strategy: {str(e)}")


@router.patch("/strategies/{portfolio_id}/params")
async def update_strategy_params(
    portfolio_id: str,
    agent_weights: Optional[str] = None,  # 改为字符串，手动解析JSON
    consecutive_signal_threshold: Optional[int] = None,
    acceleration_multiplier_min: Optional[float] = None,
    acceleration_multiplier_max: Optional[float] = None,
    fg_circuit_breaker_threshold: Optional[int] = None,
    fg_position_adjust_threshold: Optional[int] = None,
    buy_threshold: Optional[float] = None,
    partial_sell_threshold: Optional[float] = None,
    full_sell_threshold: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    更新策略实例参数（仅Admin）

    支持的参数:
    - agent_weights: Agent权重配置
    - consecutive_signal_threshold: 连续信号阈值
    - acceleration_multiplier_min/max: 加速乘数范围
    - fg_circuit_breaker_threshold: 市场恐慌熔断阈值
    - fg_position_adjust_threshold: 仓位调整阈值
    - buy_threshold: 买入信念分数阈值
    - partial_sell_threshold: 部分卖出阈值
    - full_sell_threshold: 全部卖出阈值

    注意: rebalance_period_minutes 已移至策略模板级别，不再支持实例级别配置
    """
    try:
        logger.info(f"[ADMIN] 更新策略实例参数 - portfolio_id={portfolio_id}")

        # 查询策略
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Strategy {portfolio_id} not found")

        # 获取当前参数
        params = portfolio.instance_params or {}

        # 更新所有提供的参数
        if agent_weights is not None:
            # 如果是JSON字符串，解析它
            import json
            try:
                weights_dict = json.loads(agent_weights) if isinstance(agent_weights, str) else agent_weights
                params['agent_weights'] = weights_dict
                logger.info(f"[ADMIN] 更新权重: {weights_dict}")
            except json.JSONDecodeError as e:
                logger.error(f"[ADMIN] agent_weights JSON解析失败: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid agent_weights JSON: {str(e)}")

        if consecutive_signal_threshold is not None:
            params['consecutive_signal_threshold'] = consecutive_signal_threshold
            logger.info(f"[ADMIN] 更新连续信号阈值: {consecutive_signal_threshold}")

        if acceleration_multiplier_min is not None:
            params['acceleration_multiplier_min'] = acceleration_multiplier_min
            logger.info(f"[ADMIN] 更新加速乘数最小值: {acceleration_multiplier_min}")

        if acceleration_multiplier_max is not None:
            params['acceleration_multiplier_max'] = acceleration_multiplier_max
            logger.info(f"[ADMIN] 更新加速乘数最大值: {acceleration_multiplier_max}")

        if fg_circuit_breaker_threshold is not None:
            params['fg_circuit_breaker_threshold'] = fg_circuit_breaker_threshold
            logger.info(f"[ADMIN] 更新熔断阈值: {fg_circuit_breaker_threshold}")

        if fg_position_adjust_threshold is not None:
            params['fg_position_adjust_threshold'] = fg_position_adjust_threshold
            logger.info(f"[ADMIN] 更新仓位调整阈值: {fg_position_adjust_threshold}")

        if buy_threshold is not None:
            params['buy_threshold'] = buy_threshold
            logger.info(f"[ADMIN] 更新买入阈值: {buy_threshold}")

        if partial_sell_threshold is not None:
            params['partial_sell_threshold'] = partial_sell_threshold
            logger.info(f"[ADMIN] 更新部分卖出阈值: {partial_sell_threshold}")

        if full_sell_threshold is not None:
            params['full_sell_threshold'] = full_sell_threshold
            logger.info(f"[ADMIN] 更新全部卖出阈值: {full_sell_threshold}")

        # 直接赋值并标记为已修改（强制SQLAlchemy追踪JSONB变化）
        from sqlalchemy.orm.attributes import flag_modified
        portfolio.instance_params = params
        flag_modified(portfolio, 'instance_params')
        portfolio.updated_at = datetime.utcnow()

        # 提交
        await db.commit()
        await db.refresh(portfolio)

        # 验证保存
        logger.info(f"[ADMIN] 实例参数更新成功")
        logger.info(f"[ADMIN] 提交后的参数: {portfolio.instance_params}")

        return {
            "success": True,
            "portfolio_id": str(portfolio.id),
            "updated_params": params,
            "message": "Instance parameters updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] 更新实例参数失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update instance parameters: {str(e)}")


# ============ 策略模板管理 ============

class StrategyTemplateItem(BaseModel):
    """策略模板项"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    rebalance_period_minutes: int
    business_agents: List[str]
    instance_count: int
    is_active: bool


class StrategyTemplateListResponse(BaseModel):
    """策略模板列表响应"""
    total: int
    templates: List[StrategyTemplateItem]


@router.get("/strategy-templates", response_model=StrategyTemplateListResponse)
async def get_strategy_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取所有策略模板（仅Admin）
    """
    try:
        from app.models.strategy_definition import StrategyDefinition
        from sqlalchemy import func

        # 查询所有策略模板，并统计实例数量
        result = await db.execute(
            select(
                StrategyDefinition,
                func.count(Portfolio.id).label('instance_count')
            )
            .outerjoin(Portfolio, Portfolio.strategy_definition_id == StrategyDefinition.id)
            .group_by(StrategyDefinition.id)
            .order_by(StrategyDefinition.id)
        )
        rows = result.all()

        templates = [
            StrategyTemplateItem(
                id=row.StrategyDefinition.id,
                name=row.StrategyDefinition.name,
                display_name=row.StrategyDefinition.display_name,
                description=row.StrategyDefinition.description,
                rebalance_period_minutes=row.StrategyDefinition.default_params.get("rebalance_period_minutes", 10) if row.StrategyDefinition.default_params else 10,
                business_agents=row.StrategyDefinition.business_agents or [],
                instance_count=row.instance_count,
                is_active=row.StrategyDefinition.is_active,
            )
            for row in rows
        ]

        return StrategyTemplateListResponse(
            total=len(templates),
            templates=templates,
        )

    except Exception as e:
        logger.error(f"获取策略模板列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get strategy templates: {str(e)}")


@router.patch("/strategy-templates/{template_id}/params")
async def update_strategy_template_params(
    template_id: int,
    rebalance_period_minutes: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    更新策略模板参数（仅Admin）

    修改后会自动更新调度器中的定时任务周期
    """
    try:
        from app.models.strategy_definition import StrategyDefinition
        from app.services.strategy.scheduler import strategy_scheduler
        from sqlalchemy.orm.attributes import flag_modified

        logger.info(f"[ADMIN] 更新策略模板参数 - template_id={template_id}, period={rebalance_period_minutes}")

        # 查询策略模板
        result = await db.execute(
            select(StrategyDefinition).where(StrategyDefinition.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail=f"Strategy template {template_id} not found")

        # 获取当前参数
        params = template.default_params or {}
        old_period = params.get('rebalance_period_minutes', 10)

        # 更新参数
        if rebalance_period_minutes is not None:
            if rebalance_period_minutes < 1 or rebalance_period_minutes > 1440:
                raise HTTPException(status_code=400, detail="rebalance_period_minutes must be between 1 and 1440")

            params['rebalance_period_minutes'] = rebalance_period_minutes
            logger.info(f"[ADMIN] 更新模板周期: {old_period} -> {rebalance_period_minutes}")

        # 更新字段并标记为已修改（强制SQLAlchemy追踪JSONB变化）
        template.default_params = params
        flag_modified(template, 'default_params')

        # 🔥 同时更新数据库字段（保持一致性）
        if rebalance_period_minutes is not None:
            template.rebalance_period_minutes = rebalance_period_minutes

        template.updated_at = datetime.utcnow()

        # 提交
        await db.commit()
        await db.refresh(template)

        # 验证保存
        logger.info(f"[ADMIN] 提交后的值: {template.default_params.get('rebalance_period_minutes')}")

        # 🔥 立即重新加载调度器配置（动态生效，无需重启）
        if rebalance_period_minutes is not None and rebalance_period_minutes != old_period:
            try:
                await strategy_scheduler.reload_template_schedule(template_id)
                logger.info(f"[ADMIN] ✓ 调度器已重新加载，新周期: {rebalance_period_minutes}分钟")
            except Exception as e:
                logger.error(f"[ADMIN] ✗ 调度器重载失败: {e}", exc_info=True)
                # 注意：即使重载失败，配置也已保存到数据库

        logger.info(f"[ADMIN] 模板参数更新成功")

        return {
            "success": True,
            "template_id": template.id,
            "rebalance_period_minutes": params.get('rebalance_period_minutes'),
            "message": "Template parameters updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] 更新模板参数失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update template parameters: {str(e)}")


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
