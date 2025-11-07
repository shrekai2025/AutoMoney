"""Agent Execution Model

业务Agent执行记录模型 - 解耦存储架构
统一存储 MacroAgent, TAAgent, OnChainAgent 的工作成果
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, NUMERIC
from sqlalchemy.orm import relationship
from sqlalchemy import text as sa_text
import uuid
from datetime import datetime

from app.models.base import Base


class AgentExecution(Base):
    """业务Agent执行记录（解耦存储）

    设计理念：
    - Agent工作成果独立存储，不依赖调用方
    - 保留调用方关联，支持追溯和审计
    - 通过 strategy_execution_id 实现策略系统的强关联
    - 通过 caller_type + caller_id 实现灵活关联（Research Chat等）

    支持的业务Agent：
    - macro_agent (The Oracle) - 宏观分析，权重40%
    - ta_agent (Momentum Scout) - 技术分析，权重20%
    - onchain_agent (Data Warden) - 链上分析，权重40%
    """
    __tablename__ = "agent_executions"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Agent标识
    agent_name = Column(String(50), nullable=False, index=True, comment="Agent名称: macro_agent, ta_agent, onchain_agent")
    agent_display_name = Column(String(100), comment="显示名称: The Oracle, Momentum Scout, Data Warden")

    # 执行信息
    executed_at = Column(TIMESTAMP, nullable=False, index=True, comment="执行时间")
    execution_duration_ms = Column(Integer, comment="执行耗时（毫秒）")
    status = Column(String(20), default='success', comment="执行状态: success, failed, timeout")

    # 标准化输出（所有Agent统一格式）
    signal = Column(String(20), nullable=False, comment="信号: BULLISH, BEARISH, NEUTRAL")
    confidence = Column(NUMERIC(3, 2), nullable=False, comment="置信度: 0.00 ~ 1.00")
    score = Column(NUMERIC(3, 2), comment="分数: -1.00 ~ +1.00 (可选)")
    reasoning = Column(Text, nullable=False, comment="LLM推理过程")

    # Agent专属数据（JSONB灵活存储）
    agent_specific_data = Column(
        JSONB,
        nullable=False,
        comment="Agent专属数据: MacroAgent: {etf_flow, fed_rate, ...}, TAAgent: {ema_21, rsi_14, ...}, OnChainAgent: {mvrv, nvt, ...}"
    )
    market_data_snapshot = Column(JSONB, comment="执行时的完整市场数据（用于复现分析）")

    # LLM调用追踪
    llm_provider = Column(String(50), comment="LLM供应商: tuzi, openrouter")
    llm_model = Column(String(100), comment="LLM模型: claude-sonnet-4-5-thinking-all")
    llm_prompt = Column(Text, comment="发送给LLM的完整prompt")
    llm_response = Column(Text, comment="LLM原始响应")
    tokens_used = Column(Integer, comment="Token消耗")
    llm_cost = Column(NUMERIC(10, 6), comment="LLM调用成本（USD）")

    # 调用方关联（可选，实现解耦）
    caller_type = Column(
        String(50),
        index=True,
        comment="调用方类型: research_chat, strategy_system, manual, NULL"
    )
    caller_id = Column(UUID(as_uuid=True), index=True, comment="调用方ID: conversation_id (可为NULL)")

    # 💡 策略系统专用关联（强类型外键）
    strategy_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("strategy_executions.id"),
        comment="策略执行ID (可为NULL) - 策略系统的强关联"
    )

    # ⚠️ 注意: user.id 是 Integer 类型，不是 UUID
    user_id = Column(
        Integer,
        ForeignKey("user.id"),
        comment="触发用户（可为NULL，如定时任务）"
    )

    # 审计字段
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="agent_executions")
    strategy_execution = relationship("StrategyExecution", back_populates="agent_executions")

    # 约束
    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='chk_confidence'),
        CheckConstraint('score IS NULL OR (score >= -1 AND score <= 1)', name='chk_score'),
        CheckConstraint("signal IN ('BULLISH', 'BEARISH', 'NEUTRAL')", name='chk_signal'),
        CheckConstraint("status IN ('success', 'failed', 'timeout')", name='chk_status'),

        # 索引 - Mind Hub查询最新结果（最高频）
        Index(
            'idx_agent_executions_latest',
            'agent_name',
            'executed_at',
            postgresql_where=sa_text("status = 'success'")
        ),
        # 索引 - 按调用方查询
        Index(
            'idx_agent_executions_caller',
            'caller_type',
            'caller_id',
            'executed_at'
        ),
        # 索引 - 按策略执行查询（策略系统专用）
        Index(
            'idx_agent_executions_strategy',
            'strategy_execution_id',
            'executed_at'
        ),
    )

    def __repr__(self):
        return f"<AgentExecution(agent={self.agent_name}, signal={self.signal}, executed_at={self.executed_at})>"

    def to_dict(self):
        """转换为字典（用于API响应）"""
        return {
            "id": str(self.id),
            "agent_name": self.agent_name,
            "agent_display_name": self.agent_display_name,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "execution_duration_ms": self.execution_duration_ms,
            "status": self.status,
            "signal": self.signal,
            "confidence": float(self.confidence) if self.confidence else None,
            "score": float(self.score) if self.score else None,
            "reasoning": self.reasoning,
            "agent_specific_data": self.agent_specific_data,
            "caller_type": self.caller_type,
            "caller_id": str(self.caller_id) if self.caller_id else None,
            "strategy_execution_id": str(self.strategy_execution_id) if self.strategy_execution_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
