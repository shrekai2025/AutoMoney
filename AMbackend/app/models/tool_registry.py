"""Tool Registry Model - 工具注册表"""

from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from datetime import datetime

from app.models.base import Base


class ToolRegistry(Base):
    """工具注册表
    
    用于文档展示，记录系统中所有可用的Tool：
    - Tool的基本信息
    - Tool依赖的APIs
    - Tool的代码位置
    """
    __tablename__ = "tool_registry"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # Tool标识
    tool_name = Column(String(100), unique=True, nullable=False, index=True,
                      comment="Tool唯一标识")
    display_name = Column(String(200), nullable=False,
                         comment="显示名称")
    description = Column(Text, comment="Tool功能描述")
    
    # 代码位置
    tool_module = Column(String(200), nullable=False,
                        comment="Tool模块路径")
    tool_function = Column(String(100), nullable=False,
                          comment="Tool函数名")
    
    # 依赖的APIs
    required_apis = Column(JSONB, default=list,
                          comment="Tool依赖的API列表，如 ['fred_api', 'glassnode_api']")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, index=True,
                      comment="Tool状态")
    
    # 时间戳
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ToolRegistry(id={self.id}, tool_name={self.tool_name}, display_name={self.display_name})>"

