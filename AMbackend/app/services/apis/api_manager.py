"""API Manager - API配置管理

用于查询和管理API配置
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import APIConfig

logger = logging.getLogger(__name__)


class APIManager:
    """API配置管理器"""
    
    async def list_all_apis(
        self,
        db: AsyncSession,
        active_only: bool = True
    ) -> List[APIConfig]:
        """
        获取所有API配置
        
        Args:
            db: 数据库会话
            active_only: 是否只返回活跃的API
            
        Returns:
            API配置列表
        """
        query = select(APIConfig)
        
        if active_only:
            query = query.where(APIConfig.is_active == True)
        
        query = query.order_by(APIConfig.created_at)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_api_by_name(
        self,
        db: AsyncSession,
        api_name: str
    ) -> Optional[APIConfig]:
        """
        根据名称获取API配置
        
        Args:
            db: 数据库会话
            api_name: API名称
            
        Returns:
            API配置或None
        """
        result = await db.execute(
            select(APIConfig).where(APIConfig.api_name == api_name)
        )
        return result.scalar_one_or_none()
    
    async def update_api_config(
        self,
        db: AsyncSession,
        api_name: str,
        update_data: Dict[str, Any]
    ) -> APIConfig:
        """
        更新API配置
        
        Args:
            db: 数据库会话
            api_name: API名称
            update_data: 更新数据
            
        Returns:
            更新后的API配置
            
        Raises:
            ValueError: 如果API不存在
        """
        api_config = await self.get_api_by_name(db, api_name)
        if not api_config:
            raise ValueError(f"API config {api_name} not found")
        
        # 更新允许的字段
        allowed_fields = [
            "display_name", "description", "base_url",
            "api_key_encrypted", "api_secret_encrypted",
            "rate_limit", "is_active"
        ]
        
        for field, value in update_data.items():
            if field in allowed_fields and value is not None:
                setattr(api_config, field, value)
        
        api_config.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(api_config)
        
        logger.info(f"Updated API config: {api_name}")
        return api_config
    
    def mask_api_key(self, api_key: Optional[str]) -> str:
        """
        掩码API密钥用于显示
        
        Args:
            api_key: API密钥
            
        Returns:
            掩码后的密钥
        """
        if not api_key:
            return ""
        
        if len(api_key) <= 8:
            return "****"
        
        return f"{api_key[:4]}...{api_key[-4:]}"


# 全局实例
api_manager = APIManager()

