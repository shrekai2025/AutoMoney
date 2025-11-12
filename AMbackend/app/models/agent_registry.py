"""Agent Registry Model - 业务Agent注册表"""

from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from datetime import datetime

from app.models.base import Base


class AgentRegistry(Base):
    """业务Agent注册表
    
    用于文档展示，记录系统中所有可用的业务Agent：
    - Agent的基本信息
    - Agent可用的Tools
    - Agent的代码位置
    """
    __tablename__ = "agent_registry"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # Agent标识
    agent_name = Column(String(50), unique=True, nullable=False, index=True,
                       comment="Agent唯一标识，如 'macro_agent'")
    display_name = Column(String(100), nullable=False,
                         comment="显示名称，如 'The Oracle'")
    description = Column(Text, comment="Agent功能描述")
    
    # 代码位置
    agent_module = Column(String(200), nullable=False,
                         comment="Agent模块路径，如 'app.agents.macro_agent'")
    agent_class = Column(String(100), nullable=False,
                        comment="Agent类名，如 'MacroAgent'")
    
    # 可用工具
    available_tools = Column(JSONB, default=list,
                            comment="Agent可用的Tool列表，如 ['fetch_macro_data', 'fetch_fear_greed']")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, index=True,
                      comment="Agent状态")
    
    # 时间戳
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AgentRegistry(id={self.id}, agent_name={self.agent_name}, display_name={self.display_name})>"

