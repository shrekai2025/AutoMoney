"""Strategy Definition Service - 策略模板管理服务

负责策略模板的CRUD操作、实例创建、命名生成等
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import StrategyDefinition, Portfolio, User

logger = logging.getLogger(__name__)


class DefinitionService:
    """策略模板管理服务"""
    
    async def get_all_definitions(
        self,
        db: AsyncSession,
        include_inactive: bool = False
    ) -> List[StrategyDefinition]:
        """
        获取所有策略模板
        
        Args:
            db: 数据库会话
            include_inactive: 是否包含未激活的模板
            
        Returns:
            策略模板列表
        """
        query = select(StrategyDefinition)
        
        if not include_inactive:
            query = query.where(StrategyDefinition.is_active == True)
        
        query = query.order_by(StrategyDefinition.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_definition_by_id(
        self,
        db: AsyncSession,
        definition_id: int
    ) -> Optional[StrategyDefinition]:
        """
        获取单个策略模板
        
        Args:
            db: 数据库会话
            definition_id: 模板ID
            
        Returns:
            策略模板或None
        """
        result = await db.execute(
            select(StrategyDefinition).where(StrategyDefinition.id == definition_id)
        )
        return result.scalar_one_or_none()
    
    async def get_definition_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[StrategyDefinition]:
        """
        根据name获取策略模板
        
        Args:
            db: 数据库会话
            name: 模板name（唯一标识）
            
        Returns:
            策略模板或None
        """
        result = await db.execute(
            select(StrategyDefinition).where(StrategyDefinition.name == name)
        )
        return result.scalar_one_or_none()
    
    async def update_definition(
        self,
        db: AsyncSession,
        definition_id: int,
        update_data: Dict[str, Any]
    ) -> StrategyDefinition:
        """
        更新策略模板
        
        Args:
            db: 数据库会话
            definition_id: 模板ID
            update_data: 更新数据
            
        Returns:
            更新后的策略模板
            
        Raises:
            ValueError: 如果模板不存在
        """
        definition = await self.get_definition_by_id(db, definition_id)
        if not definition:
            raise ValueError(f"Strategy definition {definition_id} not found")
        
        # 更新允许的字段
        allowed_fields = [
            "display_name", "description", "default_params",
            "rebalance_period_minutes", "is_active"
        ]
        
        for field, value in update_data.items():
            if field in allowed_fields and value is not None:
                setattr(definition, field, value)
        
        definition.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(definition)
        
        logger.info(f"Updated strategy definition: {definition.name}")
        return definition
    
    async def generate_default_instance_name(
        self,
        db: AsyncSession,
        definition: StrategyDefinition,
        user: User
    ) -> str:
        """
        生成默认的实例名称
        
        格式: {模板名称} - {用户名} - #{序号}
        
        Args:
            db: 数据库会话
            definition: 策略模板
            user: 用户
            
        Returns:
            默认实例名称
        """
        # 查询该用户基于该模板已创建的实例数
        result = await db.execute(
            select(func.count(Portfolio.id))
            .where(
                Portfolio.user_id == user.id,
                Portfolio.strategy_definition_id == definition.id
            )
        )
        count = result.scalar() or 0
        
        # 生成名称
        user_name = user.full_name or user.email.split('@')[0]
        instance_name = f"{definition.display_name} - {user_name} - #{count + 1}"
        
        return instance_name
    
    async def create_instance_from_definition(
        self,
        db: AsyncSession,
        definition_id: int,
        user_id: int,
        initial_balance: float,
        instance_name: Optional[str] = None,
        instance_description: Optional[str] = None,
        instance_params: Optional[Dict[str, Any]] = None,
    ) -> Portfolio:
        """
        从策略模板创建实例
        
        Args:
            db: 数据库会话
            definition_id: 策略模板ID
            user_id: 用户ID
            initial_balance: 初始资金
            instance_name: 实例名称（可选，不提供则自动生成）
            instance_description: 实例描述（可选）
            instance_params: 实例参数（可选，不提供则使用模板默认值）
            
        Returns:
            创建的Portfolio实例
            
        Raises:
            ValueError: 如果模板或用户不存在
        """
        # 1. 获取模板
        definition = await self.get_definition_by_id(db, definition_id)
        if not definition:
            raise ValueError(f"Strategy definition {definition_id} not found")
        
        if not definition.is_active:
            raise ValueError(f"Strategy definition {definition_id} is not active")
        
        # 2. 获取用户
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # 3. 生成实例名称（如果未提供）
        if not instance_name:
            instance_name = await self.generate_default_instance_name(db, definition, user)
        
        # 4. 准备实例参数（从模板复制）
        final_instance_params = definition.default_params.copy()
        
        # 如果用户提供了自定义参数，覆盖默认值
        if instance_params:
            final_instance_params.update(instance_params)
        
        # 5. 创建Portfolio实例
        portfolio = Portfolio(
            user_id=user_id,
            strategy_definition_id=definition_id,
            instance_name=instance_name,
            instance_description=instance_description,
            instance_params=final_instance_params,
            
            # 资金相关
            initial_balance=Decimal(str(initial_balance)),
            current_balance=Decimal(str(initial_balance)),
            total_value=Decimal(str(initial_balance)),
            
            # 状态
            is_active=True,  # 创建后自动激活
            
            # 运行时状态初始化
            consecutive_bullish_count=0,
            consecutive_bearish_count=0,
            
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)
        
        logger.info(
            f"Created strategy instance: {portfolio.instance_name} "
            f"(ID: {portfolio.id}, User: {user.email})"
        )
        
        return portfolio
    
    async def get_instances_by_definition(
        self,
        db: AsyncSession,
        definition_id: int,
        active_only: bool = True
    ) -> List[Portfolio]:
        """
        获取某个模板的所有实例
        
        Args:
            db: 数据库会话
            definition_id: 模板ID
            active_only: 是否只返回活跃实例
            
        Returns:
            实例列表
        """
        query = select(Portfolio).where(
            Portfolio.strategy_definition_id == definition_id
        )
        
        if active_only:
            query = query.where(Portfolio.is_active == True)
        
        query = query.order_by(Portfolio.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()


# 全局实例
definition_service = DefinitionService()

