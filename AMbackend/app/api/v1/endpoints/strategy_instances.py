"""Strategy Instances API Endpoints - 策略实例管理

提供策略实例的CRUD操作，支持按角色权限控制
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user, get_current_trader_or_admin
from app.models.user import User
from app.services.strategy.definition_service import definition_service
from app.services.strategy.instance_service import instance_service
from app.services.strategy.marketplace_service import marketplace_service  # 复用详情查询

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== Request/Response Models ==========

class CreateInstanceRequest(BaseModel):
    """创建策略实例请求"""
    strategy_definition_id: int = Field(..., description="策略模板ID")
    instance_name: Optional[str] = Field(None, description="实例名称（可选，不提供则自动生成）")
    instance_description: Optional[str] = Field(None, description="实例描述（可选）")
    initial_balance: float = Field(..., gt=0, description="初始资金（必须>0）")
    instance_params: Optional[Dict[str, Any]] = Field(None, description="实例参数（可选，不提供则使用模板默认值）")


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

@router.get("/", response_model=InstanceListResponse)
async def get_strategy_instances(
    definition_id: Optional[int] = Query(None, description="按策略模板筛选"),
    user_id: Optional[int] = Query(None, description="按用户筛选（仅Admin）"),
    active_only: bool = Query(False, description="是否只显示活跃实例"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取策略实例列表
    
    权限控制：
    - 普通用户：只能看到is_active=true的实例
    - 交易员/Admin：可以看到所有实例
    
    参数：
    - **definition_id**: 按策略模板筛选（可选）
    - **user_id**: 按用户筛选（仅Admin可用）
    - **active_only**: 是否只显示活跃实例
    """
    try:
        # Admin可以查看所有用户的实例，其他角色只能看自己的
        if current_user.role != "admin" and user_id and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot view other users' strategies")
        
        instances = await instance_service.get_all_instances(
            db=db,
            user_role=current_user.role,
            user_id=user_id,
            definition_id=definition_id,
            active_only=active_only
        )
        
        # 构建响应
        instance_list = []
        for instance in instances:
            strategy_name = "Unknown Strategy"
            if instance.strategy_definition:
                strategy_name = instance.strategy_definition.display_name
            
            user_name = instance.user.full_name or instance.user.email if instance.user else "Unknown"
            
            instance_list.append(
                InstanceListItemResponse(
                    id=str(instance.id),
                    instance_name=instance.instance_name,
                    instance_description=instance.instance_description,
                    strategy_definition_id=instance.strategy_definition_id,
                    strategy_display_name=strategy_name,
                    user_id=instance.user_id,
                    user_name=user_name,
                    is_active=instance.is_active,
                    total_value=float(instance.total_value),
                    total_pnl=float(instance.total_pnl),
                    total_pnl_percent=instance.total_pnl_percent or 0.0,
                    created_at=instance.created_at.isoformat(),
                )
            )
        
        return InstanceListResponse(
            instances=instance_list,
            total=len(instance_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略实例列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get instances: {str(e)}")


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





