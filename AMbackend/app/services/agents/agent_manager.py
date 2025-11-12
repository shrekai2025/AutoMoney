"""Agent Manager - 业务Agent注册管理

用于查询和管理业务Agent注册表
"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import AgentRegistry

logger = logging.getLogger(__name__)


class AgentManager:
    """业务Agent管理器"""
    
    async def list_all_agents(
        self,
        db: AsyncSession,
        active_only: bool = True
    ) -> List[AgentRegistry]:
        """
        获取所有注册的业务Agent
        
        Args:
            db: 数据库会话
            active_only: 是否只返回活跃的Agent
            
        Returns:
            Agent列表
        """
        query = select(AgentRegistry)
        
        if active_only:
            query = query.where(AgentRegistry.is_active == True)
        
        query = query.order_by(AgentRegistry.created_at)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_agent_by_name(
        self,
        db: AsyncSession,
        agent_name: str
    ) -> Optional[AgentRegistry]:
        """
        根据名称获取Agent
        
        Args:
            db: 数据库会话
            agent_name: Agent名称
            
        Returns:
            Agent或None
        """
        result = await db.execute(
            select(AgentRegistry).where(AgentRegistry.agent_name == agent_name)
        )
        return result.scalar_one_or_none()
    
    async def get_agent_tools(
        self,
        db: AsyncSession,
        agent_name: str
    ) -> List[str]:
        """
        获取Agent使用的Tools
        
        Args:
            db: 数据库会话
            agent_name: Agent名称
            
        Returns:
            Tool名称列表
        """
        agent = await self.get_agent_by_name(db, agent_name)
        if not agent:
            return []
        
        return agent.available_tools or []


# 全局实例
agent_manager = AgentManager()

