"""Tool Manager - 工具注册管理

用于查询和管理Tool注册表
"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import ToolRegistry

logger = logging.getLogger(__name__)


class ToolManager:
    """工具管理器"""
    
    async def list_all_tools(
        self,
        db: AsyncSession,
        active_only: bool = True
    ) -> List[ToolRegistry]:
        """
        获取所有注册的Tools
        
        Args:
            db: 数据库会话
            active_only: 是否只返回活跃的Tool
            
        Returns:
            Tool列表
        """
        query = select(ToolRegistry)
        
        if active_only:
            query = query.where(ToolRegistry.is_active == True)
        
        query = query.order_by(ToolRegistry.created_at)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_tool_by_name(
        self,
        db: AsyncSession,
        tool_name: str
    ) -> Optional[ToolRegistry]:
        """
        根据名称获取Tool
        
        Args:
            db: 数据库会话
            tool_name: Tool名称
            
        Returns:
            Tool或None
        """
        result = await db.execute(
            select(ToolRegistry).where(ToolRegistry.tool_name == tool_name)
        )
        return result.scalar_one_or_none()
    
    async def get_tool_required_apis(
        self,
        db: AsyncSession,
        tool_name: str
    ) -> List[str]:
        """
        获取Tool依赖的APIs
        
        Args:
            db: 数据库会话
            tool_name: Tool名称
            
        Returns:
            API名称列表
        """
        tool = await self.get_tool_by_name(db, tool_name)
        if not tool:
            return []
        
        return tool.required_apis or []


# 全局实例
tool_manager = ToolManager()

