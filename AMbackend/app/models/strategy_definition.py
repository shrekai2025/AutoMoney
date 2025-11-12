"""Strategy Definition Model - 策略模板"""

from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class StrategyDefinition(Base):
    """策略模板
    
    定义策略的核心逻辑：
    - 使用哪些业务Agent
    - 使用哪个决策引擎
    - 交易什么币种、在哪个渠道
    - 执行周期
    - 默认参数配置
    """
    __tablename__ = "strategy_definitions"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 标识和展示信息
    name = Column(String(100), unique=True, nullable=False, index=True, 
                  comment="唯一标识，如 'multi_agent_btc_v1'")
    display_name = Column(String(200), nullable=False, 
                         comment="显示名称，如 'Multi-Agent BTC Strategy'")
    description = Column(Text, comment="策略描述")
    
    # 决策引擎配置（代码引用）
    decision_agent_module = Column(String(200), nullable=False,
                                   comment="决策Agent模块路径，如 'app.decision_agents.multi_agent_conviction'")
    decision_agent_class = Column(String(100), nullable=False,
                                  comment="决策Agent类名，如 'MultiAgentConvictionDecision'")
    
    # 业务Agent配置
    business_agents = Column(JSONB, nullable=False,
                            comment="业务Agent列表，如 ['macro', 'ta', 'onchain']")
    
    # 交易配置
    trade_channel = Column(String(50), nullable=False,
                          comment="交易渠道，如 'binance_spot', 'hyperliquid_perp'")
    trade_symbol = Column(String(20), nullable=False,
                         comment="交易币种，如 'BTC', 'ETH'")
    
    # 执行周期（所有实例共享）
    rebalance_period_minutes = Column(Integer, nullable=False, default=10,
                                     comment="策略执行周期（分钟）")
    
    # 默认参数配置
    default_params = Column(JSONB, nullable=False,
                           comment="默认参数配置，包含所有阈值、权重等")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, index=True,
                      comment="模板开关")
    
    # 时间戳
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联关系
    portfolios = relationship("Portfolio", back_populates="strategy_definition")
    
    def __repr__(self):
        return f"<StrategyDefinition(id={self.id}, name={self.name}, display_name={self.display_name})>"

