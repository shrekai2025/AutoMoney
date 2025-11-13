"""Portfolio and Trading Models"""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, NUMERIC
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.models.base import Base


class Portfolio(Base):
    """策略实例（投资组合）
    
    用户/交易员基于策略模板创建的可运行策略实例
    """
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    strategy_definition_id = Column(Integer, ForeignKey("strategy_definitions.id"), nullable=False, index=True, 
                                    comment="关联的策略模板ID")
    
    # 实例标识
    instance_name = Column(String(200), nullable=False, comment="实例名称，用户自定义")
    instance_description = Column(Text, nullable=True, comment="实例描述，用户可选")
    tags = Column(JSONB, server_default='[]', comment="策略标签（如 Macro-Driven, Low-Medium Risk）")
    risk_level = Column(String(20), server_default='medium', comment="风险程度: low, medium, high")

    # 实例参数（从模板复制而来，独立修改）
    instance_params = Column(JSONB, nullable=False, comment="实例独立参数配置")
    
    # 保留旧的name字段用于向后兼容（迁移后可考虑移除）
    name = Column(String(100), nullable=True)

    # 账户余额
    initial_balance = Column(NUMERIC(20, 8), nullable=False)
    current_balance = Column(NUMERIC(20, 8), nullable=False)
    total_value = Column(NUMERIC(20, 8), nullable=False)

    # 盈亏统计
    total_pnl = Column(NUMERIC(20, 8), server_default='0')
    total_pnl_percent = Column(Float, server_default='0')

    # 交易统计
    total_trades = Column(Integer, server_default='0')
    winning_trades = Column(Integer, server_default='0')
    losing_trades = Column(Integer, server_default='0')
    win_rate = Column(Float, server_default='0')

    # 风险指标
    max_drawdown = Column(Float, server_default='0')
    sharpe_ratio = Column(Float)

    # 状态
    is_active = Column(Boolean, server_default='true', comment="实例开关")
    
    # 运行时状态（保留，因为是动态变化的）
    last_execution_time = Column(TIMESTAMP, nullable=True, comment="上次执行时间")
    consecutive_bullish_count = Column(Integer, server_default='0', nullable=False, comment="当前连续看涨信号次数")
    consecutive_bullish_since = Column(TIMESTAMP, nullable=True, comment="连续看涨开始时间")
    consecutive_bearish_count = Column(Integer, server_default='0', nullable=False, comment="当前连续看跌信号次数")
    consecutive_bearish_since = Column(TIMESTAMP, nullable=True, comment="连续看跌开始时间")
    last_conviction_score = Column(Float, nullable=True, comment="上次信念分数")

    # 基准对比参数
    initial_btc_amount = Column(NUMERIC(20, 8), nullable=True)  # 初始BTC数量(用于基准对比)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolios")
    strategy_definition = relationship("StrategyDefinition", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_portfolios_user', 'user_id'),
        Index('idx_portfolios_active', 'is_active', 'user_id'),
        Index('idx_portfolios_definition', 'strategy_definition_id'),
    )

    def __repr__(self):
        return f"<Portfolio(id={self.id}, instance_name={self.instance_name}, user_id={self.user_id})>"


class PortfolioHolding(Base):
    """持仓记录"""
    __tablename__ = "portfolio_holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)

    amount = Column(NUMERIC(20, 8), nullable=False)
    avg_buy_price = Column(NUMERIC(20, 8), nullable=False)
    current_price = Column(NUMERIC(20, 8), nullable=False)
    market_value = Column(NUMERIC(20, 8), nullable=False)
    cost_basis = Column(NUMERIC(20, 8), nullable=False)

    unrealized_pnl = Column(NUMERIC(20, 8), server_default='0')
    unrealized_pnl_percent = Column(Float, server_default='0')

    first_buy_time = Column(TIMESTAMP, nullable=False)
    last_updated = Column(TIMESTAMP, server_default="NOW()", onupdate=datetime.utcnow)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")

    __table_args__ = (
        UniqueConstraint('portfolio_id', 'symbol', name='uq_holdings_portfolio_symbol'),
        Index('idx_holdings_portfolio', 'portfolio_id', 'symbol'),
    )

    def __repr__(self):
        return f"<PortfolioHolding(id={self.id}, symbol={self.symbol}, amount={self.amount})>"


class Trade(Base):
    """交易记录"""
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("strategy_executions.id"))

    symbol = Column(String(20), nullable=False, index=True)
    trade_type = Column(String(10), nullable=False, index=True)

    amount = Column(NUMERIC(20, 8), nullable=False)
    price = Column(NUMERIC(20, 8), nullable=False)
    total_value = Column(NUMERIC(20, 8), nullable=False)
    fee = Column(NUMERIC(20, 8), server_default='0')
    fee_percent = Column(Float, server_default='0')

    # 交易前后状态
    balance_before = Column(NUMERIC(20, 8))
    balance_after = Column(NUMERIC(20, 8))
    holding_before = Column(NUMERIC(20, 8))
    holding_after = Column(NUMERIC(20, 8))

    # 盈亏 (仅SELL时有值)
    realized_pnl = Column(NUMERIC(20, 8))
    realized_pnl_percent = Column(Float)

    # 策略决策信息
    conviction_score = Column(Float)
    signal_strength = Column(Float)
    reason = Column(Text)

    executed_at = Column(TIMESTAMP, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default="NOW()", nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")
    execution = relationship("StrategyExecution", back_populates="trades")

    __table_args__ = (
        Index('idx_trades_portfolio', 'portfolio_id', 'executed_at'),
        Index('idx_trades_execution', 'execution_id'),
        Index('idx_trades_symbol', 'symbol', 'executed_at'),
        Index('idx_trades_type', 'trade_type', 'executed_at'),
    )

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, type={self.trade_type}, amount={self.amount})>"


class PortfolioSnapshot(Base):
    """投资组合快照"""
    __tablename__ = "portfolio_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    snapshot_time = Column(TIMESTAMP, nullable=False, index=True)

    total_value = Column(NUMERIC(20, 8), nullable=False)
    balance = Column(NUMERIC(20, 8), nullable=False)
    holdings_value = Column(NUMERIC(20, 8), nullable=False)

    total_pnl = Column(NUMERIC(20, 8))
    total_pnl_percent = Column(Float)
    daily_pnl = Column(NUMERIC(20, 8))
    daily_pnl_percent = Column(Float)

    btc_price = Column(NUMERIC(20, 8))
    eth_price = Column(NUMERIC(20, 8))
    holdings = Column(JSONB)

    created_at = Column(TIMESTAMP, server_default="NOW()", nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")

    __table_args__ = (
        Index('idx_snapshots_portfolio_time', 'portfolio_id', 'snapshot_time'),
    )

    def __repr__(self):
        return f"<PortfolioSnapshot(id={self.id}, portfolio_id={self.portfolio_id}, time={self.snapshot_time})>"
