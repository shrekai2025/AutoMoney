"""Portfolio and Trading Models"""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, NUMERIC
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.models.base import Base


class Portfolio(Base):
    """投资组合"""
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    name = Column(String(100), nullable=False)

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

    is_active = Column(Boolean, server_default='true')
    strategy_name = Column(String(100))

    # 策略参数
    rebalance_period_minutes = Column(Integer, server_default='10', nullable=False)  # 策略执行周期（分钟）
    last_execution_time = Column(TIMESTAMP, nullable=True)  # 上次执行时间
    agent_weights = Column(JSONB, nullable=True)  # Agent权重配置 {"macro": 0.40, "onchain": 0.40, "ta": 0.20}

    # 连续信号机制配置
    consecutive_bullish_count = Column(Integer, server_default='0', nullable=False)  # 当前连续看涨信号次数
    consecutive_bullish_since = Column(TIMESTAMP, nullable=True)  # 连续看涨开始时间
    consecutive_bearish_count = Column(Integer, server_default='0', nullable=False)  # 当前连续看跌信号次数
    consecutive_bearish_since = Column(TIMESTAMP, nullable=True)  # 连续看跌开始时间
    last_conviction_score = Column(Float, nullable=True)  # 上次信念分数
    consecutive_signal_threshold = Column(Integer, server_default='30', nullable=False)  # 连续信号阈值（触发加速）
    acceleration_multiplier_min = Column(Float, server_default='1.1', nullable=False)  # 加速乘数最小值
    acceleration_multiplier_max = Column(Float, server_default='2.0', nullable=False)  # 加速乘数最大值

    # 交易阈值配置
    fg_circuit_breaker_threshold = Column(Integer, server_default='20', nullable=False)  # Fear & Greed熔断阈值 (< 此值暂停交易)
    fg_position_adjust_threshold = Column(Integer, server_default='30', nullable=False)  # Fear & Greed仓位调整阈值 (< 此值减少仓位)
    buy_threshold = Column(Float, server_default='50', nullable=False)  # 买入阈值 (Conviction Score >= 此值买入)
    partial_sell_threshold = Column(Float, server_default='50', nullable=False)  # 部分减仓阈值 (Conviction Score 介于此值和full_sell之间部分减仓)
    full_sell_threshold = Column(Float, server_default='45', nullable=False)  # 全部清仓阈值 (Conviction Score < 此值全部清仓)

    # 基准对比参数
    initial_btc_amount = Column(NUMERIC(20, 8), nullable=True)  # 初始BTC数量(用于基准对比)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_portfolios_user', 'user_id'),
        Index('idx_portfolios_active', 'is_active', 'user_id'),
    )

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name={self.name}, user_id={self.user_id})>"


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
