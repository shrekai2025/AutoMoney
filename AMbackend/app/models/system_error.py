"""System error tracking model"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class SystemError(Base):
    """系统错误记录表"""
    
    __tablename__ = "system_errors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 错误基本信息
    error_type = Column(String(100), nullable=False, index=True)  # 'data_collection', 'agent_execution', 'strategy_execution', etc.
    error_category = Column(String(50), nullable=False, index=True)  # 'network', 'api', 'logic', 'timeout', etc.
    severity = Column(String(20), nullable=False, index=True)  # 'critical', 'error', 'warning', 'info'
    
    # 错误详情
    component = Column(String(200), nullable=False)  # 'BinanceCollector', 'MacroAgent', 'Scheduler', etc.
    error_message = Column(Text, nullable=False)  # 简短错误信息
    error_details = Column(Text)  # 详细堆栈信息
    
    # 上下文信息
    context = Column(JSON)  # 错误发生时的上下文数据
    user_id = Column(Integer, nullable=True)  # 如果与特定用户相关
    portfolio_id = Column(String(36), nullable=True)  # 如果与特定Portfolio相关
    strategy_name = Column(String(100), nullable=True)  # 如果与特定策略相关
    
    # 错误状态
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)
    
    # 发生次数(如果是重复错误)
    occurrence_count = Column(Integer, default=1)
    first_occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    last_occurred_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

