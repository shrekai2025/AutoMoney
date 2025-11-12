"""Strategy Instance Service - 策略实例管理服务（重构版）

负责策略实例（Portfolio）的查询、更新等操作
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models import Portfolio, User, StrategyDefinition

logger = logging.getLogger(__name__)


class InstanceService:
    """策略实例管理服务"""
    
    async def get_all_instances(
        self,
        db: AsyncSession,
        user_role: str,
        user_id: Optional[int] = None,
        definition_id: Optional[int] = None,
        active_only: bool = False
    ) -> List[Portfolio]:
        """
        获取策略实例列表（根据角色过滤）
        
        Args:
            db: 数据库会话
            user_role: 用户角色 (user/trader/admin)
            user_id: 用户ID（可选，用于过滤特定用户的实例）
            definition_id: 策略模板ID（可选，用于过滤特定模板的实例）
            active_only: 是否只返回活跃实例
            
        Returns:
            实例列表
        """
        query = select(Portfolio).options(
            selectinload(Portfolio.strategy_definition),
            selectinload(Portfolio.user),
            selectinload(Portfolio.holdings)
        )
        
        # 根据角色过滤
        if user_role == "user":
            # 普通用户只能看到活跃的实例
            query = query.where(Portfolio.is_active == True)
        # trader和admin可以看到所有实例（由active_only参数控制）
        
        if active_only:
            query = query.where(Portfolio.is_active == True)
        
        if user_id:
            query = query.where(Portfolio.user_id == user_id)
        
        if definition_id:
            query = query.where(Portfolio.strategy_definition_id == definition_id)
        
        query = query.order_by(Portfolio.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_instance_by_id(
        self,
        db: AsyncSession,
        portfolio_id: str
    ) -> Optional[Portfolio]:
        """
        获取单个策略实例
        
        Args:
            db: 数据库会话
            portfolio_id: 实例ID
            
        Returns:
            Portfolio或None
        """
        result = await db.execute(
            select(Portfolio)
            .options(
                selectinload(Portfolio.strategy_definition),
                selectinload(Portfolio.user),
                selectinload(Portfolio.holdings)
            )
            .where(Portfolio.id == portfolio_id)
        )
        return result.scalar_one_or_none()
    
    async def update_instance(
        self,
        db: AsyncSession,
        portfolio_id: str,
        update_data: Dict[str, Any]
    ) -> Portfolio:
        """
        更新策略实例
        
        Args:
            db: 数据库会话
            portfolio_id: 实例ID
            update_data: 更新数据
            
        Returns:
            更新后的实例
            
        Raises:
            ValueError: 如果实例不存在
        """
        portfolio = await self.get_instance_by_id(db, portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # 更新允许的字段
        allowed_fields = [
            "instance_name", "instance_description", "instance_params",
            "is_active"
        ]
        
        for field, value in update_data.items():
            if field in allowed_fields and value is not None:
                setattr(portfolio, field, value)
        
        portfolio.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(portfolio)
        
        logger.info(f"Updated strategy instance: {portfolio.instance_name} (ID: {portfolio.id})")
        return portfolio
    
    async def delete_instance(
        self,
        db: AsyncSession,
        portfolio_id: str
    ) -> bool:
        """
        删除策略实例
        
        Args:
            db: 数据库会话
            portfolio_id: 实例ID
            
        Returns:
            是否成功删除
        """
        portfolio = await self.get_instance_by_id(db, portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # 先停用，然后删除
        portfolio.is_active = False
        await db.commit()
        
        await db.delete(portfolio)
        await db.commit()
        
        logger.info(f"Deleted strategy instance: {portfolio_id}")
        return True


# 全局实例
instance_service = InstanceService()





