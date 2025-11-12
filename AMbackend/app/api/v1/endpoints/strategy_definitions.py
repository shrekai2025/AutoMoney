"""Strategy Definitions API Endpoints - 策略模板管理（仅Admin）

提供策略模板的CRUD操作
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_admin_user
from app.models.user import User
from app.services.strategy.definition_service import definition_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic模型
class StrategyDefinitionResponse(BaseModel):
    """策略模板响应"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    decision_agent_module: str
    decision_agent_class: str
    business_agents: List[str]
    trade_channel: str
    trade_symbol: str
    rebalance_period_minutes: int
    default_params: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class StrategyDefinitionListResponse(BaseModel):
    """策略模板列表响应"""
    definitions: List[StrategyDefinitionResponse]
    total: int


class StrategyDefinitionUpdateRequest(BaseModel):
    """策略模板更新请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    default_params: Optional[Dict[str, Any]] = None
    rebalance_period_minutes: Optional[int] = Field(None, ge=1, le=1440)
    is_active: Optional[bool] = None


@router.get("/", response_model=StrategyDefinitionListResponse)
async def get_all_strategy_definitions(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取所有策略模板（仅Admin）
    
    - **include_inactive**: 是否包含未激活的模板
    """
    try:
        definitions = await definition_service.get_all_definitions(
            db=db,
            include_inactive=include_inactive
        )
        
        return StrategyDefinitionListResponse(
            definitions=[
                StrategyDefinitionResponse(
                    **{
                        **definition.__dict__,
                        "created_at": definition.created_at.isoformat(),
                        "updated_at": definition.updated_at.isoformat(),
                    }
                )
                for definition in definitions
            ],
            total=len(definitions)
        )
        
    except Exception as e:
        logger.error(f"获取策略模板列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get strategy definitions: {str(e)}")


@router.get("/{definition_id}", response_model=StrategyDefinitionResponse)
async def get_strategy_definition(
    definition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取单个策略模板详情（仅Admin）
    
    - **definition_id**: 策略模板ID
    """
    try:
        definition = await definition_service.get_definition_by_id(db, definition_id)
        
        if not definition:
            raise HTTPException(status_code=404, detail=f"Strategy definition {definition_id} not found")
        
        return StrategyDefinitionResponse(
            **{
                **definition.__dict__,
                "created_at": definition.created_at.isoformat(),
                "updated_at": definition.updated_at.isoformat(),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get strategy definition: {str(e)}")


@router.patch("/{definition_id}", response_model=StrategyDefinitionResponse)
async def update_strategy_definition(
    definition_id: int,
    update_request: StrategyDefinitionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    更新策略模板配置（仅Admin）
    
    - **definition_id**: 策略模板ID
    - **update_request**: 更新数据（只更新提供的字段）
    
    可更新字段：
    - display_name: 显示名称
    - description: 描述
    - default_params: 默认参数配置
    - rebalance_period_minutes: 执行周期（1-1440分钟）
    - is_active: 模板开关
    """
    try:
        # 过滤None值
        update_data = {k: v for k, v in update_request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        definition = await definition_service.update_definition(
            db=db,
            definition_id=definition_id,
            update_data=update_data
        )
        
        return StrategyDefinitionResponse(
            **{
                **definition.__dict__,
                "created_at": definition.created_at.isoformat(),
                "updated_at": definition.updated_at.isoformat(),
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新策略模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update strategy definition: {str(e)}")

