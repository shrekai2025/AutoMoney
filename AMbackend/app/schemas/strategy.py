"""Strategy and Trading Schemas"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
from app.schemas.base import UTCAwareBaseModel


class StrategyStatus(str, Enum):
    """策略执行状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TradeSignal(str, Enum):
    """交易信号"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradeType(str, Enum):
    """交易类型"""
    BUY = "BUY"
    SELL = "SELL"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ============ Strategy Execution ============

class StrategyExecutionCreate(BaseModel):
    """创建策略执行记录"""
    strategy_name: str
    user_id: int
    market_snapshot: Dict[str, Any]


class StrategyExecutionUpdate(BaseModel):
    """更新策略执行记录"""
    status: Optional[StrategyStatus] = None
    conviction_score: Optional[float] = None
    signal: Optional[TradeSignal] = None
    signal_strength: Optional[float] = None
    position_size: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    execution_duration_ms: Optional[int] = None
    error_message: Optional[str] = None


class StrategyExecutionResponse(UTCAwareBaseModel):
    """策略执行记录响应"""
    id: str
    execution_time: datetime
    strategy_name: str
    status: StrategyStatus
    user_id: int
    conviction_score: Optional[float] = None
    signal: Optional[TradeSignal] = None
    signal_strength: Optional[float] = None
    position_size: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    execution_duration_ms: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True


# ============ Portfolio ============

class PortfolioCreate(BaseModel):
    """创建投资组合"""
    name: str
    initial_balance: Decimal = Field(..., gt=0)
    strategy_name: Optional[str] = None


class PortfolioResponse(UTCAwareBaseModel):
    """投资组合响应"""
    id: str
    user_id: int
    name: str
    initial_balance: Decimal
    current_balance: Decimal
    total_value: Decimal
    total_pnl: Decimal
    total_pnl_percent: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    is_active: bool
    strategy_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ============ Holding ============

class PortfolioHoldingResponse(UTCAwareBaseModel):
    """持仓响应"""
    id: str
    symbol: str
    amount: Decimal
    avg_buy_price: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: float
    first_buy_time: datetime
    last_updated: datetime

    class Config:
        orm_mode = True


# 为了向后兼容，保留旧名称
HoldingResponse = PortfolioHoldingResponse


class PortfolioDetailResponse(PortfolioResponse):
    """投资组合详细响应（包含持仓信息）"""
    holdings: List['PortfolioHoldingResponse'] = []

    class Config:
        orm_mode = True


# ============ Trade ============

class TradeCreate(BaseModel):
    """创建交易记录"""
    portfolio_id: str
    execution_id: Optional[str] = None
    symbol: str
    trade_type: TradeType
    amount: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    conviction_score: Optional[float] = None
    signal_strength: Optional[float] = None
    reason: Optional[str] = None


class TradeResponse(UTCAwareBaseModel):
    """交易记录响应"""
    id: str
    symbol: str
    trade_type: TradeType
    amount: Decimal
    price: Decimal
    total_value: Decimal
    fee: Decimal
    balance_before: Optional[Decimal] = None
    balance_after: Optional[Decimal] = None
    holding_before: Optional[Decimal] = None
    holding_after: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    realized_pnl_percent: Optional[float] = None
    conviction_score: Optional[float] = None
    reason: Optional[str] = None
    executed_at: datetime
    created_at: datetime

    class Config:
        orm_mode = True


# ============ Portfolio Snapshot ============

class PortfolioSnapshotResponse(UTCAwareBaseModel):
    """投资组合快照响应"""
    id: str
    snapshot_time: datetime
    total_value: Decimal
    balance: Decimal
    holdings_value: Decimal
    total_pnl: Decimal
    total_pnl_percent: float
    daily_pnl: Optional[Decimal] = None
    daily_pnl_percent: Optional[float] = None
    btc_price: Optional[Decimal] = None
    eth_price: Optional[Decimal] = None

    class Config:
        orm_mode = True


# ============ Strategy Marketplace ============

class HistoryPoint(BaseModel):
    """历史数据点"""
    date: str
    value: float


class StrategyMarketplaceCard(BaseModel):
    """策略市场卡片数据"""
    id: str
    name: str
    subtitle: str
    description: str
    tags: List[str]
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    pool_size: float
    squad_size: int
    risk_level: str
    history: List[HistoryPoint]


class StrategyMarketplaceListResponse(BaseModel):
    """策略市场列表响应"""
    strategies: List[StrategyMarketplaceCard]


class SquadAgent(BaseModel):
    """Squad Agent信息"""
    name: str
    role: str
    weight: str


class ConvictionSummary(UTCAwareBaseModel):
    """Conviction摘要"""
    score: float
    message: str
    updated_at: datetime


class PerformanceHistory(BaseModel):
    """性能历史数据"""
    strategy: List[float]
    btc_benchmark: List[float]
    eth_benchmark: List[float]
    dates: List[str]


class RecentActivity(BaseModel):
    """最近操作记录"""
    date: str
    signal: str
    action: str
    result: str
    agent: str
    execution_id: Optional[str] = None


class StrategyParameters(BaseModel):
    """策略参数"""
    assets: str
    rebalance_period: str
    risk_level: str
    min_investment: str
    lockup_period: str
    management_fee: str
    performance_fee: str


class PerformanceMetrics(BaseModel):
    """性能指标"""
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: Optional[float] = None


class HoldingInfo(BaseModel):
    """持仓信息"""
    symbol: str
    amount: float
    avg_buy_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_percent: float


class StrategyDetailResponse(BaseModel):
    """策略详情响应"""
    id: str
    name: str
    description: str
    tags: List[str]
    performance_metrics: PerformanceMetrics
    conviction_summary: ConvictionSummary
    squad_agents: List[SquadAgent]
    performance_history: PerformanceHistory
    recent_activities: List[RecentActivity]
    parameters: StrategyParameters
    philosophy: str
    holdings: List[HoldingInfo]
    total_unrealized_pnl: float
    current_balance: float


# ============ Strategy Execution Details ============

class AgentExecutionDetail(UTCAwareBaseModel):
    """Agent执行详情"""
    id: str
    agent_name: str
    agent_display_name: Optional[str]
    executed_at: datetime
    execution_duration_ms: Optional[int]
    status: str
    signal: str
    confidence: float
    score: Optional[float]
    reasoning: str
    agent_specific_data: Dict[str, Any]
    market_data_snapshot: Optional[Dict[str, Any]]
    llm_provider: Optional[str]
    llm_model: Optional[str]
    llm_prompt: Optional[str]
    llm_response: Optional[str]
    tokens_used: Optional[int]
    llm_cost: Optional[float]


class StrategyExecutionDetail(UTCAwareBaseModel):
    """策略执行详情"""
    id: str
    execution_time: datetime
    strategy_name: str
    status: str
    market_snapshot: Dict[str, Any]
    conviction_score: Optional[float]
    signal: Optional[str]
    signal_strength: Optional[float]
    position_size: Optional[float]
    risk_level: Optional[str]
    execution_duration_ms: Optional[int]
    error_message: Optional[str]
    agent_executions: List[AgentExecutionDetail]
