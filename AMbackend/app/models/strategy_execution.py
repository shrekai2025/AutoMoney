"""Strategy Execution Models"""

from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.models.base import Base


class StrategyExecution(Base):
    """策略执行记录"""
    __tablename__ = "strategy_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_time = Column(TIMESTAMP, nullable=False, index=True)
    strategy_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    # Market data
    market_snapshot = Column(JSONB, nullable=False)
    # Note: agent_outputs field removed - query from agent_executions table instead

    # Decision results
    conviction_score = Column(Float)
    signal = Column(String(10))
    signal_strength = Column(Float)
    position_size = Column(Float)
    risk_level = Column(String(20))
    llm_summary = Column(Text)  # LLM生成的策略总结

    # Execution info
    execution_duration_ms = Column(Integer)
    error_message = Column(Text)
    error_details = Column(JSONB, comment="详细错误信息（包含失败的agent、重试次数等）")

    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="strategy_executions")
    agent_executions = relationship("AgentExecution", back_populates="strategy_execution", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="execution")

    __table_args__ = (
        Index('idx_executions_user_time', 'user_id', 'execution_time'),
    )

    def __repr__(self):
        return f"<StrategyExecution(id={self.id}, strategy={self.strategy_name}, status={self.status})>"


# ❌ AgentConversation class removed
# Use agent_executions table instead (see AGENT_DECOUPLING_PLAN.md)
#
# Reasons:
# 1. Avoid data redundancy - Agent results stored only once
# 2. Implement decoupling - Agent work results independent of caller
# 3. Unified query - Mind Hub and Strategy System use same data source
# 4. Use strategy_execution_id foreign key for strong association
#
# Query method:
# agent_executions = await db.execute(
#     select(AgentExecution).where(
#         AgentExecution.strategy_execution_id == execution_id
#     )
# )
