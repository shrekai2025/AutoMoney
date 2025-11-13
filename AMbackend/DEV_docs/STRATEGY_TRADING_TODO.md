# 策略系统和模拟交易开发计划

> **版本**: 2.0 (最终合并版)
> **创建日期**: 2025-11-06
> **最后更新**: 2025-11-06 23:45
> **基于**: architecture-v2文档 + Phase 1完成的Multi-Agent系统
> **状态**: 📋 待开始 (Phase 1 MVP已完成100%)

---

## ⚠️ 重要架构变更

**本文档已与 `AGENT_DECOUPLING_PLAN.md` 完成协调整合**

### 核心变更
1. **删除 `agent_conversations` 表** - 改用 `agent_executions` 表统一存储Agent工作成果
2. **删除 `agent_outputs` 字段** - StrategyExecution表不再存储Agent输出，改为通过外键关联
3. **使用 `strategy_execution_id`** - agent_executions表新增外键，实现策略系统的强关联

### 架构优势
✅ **避免数据冗余** - Agent结果只存一份
✅ **实现解耦** - Agent工作成果独立于调用方
✅ **统一查询** - Mind Hub和Strategy系统使用同一数据源
✅ **灵活追溯** - 通过外键或caller字段都可以追溯

### ✅ agent_executions表已创建（2025-11-06）

**当前状态**:
- ✅ agent_executions表已创建（Migration 003）
- ✅ AgentExecutionRecorder服务已实现
- ✅ ResearchWorkflow集成完成
- ✅ 完整测试通过

**可以开始策略系统开发！**

### 开发顺序
1. ✅ **AGENT_DECOUPLING_PLAN.md Phase 1-2** - agent_executions表创建和服务实现（已完成）
2. ⏳ **本文档 Phase 1** - 创建strategy_executions等表（待开发）
3. ⏳ **本文档 Phase 2-6** - 实现策略系统其他功能（待开发）

---

## 📊 当前项目进度

### ✅ 已完成 (Phase 1 MVP - 100%)

**Week 1-2: 基础设施** ✅
- ✅ FastAPI项目初始化 + PostgreSQL + Redis Docker配置
- ✅ Firebase Authentication集成
- ✅ 数据库ORM配置 (SQLAlchemy + Alembic)
- ✅ 中间件和错误处理

**Week 3-4: Agent核心** ✅
- ✅ **Multi-Agent系统完整实现**:
  - MacroAgent (宏观分析，权重40%)
  - TAAgent (技术分析，权重20%)
  - OnChainAgent (链上分析，权重40%)
  - SuperAgent (意图路由)
  - PlanningAgent (任务规划)
  - GeneralAnalysisAgent (综合分析)
- ✅ **LLM多供应商抽象层**: OpenRouter + Tuzi，支持Fallback
- ✅ **数据采集模块 (真实API)**:
  - Alternative.me (恐惧贪婪指数)
  - Binance (价格和K线)
  - FRED (宏观经济)
  - Blockchain.info (链上数据)
  - Mempool.space (网络状态)
- ✅ **技术指标计算**: EMA, RSI, MACD, Bollinger Bands
- ✅ **Research Workflow**: 完整工作流 + SSE流式输出
- ✅ **前后端集成**: Firebase认证 + Research Chat页面

**测试状态**: 28/30 测试通过 (93%)

### ❌ 待开发 (本文档覆盖的内容)

**Phase 2: 策略系统和Paper Trading** (预计 15-20天)
- ❌ ConvictionCalculator (信念分数计算)
- ❌ SignalGenerator (交易信号生成)
- ❌ Paper Trading Engine (模拟交易引擎)
- ❌ APScheduler (定时调度)
- ❌ WebSocket实时推送
- ❌ Portfolio管理API

---

## 📅 开发周期: 预计 15-20 天

## 🎯 项目目标

基于已完成的Multi-Agent系统，开发自动化投资策略和Paper Trading模拟交易功能，实现完整的"数据采集 → Agent分析 → 策略决策 → 模拟交易"闭环。

---

## ✅ 可复用的现有模块 (100%)

| 模块 | 复用程度 | 说明 |
|-----|---------|------|
| Multi-Agent系统 | 100% | MacroAgent, TAAgent, OnChainAgent完全复用 |
| 数据采集 | 100% | Alternative.me, Binance, FRED, Blockchain.info, Mempool.space |
| LLM调用 | 100% | llm_manager (OpenRouter + Tuzi) |
| 技术指标 | 100% | EMA, RSI, MACD, Bollinger Bands |
| 认证系统 | 100% | Firebase Authentication |
| 数据库 | 100% | PostgreSQL + SQLAlchemy |

**优势**: 可以直接调用现有Agent，无需重复开发分析逻辑

---

## ⭐ 新增模块

### 1. 决策层 (ConvictionCalculator + SignalGenerator)
- 基于Agent分析结果计算投资信念分数
- 生成具体交易信号 (BUY/SELL/HOLD)
- 动态仓位管理

### 2. 交易层 (Paper Trading Engine)
- 模拟交易执行
- 投资组合管理
- 盈亏计算

### 3. 调度层 (APScheduler)
- 定时策略执行
- 市场数据定期采集
- 分布式锁机制

### 4. 存储层 (数据持久化)
- **策略执行记录** - 每次分析的完整数据
- **Agent对话记录** - LLM的完整prompt和response
- **交易记录** - 所有模拟交易
- **投资组合快照** - 历史持仓和盈亏

---

## 📊 开发阶段划分

### Phase 1: 数据库设计和模型 ✅ 优先级 P0 (预计 2-3天)
### Phase 2: 决策引擎 ✅ 优先级 P0 (预计 3-4天)
### Phase 3: Paper Trading引擎 ✅ 优先级 P0 (预计 3-4天)
### Phase 4: 策略调度系统 ✅ 优先级 P1 (预计 2-3天)
### Phase 5: API和前端集成 ✅ 优先级 P1 (预计 3-4天)
### Phase 6: 测试和优化 ✅ 优先级 P1 (预计 2-3天)

---

---

## Phase 1: 数据库设计和模型 📐

**目标**: 设计并实现完整的数据模型，支持策略执行、交易记录、Agent对话的持久化

**工期**: 2-3天

### Task 1.1: 策略执行相关表 ⏳

**数据表设计:**

#### 1. `strategy_executions` - 策略执行记录

每次策略运行的主记录，包含完整的市场数据快照和Agent分析结果。

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | UUID | 主键 |
| execution_time | TIMESTAMP | 执行时间 |
| strategy_name | VARCHAR(100) | 策略名称 (如: "HODL Wave") |
| status | VARCHAR(20) | 状态: running/completed/failed |
| user_id | UUID | 用户ID (FK: users.id) |
| market_snapshot | JSONB | 完整市场数据快照 |
| ~~agent_outputs~~ | ~~JSONB~~ | ❌ 已删除 - Agent结果从agent_executions表查询 |
| conviction_score | FLOAT | 信念分数 (0-100) |
| signal | VARCHAR(10) | 交易信号: BUY/SELL/HOLD |
| signal_strength | FLOAT | 信号强度 (0-1) |
| position_size | FLOAT | 建议仓位 (0-1) |
| risk_level | VARCHAR(20) | 风险等级: LOW/MEDIUM/HIGH |
| execution_duration_ms | INTEGER | 执行耗时(毫秒) |
| error_message | TEXT | 错误信息 (如果失败) |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**索引:**
- `idx_executions_user_time` (user_id, execution_time DESC)
- `idx_executions_strategy` (strategy_name, execution_time DESC)
- `idx_executions_status` (status)

---

#### 2. ~~`agent_conversations`~~ - ❌ 已删除

**🔄 改用 `agent_executions` 表**

Agent对话记录现在统一存储在 `agent_executions` 表中（见 `AGENT_DECOUPLING_PLAN.md`）。

**为什么删除?**
- ✅ 避免数据冗余 - Agent结果不需要在多个表存储
- ✅ 实现解耦 - Agent工作成果独立于调用方
- ✅ 统一查询 - Mind Hub和Strategy系统使用同一数据源
- ✅ 通过 `strategy_execution_id` 外键实现策略系统的强关联需求

**如何查询策略执行的Agent对话?**
```sql
SELECT * FROM agent_executions 
WHERE strategy_execution_id = 'xxx'
ORDER BY executed_at;
```

---

### Task 1.2: 交易和投资组合相关表 ⏳

#### 3. `portfolios` - 投资组合

用户的模拟交易账户。

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | UUID | 主键 |
| user_id | UUID | FK: users.id |
| name | VARCHAR(100) | 组合名称 (如: "默认策略组合") |
| initial_balance | NUMERIC(20,8) | 初始余额 (USDT) |
| current_balance | NUMERIC(20,8) | 当前余额 (USDT) |
| total_value | NUMERIC(20,8) | 总价值 (余额+持仓市值) |
| total_pnl | NUMERIC(20,8) | 总盈亏 (USDT) |
| total_pnl_percent | FLOAT | 总盈亏率 (%) |
| total_trades | INTEGER | 总交易次数 |
| winning_trades | INTEGER | 盈利交易次数 |
| losing_trades | INTEGER | 亏损交易次数 |
| win_rate | FLOAT | 胜率 (%) |
| max_drawdown | FLOAT | 最大回撤 (%) |
| sharpe_ratio | FLOAT | 夏普比率 |
| is_active | BOOLEAN | 是否激活 |
| strategy_name | VARCHAR(100) | 关联的策略名称 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**索引:**
- `idx_portfolios_user` (user_id)
- `idx_portfolios_active` (is_active, user_id)

---

#### 4. `portfolio_holdings` - 持仓记录

当前持有的加密货币。

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | UUID | 主键 |
| portfolio_id | UUID | FK: portfolios.id |
| symbol | VARCHAR(20) | 币种: BTC/ETH |
| amount | NUMERIC(20,8) | 持有数量 |
| avg_buy_price | NUMERIC(20,8) | 平均买入价格 (USDT) |
| current_price | NUMERIC(20,8) | 当前价格 (USDT) |
| market_value | NUMERIC(20,8) | 市值 (amount * current_price) |
| cost_basis | NUMERIC(20,8) | 成本 (amount * avg_buy_price) |
| unrealized_pnl | NUMERIC(20,8) | 未实现盈亏 |
| unrealized_pnl_percent | FLOAT | 未实现盈亏率 (%) |
| first_buy_time | TIMESTAMP | 首次买入时间 |
| last_updated | TIMESTAMP | 最后更新时间 |

**索引:**
- `idx_holdings_portfolio` (portfolio_id, symbol)

**唯一约束:**
- `uq_holdings_portfolio_symbol` (portfolio_id, symbol)

---

#### 5. `trades` - 交易记录

所有模拟交易的详细记录。

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | UUID | 主键 |
| portfolio_id | UUID | FK: portfolios.id |
| execution_id | UUID | FK: strategy_executions.id |
| symbol | VARCHAR(20) | 交易币种: BTC/ETH |
| trade_type | VARCHAR(10) | 交易类型: BUY/SELL |
| amount | NUMERIC(20,8) | 交易数量 |
| price | NUMERIC(20,8) | 交易价格 (USDT) |
| total_value | NUMERIC(20,8) | 交易总额 (amount * price) |
| fee | NUMERIC(20,8) | 手续费 (USDT) |
| fee_percent | FLOAT | 手续费率 (%) |
| balance_before | NUMERIC(20,8) | 交易前余额 |
| balance_after | NUMERIC(20,8) | 交易后余额 |
| holding_before | NUMERIC(20,8) | 交易前持仓 |
| holding_after | NUMERIC(20,8) | 交易后持仓 |
| realized_pnl | NUMERIC(20,8) | 已实现盈亏 (仅SELL时有值) |
| realized_pnl_percent | FLOAT | 已实现盈亏率 (%) |
| conviction_score | FLOAT | 执行时的信念分数 |
| signal_strength | FLOAT | 信号强度 |
| reason | TEXT | 交易原因 (来自策略决策) |
| executed_at | TIMESTAMP | 执行时间 |
| created_at | TIMESTAMP | 创建时间 |

**索引:**
- `idx_trades_portfolio` (portfolio_id, executed_at DESC)
- `idx_trades_execution` (execution_id)
- `idx_trades_symbol` (symbol, executed_at DESC)
- `idx_trades_type` (trade_type, executed_at DESC)

---

#### 6. `portfolio_snapshots` - 投资组合快照

定期记录投资组合状态，用于绘制净值曲线和性能分析。

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | UUID | 主键 |
| portfolio_id | UUID | FK: portfolios.id |
| snapshot_time | TIMESTAMP | 快照时间 |
| total_value | NUMERIC(20,8) | 总价值 |
| balance | NUMERIC(20,8) | 现金余额 |
| holdings_value | NUMERIC(20,8) | 持仓市值 |
| total_pnl | NUMERIC(20,8) | 累计盈亏 |
| total_pnl_percent | FLOAT | 累计盈亏率 (%) |
| daily_pnl | NUMERIC(20,8) | 日盈亏 |
| daily_pnl_percent | FLOAT | 日盈亏率 (%) |
| btc_price | NUMERIC(20,8) | BTC价格 |
| eth_price | NUMERIC(20,8) | ETH价格 |
| holdings | JSONB | 持仓详情 |
| created_at | TIMESTAMP | 创建时间 |

**索引:**
- `idx_snapshots_portfolio_time` (portfolio_id, snapshot_time DESC)

---

### Task 1.3: 创建Alembic迁移脚本 ⏳

**文件**: `alembic/versions/003_create_strategy_trading_tables.py`

**步骤**:
1. 生成迁移脚本
   ```bash
   alembic revision -m "create_strategy_trading_tables"
   ```

2. 编写upgrade()函数
   - 创建6个表
   - 创建所有索引
   - 创建外键约束
   - 创建唯一约束

3. 编写downgrade()函数
   - 按相反顺序删除表

4. 测试迁移
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

**验收标准**:
- [ ] 迁移脚本执行成功
- [ ] 所有表创建成功
- [ ] 所有索引创建成功
- [ ] 外键约束正确
- [ ] 可以正常回滚

---

### Task 1.4: 创建SQLAlchemy模型 ⏳

#### 文件1: `app/models/strategy_execution.py`

```python
"""Strategy Execution Models"""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, ForeignKey, Index
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
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 市场数据
    market_snapshot = Column(JSONB, nullable=False)
    # 注意: agent_outputs 字段已删除，Agent结果从 agent_executions 表查询
    
    # 决策结果
    conviction_score = Column(Float)
    signal = Column(String(10))
    signal_strength = Column(Float)
    position_size = Column(Float)
    risk_level = Column(String(20))
    
    # 执行信息
    execution_duration_ms = Column(Integer)
    error_message = Column(Text)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="strategy_executions")
    agent_executions = relationship("AgentExecution", back_populates="strategy_execution", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="execution")
    
    __table_args__ = (
        Index('idx_executions_user_time', 'user_id', 'execution_time'),
    )


# ❌ AgentConversation 类已删除
# 改用 agent_executions 表（见 AGENT_DECOUPLING_PLAN.md）
#
# 原因:
# 1. 避免数据冗余 - Agent结果不需要在多个表存储
# 2. 实现解耦 - Agent工作成果独立于调用方
# 3. 统一查询 - Mind Hub和Strategy系统使用同一数据源
# 4. 通过 strategy_execution_id 外键实现强关联
#
# 查询方式:
# agent_executions = await db.execute(
#     select(AgentExecution).where(
#         AgentExecution.strategy_execution_id == execution_id
#     )
# )
```

---

#### 文件2: `app/models/portfolio.py`

```python
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
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    
    # 账户余额
    initial_balance = Column(NUMERIC(20, 8), nullable=False)
    current_balance = Column(NUMERIC(20, 8), nullable=False)
    total_value = Column(NUMERIC(20, 8), nullable=False)
    
    # 盈亏统计
    total_pnl = Column(NUMERIC(20, 8), default=0)
    total_pnl_percent = Column(Float, default=0)
    
    # 交易统计
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0)
    
    # 风险指标
    max_drawdown = Column(Float, default=0)
    sharpe_ratio = Column(Float)
    
    is_active = Column(Boolean, default=True)
    strategy_name = Column(String(100))
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioHolding(Base):
    """持仓记录"""
    __tablename__ = "portfolio_holdings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    
    amount = Column(NUMERIC(20, 8), nullable=False)
    avg_buy_price = Column(NUMERIC(20, 8), nullable=False)
    current_price = Column(NUMERIC(20, 8), nullable=False)
    market_value = Column(NUMERIC(20, 8), nullable=False)
    cost_basis = Column(NUMERIC(20, 8), nullable=False)
    
    unrealized_pnl = Column(NUMERIC(20, 8), default=0)
    unrealized_pnl_percent = Column(Float, default=0)
    
    first_buy_time = Column(TIMESTAMP, nullable=False)
    last_updated = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'symbol', name='uq_holdings_portfolio_symbol'),
        Index('idx_holdings_portfolio', 'portfolio_id', 'symbol'),
    )


class Trade(Base):
    """交易记录"""
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("strategy_executions.id"))
    
    symbol = Column(String(20), nullable=False, index=True)
    trade_type = Column(String(10), nullable=False, index=True)
    
    amount = Column(NUMERIC(20, 8), nullable=False)
    price = Column(NUMERIC(20, 8), nullable=False)
    total_value = Column(NUMERIC(20, 8), nullable=False)
    fee = Column(NUMERIC(20, 8), default=0)
    fee_percent = Column(Float, default=0)
    
    # 交易前后状态
    balance_before = Column(NUMERIC(20, 8))
    balance_after = Column(NUMERIC(20, 8))
    holding_before = Column(NUMERIC(20, 8))
    holding_after = Column(NUMERIC(20, 8))
    
    # 盈亏
    realized_pnl = Column(NUMERIC(20, 8))
    realized_pnl_percent = Column(Float)
    
    # 策略决策信息
    conviction_score = Column(Float)
    signal_strength = Column(Float)
    reason = Column(Text)
    
    executed_at = Column(TIMESTAMP, nullable=False, index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")
    execution = relationship("StrategyExecution", back_populates="trades")
    
    __table_args__ = (
        Index('idx_trades_portfolio', 'portfolio_id', 'executed_at'),
    )


class PortfolioSnapshot(Base):
    """投资组合快照"""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
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
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")
    
    __table_args__ = (
        Index('idx_snapshots_portfolio_time', 'portfolio_id', 'snapshot_time'),
    )
```

---

#### 文件3: `app/models/__init__.py` (更新)

```python
"""Models package"""

from app.models.base import Base
from app.models.user import User
from app.models.strategy_execution import StrategyExecution
from app.models.portfolio import Portfolio, PortfolioHolding, Trade, PortfolioSnapshot
from app.models.agent_execution import AgentExecution  # 从解耦计划导入

__all__ = [
    "Base",
    "User",
    "StrategyExecution",
    "AgentExecution",  # 替代 AgentConversation
    "Portfolio",
    "PortfolioHolding",
    "Trade",
    "PortfolioSnapshot",
]
```

---

### Task 1.5: 创建Pydantic Schemas ⏳

#### 文件: `app/schemas/strategy.py`

```python
"""Strategy and Trading Schemas"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator


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
    user_id: str
    market_snapshot: Dict[str, Any]
    agent_outputs: Dict[str, Any]


class StrategyExecutionUpdate(BaseModel):
    """更新策略执行记录"""
    status: Optional[StrategyStatus]
    conviction_score: Optional[float]
    signal: Optional[TradeSignal]
    signal_strength: Optional[float]
    position_size: Optional[float]
    risk_level: Optional[RiskLevel]
    execution_duration_ms: Optional[int]
    error_message: Optional[str]


class StrategyExecutionResponse(BaseModel):
    """策略执行记录响应"""
    id: str
    execution_time: datetime
    strategy_name: str
    status: StrategyStatus
    user_id: str
    conviction_score: Optional[float]
    signal: Optional[TradeSignal]
    signal_strength: Optional[float]
    position_size: Optional[float]
    risk_level: Optional[RiskLevel]
    execution_duration_ms: Optional[int]
    created_at: datetime
    
    class Config:
        orm_mode = True


# ============ Agent Conversation ============
# ❌ AgentConversation schemas 已删除
# 改用 agent_executions 表的 schemas (见 AGENT_DECOUPLING_PLAN.md)
#
# 如需查询Agent执行记录，使用:
# from app.schemas.agents import AgentExecutionResponse


# ============ Portfolio ============

class PortfolioCreate(BaseModel):
    """创建投资组合"""
    name: str
    initial_balance: Decimal = Field(..., gt=0)
    strategy_name: Optional[str]


class PortfolioResponse(BaseModel):
    """投资组合响应"""
    id: str
    user_id: str
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
    sharpe_ratio: Optional[float]
    is_active: bool
    strategy_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# ============ Holding ============

class HoldingResponse(BaseModel):
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


# ============ Trade ============

class TradeCreate(BaseModel):
    """创建交易记录"""
    portfolio_id: str
    execution_id: Optional[str]
    symbol: str
    trade_type: TradeType
    amount: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    conviction_score: Optional[float]
    signal_strength: Optional[float]
    reason: Optional[str]


class TradeResponse(BaseModel):
    """交易记录响应"""
    id: str
    symbol: str
    trade_type: TradeType
    amount: Decimal
    price: Decimal
    total_value: Decimal
    fee: Decimal
    balance_before: Decimal
    balance_after: Decimal
    holding_before: Decimal
    holding_after: Decimal
    realized_pnl: Optional[Decimal]
    realized_pnl_percent: Optional[float]
    conviction_score: Optional[float]
    reason: Optional[str]
    executed_at: datetime
    created_at: datetime
    
    class Config:
        orm_mode = True


# ============ Portfolio Snapshot ============

class PortfolioSnapshotResponse(BaseModel):
    """投资组合快照响应"""
    id: str
    snapshot_time: datetime
    total_value: Decimal
    balance: Decimal
    holdings_value: Decimal
    total_pnl: Decimal
    total_pnl_percent: float
    daily_pnl: Optional[Decimal]
    daily_pnl_percent: Optional[float]
    btc_price: Optional[Decimal]
    eth_price: Optional[Decimal]
    
    class Config:
        orm_mode = True
```

---

### Task 1.6: 测试数据库模型 ⏳

**测试文件**: `tests/unit/test_strategy_models.py`

```python
"""Test Strategy and Trading Models"""

import pytest
from decimal import Decimal
from datetime import datetime
from app.models import (
    StrategyExecution,
    AgentExecution,  # 替代 AgentConversation
    Portfolio,
    PortfolioHolding,
    Trade,
    PortfolioSnapshot
)


@pytest.mark.asyncio
async def test_create_strategy_execution(db_session, test_user):
    """测试创建策略执行记录"""
    execution = StrategyExecution(
        execution_time=datetime.utcnow(),
        strategy_name="HODL Wave",
        status="completed",
        user_id=test_user.id,
        market_snapshot={"btc_price": 45000},
        # agent_outputs字段已删除
        conviction_score=75.5,
        signal="BUY",
    )
    
    db_session.add(execution)
    await db_session.commit()
    
    assert execution.id is not None
    assert execution.conviction_score == 75.5


@pytest.mark.asyncio
async def test_create_portfolio(db_session, test_user):
    """测试创建投资组合"""
    portfolio = Portfolio(
        user_id=test_user.id,
        name="测试组合",
        initial_balance=Decimal("10000"),
        current_balance=Decimal("10000"),
        total_value=Decimal("10000"),
    )
    
    db_session.add(portfolio)
    await db_session.commit()
    
    assert portfolio.id is not None
    assert portfolio.current_balance == Decimal("10000")


# 更多测试...
```

---

### Phase 1 验收标准

- [ ] ✅ 5个数据表创建成功 (删除了agent_conversations)
  - strategy_executions
  - portfolios
  - portfolio_holdings
  - trades
  - portfolio_snapshots
- [ ] ⚠️ agent_executions表由 AGENT_DECOUPLING_PLAN.md 创建
- [ ] Alembic迁移可以正常执行和回滚
- [ ] SQLAlchemy模型创建成功
- [ ] 模型之间的关系正确 (StrategyExecution → AgentExecution)
- [ ] Pydantic schemas验证正常
- [ ] 单元测试全部通过

---

---

## Phase 2: 决策引擎 🧠

**目标**: 实现ConvictionCalculator和SignalGenerator，基于Agent分析结果生成交易决策

**工期**: 3-4天

### Task 2.1: ConvictionCalculator - 信念分数计算器 ⏳

**目标**: 将3个Agent的分析结果转换为0-100的信念分数

**文件**: `app/services/decision/conviction_calculator.py`

```python
"""Conviction Calculator - 计算投资信念分数"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ConvictionInput:
    """信念计算输入"""
    macro_output: Dict[str, Any]  # MacroAgent输出
    ta_output: Dict[str, Any]     # TAAgent输出
    onchain_output: Dict[str, Any]  # OnChainAgent输出
    market_data: Dict[str, Any]   # 当前市场数据


@dataclass
class ConvictionResult:
    """信念计算结果"""
    score: float  # 0-100
    raw_weighted_score: float  # 加权前原始分数
    macro_contribution: float  # MacroAgent贡献
    ta_contribution: float     # TAAgent贡献
    onchain_contribution: float  # OnChainAgent贡献
    risk_adjustment: float     # 风险调整因子
    confidence_adjustment: float  # 置信度调整因子
    details: Dict[str, Any]    # 详细计算过程


class ConvictionCalculator:
    """
    信念分数计算器
    
    计算逻辑:
    1. 将每个Agent的signal转换为基础分数 (-100到+100)
    2. 应用Agent权重 (Macro 40%, OnChain 40%, TA 20%)
    3. 根据风险指标调整 (恐惧指数, 波动率)
    4. 根据置信度调整
    5. 归一化到0-100
    """
    
    # Agent权重配置
    WEIGHTS = {
        "macro": 0.40,      # 宏观分析权重40%
        "onchain": 0.40,    # 链上分析权重40%
        "ta": 0.20,         # 技术分析权重20%
    }
    
    # Signal到分数的映射
    SIGNAL_SCORES = {
        "BULLISH": 100,
        "NEUTRAL": 0,
        "BEARISH": -100,
    }
    
    def calculate(self, input_data: ConvictionInput) -> ConvictionResult:
        """
        计算信念分数
        
        Args:
            input_data: Agent输出和市场数据
            
        Returns:
            ConvictionResult: 信念分数和详细信息
        """
        # Step 1: 获取每个Agent的基础分数
        macro_score = self._get_agent_score(input_data.macro_output)
        ta_score = self._get_agent_score(input_data.ta_output)
        onchain_score = self._get_agent_score(input_data.onchain_output)
        
        # Step 2: 应用权重
        weighted_score = (
            macro_score * self.WEIGHTS["macro"]
            + onchain_score * self.WEIGHTS["onchain"]
            + ta_score * self.WEIGHTS["ta"]
        )
        
        # Step 3: 风险调整
        risk_factor = self._calculate_risk_factor(input_data.market_data)
        
        # Step 4: 置信度调整
        confidence_factor = self._calculate_confidence_factor(input_data)
        
        # Step 5: 应用调整
        adjusted_score = weighted_score * risk_factor * confidence_factor
        
        # Step 6: 归一化到0-100 (原来-100到+100)
        normalized_score = (adjusted_score + 100) / 2
        
        # 限制在0-100范围
        final_score = max(0, min(100, normalized_score))
        
        return ConvictionResult(
            score=final_score,
            raw_weighted_score=weighted_score,
            macro_contribution=macro_score * self.WEIGHTS["macro"],
            ta_contribution=ta_score * self.WEIGHTS["ta"],
            onchain_contribution=onchain_score * self.WEIGHTS["onchain"],
            risk_adjustment=risk_factor,
            confidence_adjustment=confidence_factor,
            details={
                "agent_scores": {
                    "macro": macro_score,
                    "ta": ta_score,
                    "onchain": onchain_score,
                },
                "weighted_score": weighted_score,
                "risk_factor": risk_factor,
                "confidence_factor": confidence_factor,
                "adjusted_score": adjusted_score,
            }
        )
    
    def _get_agent_score(self, agent_output: Dict[str, Any]) -> float:
        """
        获取Agent的基础分数
        
        将signal (BULLISH/NEUTRAL/BEARISH) 和 confidence (0-1)
        转换为 -100到+100的分数
        """
        signal = agent_output.get("signal", "NEUTRAL")
        confidence = agent_output.get("confidence", 0.5)
        
        base_score = self.SIGNAL_SCORES.get(signal, 0)
        
        # 根据置信度调整: confidence越低,分数越靠近0
        adjusted_score = base_score * confidence
        
        return adjusted_score
    
    def _calculate_risk_factor(self, market_data: Dict[str, Any]) -> float:
        """
        计算风险调整因子 (0-1)
        
        考虑因素:
        - 恐惧贪婪指数 (Fear & Greed)
        - 价格波动率
        - DXY美元指数
        """
        risk_factor = 1.0
        
        # 1. 恐惧指数调整
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 20:  # 极度恐惧
            risk_factor *= 0.7  # 降低30%
        elif fg_value > 80:  # 极度贪婪
            risk_factor *= 0.8  # 降低20%
        
        # 2. 波动率调整 (从价格变化推断)
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 10:  # 24h波动超过10%
            risk_factor *= 0.75  # 降低25%
        elif price_change > 5:  # 24h波动超过5%
            risk_factor *= 0.9   # 降低10%
        
        # 3. 美元强度调整
        dxy = market_data.get("macro", {}).get("dxy_index", 100)
        if dxy > 110:  # 美元极强
            risk_factor *= 0.85  # 降低15%
        
        return risk_factor
    
    def _calculate_confidence_factor(self, input_data: ConvictionInput) -> float:
        """
        计算综合置信度因子 (0-1)
        
        如果所有Agent的置信度都很低,降低整体信念分数
        """
        confidences = [
            input_data.macro_output.get("confidence", 0.5),
            input_data.ta_output.get("confidence", 0.5),
            input_data.onchain_output.get("confidence", 0.5),
        ]
        
        avg_confidence = sum(confidences) / len(confidences)
        
        # 置信度低于0.4时开始降低因子
        if avg_confidence < 0.4:
            return 0.7
        elif avg_confidence < 0.5:
            return 0.85
        else:
            return 1.0


# 全局实例
conviction_calculator = ConvictionCalculator()
```

---

### Task 2.2: SignalGenerator - 交易信号生成器 ⏳

**目标**: 根据信念分数生成具体的交易信号和仓位大小

**文件**: `app/services/decision/signal_generator.py`

```python
"""Signal Generator - 生成交易信号"""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class TradeSignal(str, Enum):
    """交易信号"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class SignalOutput:
    """信号输出"""
    signal: TradeSignal
    signal_strength: float  # 0-1
    position_size: float    # 0-1 (占总资金的比例)
    risk_level: RiskLevel
    should_execute: bool    # 是否应该执行交易
    reasons: List[str]      # 决策原因
    warnings: List[str]     # 风险警告


@dataclass
class CircuitBreaker:
    """熔断规则"""
    is_triggered: bool
    rule_name: str
    description: str


class SignalGenerator:
    """
    交易信号生成器
    
    规则:
    1. Conviction < 30: SELL
    2. 30 <= Conviction < 45: HOLD (偏空)
    3. 45 <= Conviction < 55: HOLD (中性)
    4. 55 <= Conviction < 70: HOLD (偏多)
    5. Conviction >= 70: BUY
    
    熔断机制:
    - 极度恐惧 (Fear < 20): 暂停买入
    - 美元极强 (DXY > 115): 降低仓位
    - 极度波动 (24h > 15%): 暂停交易
    """
    
    # 信号阈值
    SELL_THRESHOLD = 30
    WEAK_HOLD_THRESHOLD = 45
    NEUTRAL_THRESHOLD = 55
    STRONG_HOLD_THRESHOLD = 70
    
    # 仓位配置
    MIN_POSITION_SIZE = 0.002  # 最小0.2% (原0.25%调整为更保守)
    MAX_POSITION_SIZE = 0.005  # 最大0.5% (原0.75%调整为更保守)
    
    def generate_signal(
        self,
        conviction_score: float,
        market_data: dict,
        current_position: Optional[float] = None
    ) -> SignalOutput:
        """
        生成交易信号
        
        Args:
            conviction_score: 信念分数 (0-100)
            market_data: 市场数据
            current_position: 当前持仓比例 (0-1)
            
        Returns:
            SignalOutput: 交易信号和详细信息
        """
        reasons = []
        warnings = []
        current_position = current_position or 0.0
        
        # Step 1: 检查熔断规则
        circuit_breaker = self._check_circuit_breaker(market_data)
        if circuit_breaker.is_triggered:
            warnings.append(f"⚠️ 熔断触发: {circuit_breaker.description}")
            return SignalOutput(
                signal=TradeSignal.HOLD,
                signal_strength=0.0,
                position_size=0.0,
                risk_level=RiskLevel.HIGH,
                should_execute=False,
                reasons=[f"熔断: {circuit_breaker.description}"],
                warnings=warnings,
            )
        
        # Step 2: 根据conviction_score确定信号
        if conviction_score >= self.STRONG_HOLD_THRESHOLD:
            signal = TradeSignal.BUY
            signal_strength = (conviction_score - self.STRONG_HOLD_THRESHOLD) / 30
            reasons.append(f"✅ 强烈看多 (信念分数: {conviction_score:.1f}/100)")
            
        elif conviction_score < self.SELL_THRESHOLD:
            signal = TradeSignal.SELL
            signal_strength = (self.SELL_THRESHOLD - conviction_score) / 30
            reasons.append(f"🔴 强烈看空 (信念分数: {conviction_score:.1f}/100)")
            
        else:
            signal = TradeSignal.HOLD
            signal_strength = 0.0
            
            if conviction_score < self.WEAK_HOLD_THRESHOLD:
                reasons.append(f"⚪ 持币观望 - 偏空 (信念分数: {conviction_score:.1f}/100)")
            elif conviction_score < self.NEUTRAL_THRESHOLD:
                reasons.append(f"⚪ 持币观望 - 中性 (信念分数: {conviction_score:.1f}/100)")
            else:
                reasons.append(f"⚪ 持币观望 - 偏多 (信念分数: {conviction_score:.1f}/100)")
        
        # Step 3: 计算仓位大小
        position_size = self._calculate_position_size(
            conviction_score,
            signal,
            signal_strength,
            market_data
        )
        
        # Step 4: 评估风险等级
        risk_level = self._assess_risk_level(market_data, conviction_score)
        
        # Step 5: 决定是否执行
        should_execute = self._should_execute(
            signal,
            position_size,
            current_position,
            market_data
        )
        
        if not should_execute and signal != TradeSignal.HOLD:
            reasons.append(f"⏸️ 暂不执行 (仓位限制或风控)")
        
        # Step 6: 添加市场警告
        self._add_market_warnings(market_data, warnings)
        
        return SignalOutput(
            signal=signal,
            signal_strength=signal_strength,
            position_size=position_size,
            risk_level=risk_level,
            should_execute=should_execute,
            reasons=reasons,
            warnings=warnings,
        )
    
    def _check_circuit_breaker(self, market_data: dict) -> CircuitBreaker:
        """检查熔断规则"""
        
        # 1. 极度恐惧
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 20:
            return CircuitBreaker(
                is_triggered=True,
                rule_name="extreme_fear",
                description=f"市场极度恐惧 (Fear & Greed: {fg_value})"
            )
        
        # 2. 美元极强
        dxy = market_data.get("macro", {}).get("dxy_index", 100)
        if dxy > 115:
            return CircuitBreaker(
                is_triggered=True,
                rule_name="strong_dollar",
                description=f"美元极度强势 (DXY: {dxy:.2f})"
            )
        
        # 3. 极度波动
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 15:
            return CircuitBreaker(
                is_triggered=True,
                rule_name="high_volatility",
                description=f"价格极度波动 (24h: {price_change:.1f}%)"
            )
        
        return CircuitBreaker(
            is_triggered=False,
            rule_name="none",
            description=""
        )
    
    def _calculate_position_size(
        self,
        conviction_score: float,
        signal: TradeSignal,
        signal_strength: float,
        market_data: dict
    ) -> float:
        """
        计算仓位大小
        
        策略:
        - 信念分数越高,仓位越大
        - 波动率越高,仓位越小
        - 风险指标不好时,仓位越小
        """
        if signal == TradeSignal.HOLD:
            return 0.0
        
        # 基础仓位 (根据信念分数)
        if signal == TradeSignal.BUY:
            # Conviction 70-100 -> position 0.2%-0.5%
            base_position = self.MIN_POSITION_SIZE + (
                signal_strength * (self.MAX_POSITION_SIZE - self.MIN_POSITION_SIZE)
            )
        else:  # SELL
            # 卖出时清空所有仓位
            return 1.0
        
        # 波动率调整
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 10:
            base_position *= 0.5  # 高波动减半
        elif price_change > 5:
            base_position *= 0.75  # 中等波动减25%
        
        # 恐惧指数调整
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 30:  # 恐惧
            base_position *= 0.8
        
        return base_position
    
    def _assess_risk_level(self, market_data: dict, conviction_score: float) -> RiskLevel:
        """评估风险等级"""
        
        risk_score = 0
        
        # 恐惧指数
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 30 or fg_value > 75:
            risk_score += 1
        
        # 波动率
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 7:
            risk_score += 1
        if price_change > 12:
            risk_score += 1
        
        # 信念分数
        if conviction_score < 40 or conviction_score > 85:
            risk_score += 1
        
        if risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _should_execute(
        self,
        signal: TradeSignal,
        position_size: float,
        current_position: float,
        market_data: dict
    ) -> bool:
        """决定是否应该执行交易"""
        
        # HOLD信号不执行
        if signal == TradeSignal.HOLD:
            return False
        
        # BUY: 检查仓位限制
        if signal == TradeSignal.BUY:
            # 已经接近满仓,不再买入
            if current_position > 0.95:
                return False
            
            # 仓位太小不值得买入
            if position_size < self.MIN_POSITION_SIZE:
                return False
        
        # SELL: 检查是否有持仓
        if signal == TradeSignal.SELL:
            if current_position < 0.01:  # 几乎没有持仓
                return False
        
        return True
    
    def _add_market_warnings(self, market_data: dict, warnings: List[str]):
        """添加市场风险警告"""
        
        # 恐惧指数
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 25:
            warnings.append(f"⚠️ 市场恐惧 (Fear & Greed: {fg_value})")
        elif fg_value > 75:
            warnings.append(f"⚠️ 市场贪婪 (Fear & Greed: {fg_value})")
        
        # 波动率
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 10:
            warnings.append(f"⚠️ 高波动 (24h: {price_change:.1f}%)")


# 全局实例
signal_generator = SignalGenerator()
```

---

### Task 2.3: 决策流程编排 ⏳

**文件**: `app/services/decision/strategy_executor.py`

```python
"""Strategy Executor - 编排完整的策略执行流程"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.workflows.research_workflow import research_workflow
from app.services.data_collectors.manager import data_manager
from app.services.decision.conviction_calculator import conviction_calculator, ConvictionInput
from app.services.decision.signal_generator import signal_generator
from app.models import StrategyExecution, AgentExecution
from app.services.agents.execution_recorder import agent_execution_recorder  # 从解耦计划导入
from app.schemas.strategy import StrategyStatus


class StrategyExecutor:
    """
    策略执行器
    
    完整流程:
    1. 采集市场数据
    2. 调用Multi-Agent分析
    3. 计算信念分数
    4. 生成交易信号
    5. 保存执行记录
    """
    
    async def execute_strategy(
        self,
        user_id: str,
        strategy_name: str,
        db: AsyncSession,
        current_position: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        执行策略
        
        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            db: 数据库会话
            current_position: 当前仓位比例
            
        Returns:
            包含signal, conviction_score等的结果字典
        """
        start_time = datetime.utcnow()
        
        # Step 1: 创建执行记录
        execution = StrategyExecution(
            execution_time=start_time,
            strategy_name=strategy_name,
            status=StrategyStatus.RUNNING,
            user_id=user_id,
            market_snapshot={},
            agent_outputs={},
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        
        try:
            # Step 2: 采集市场数据
            market_snapshot = await self._collect_market_data()
            
            # Step 3: 执行Multi-Agent分析
            agent_outputs = await self._run_agent_analysis(
                execution_id=str(execution.id),
                market_snapshot=market_snapshot,
                db=db
            )
            
            # Step 4: 计算信念分数
            conviction_result = conviction_calculator.calculate(
                ConvictionInput(
                    macro_output=agent_outputs["macro_agent"],
                    ta_output=agent_outputs["ta_agent"],
                    onchain_output=agent_outputs["onchain_agent"],
                    market_data=market_snapshot,
                )
            )
            
            # Step 5: 生成交易信号
            signal_output = signal_generator.generate_signal(
                conviction_score=conviction_result.score,
                market_data=market_snapshot,
                current_position=current_position,
            )
            
            # Step 6: 更新执行记录
            execution.status = StrategyStatus.COMPLETED
            execution.market_snapshot = market_snapshot
            # agent_outputs字段已删除，Agent结果在agent_executions表
            execution.conviction_score = conviction_result.score
            execution.signal = signal_output.signal
            execution.signal_strength = signal_output.signal_strength
            execution.position_size = signal_output.position_size
            execution.risk_level = signal_output.risk_level
            execution.execution_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await db.commit()
            
            # Step 7: 构建返回结果
            return {
                "execution_id": str(execution.id),
                "execution_time": start_time.isoformat(),
                "conviction": {
                    "score": conviction_result.score,
                    "details": conviction_result.details,
                    "contributions": {
                        "macro": conviction_result.macro_contribution,
                        "ta": conviction_result.ta_contribution,
                        "onchain": conviction_result.onchain_contribution,
                    },
                    "adjustments": {
                        "risk": conviction_result.risk_adjustment,
                        "confidence": conviction_result.confidence_adjustment,
                    },
                },
                "signal": {
                    "signal": signal_output.signal,
                    "signal_strength": signal_output.signal_strength,
                    "position_size": signal_output.position_size,
                    "risk_level": signal_output.risk_level,
                    "should_execute": signal_output.should_execute,
                    "reasons": signal_output.reasons,
                    "warnings": signal_output.warnings,
                },
                "market_snapshot": market_snapshot,
                "agent_outputs": agent_outputs,
            }
            
        except Exception as e:
            # 失败时更新记录
            execution.status = StrategyStatus.FAILED
            execution.error_message = str(e)
            await db.commit()
            raise
    
    async def _collect_market_data(self) -> Dict[str, Any]:
        """采集市场数据快照"""
        snapshot = await data_manager.collect_all()
        
        return {
            "btc_price": snapshot.btc_price.price,
            "btc_price_change_24h": snapshot.btc_price.price_change_24h,
            "eth_price": snapshot.eth_price.price if snapshot.eth_price else None,
            "fear_greed": snapshot.fear_greed.dict() if snapshot.fear_greed else {},
            "macro": snapshot.macro.dict() if snapshot.macro else {},
            "ohlcv_count": len(snapshot.btc_ohlcv),
            "timestamp": snapshot.timestamp.isoformat(),
        }
    
    async def _run_agent_analysis(
        self,
        execution_id: str,
        market_snapshot: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        运行Multi-Agent分析并记录到agent_executions表
        
        复用research_workflow的_execute_business_agents方法
        """
        # 收集完整数据用于Agent分析
        macro_data = await data_manager.collect_for_macro_agent()
        ta_data = await data_manager.collect_for_ta_agent()
        onchain_data = await data_manager.collect_for_onchain_agent()
        
        market_data_dict = {
            "btc_price": market_snapshot["btc_price"],
            "macro": macro_data.get("macro"),
            "fear_greed": macro_data.get("fear_greed"),
            "indicators": ta_data.get("indicators"),
            "onchain": onchain_data,
        }
        
        # 执行3个Agent (复用workflow的_execute_business_agents)
        agent_names = ["macro_agent", "ta_agent", "onchain_agent"]
        agent_outputs = await research_workflow._execute_business_agents(
            agent_names=agent_names,
            market_data=market_data_dict,
            user_message="策略自动执行",
        )
        
        # 💡 保存到agent_executions表 (使用解耦计划的recorder)
        for agent_name, output in agent_outputs.items():
            # 根据agent类型调用对应的record方法
            if agent_name == "macro_agent":
                await agent_execution_recorder.record_macro_agent(
                    db=db,
                    output=output,
                    market_data=market_data_dict,
                    llm_info={
                        'provider': 'tuzi',
                        'model': 'claude-sonnet-4-5-thinking-all',
                        'prompt': getattr(output, 'prompt_sent', ''),
                        'response': getattr(output, 'llm_response', ''),
                        'tokens_used': getattr(output, 'tokens_used', 0),
                        'cost': 0,  # TODO: 计算实际成本
                    },
                    caller_type='strategy_system',
                    caller_id=None,
                    strategy_execution_id=execution_id,  # 🔑 关键: 使用外键关联
                    user_id=None,  # 定时任务,无user_id
                )
            elif agent_name == "ta_agent":
                await agent_execution_recorder.record_ta_agent(
                    db=db,
                    output=output,
                    market_data=market_data_dict,
                    llm_info={
                        'provider': 'tuzi',
                        'model': 'claude-sonnet-4-5-thinking-all',
                        'prompt': getattr(output, 'prompt_sent', ''),
                        'response': getattr(output, 'llm_response', ''),
                        'tokens_used': getattr(output, 'tokens_used', 0),
                        'cost': 0,
                    },
                    caller_type='strategy_system',
                    caller_id=None,
                    strategy_execution_id=execution_id,
                    user_id=None,
                )
            elif agent_name == "onchain_agent":
                await agent_execution_recorder.record_onchain_agent(
                    db=db,
                    output=output,
                    market_data=market_data_dict,
                    llm_info={
                        'provider': 'tuzi',
                        'model': 'claude-sonnet-4-5-thinking-all',
                        'prompt': getattr(output, 'prompt_sent', ''),
                        'response': getattr(output, 'llm_response', ''),
                        'tokens_used': getattr(output, 'tokens_used', 0),
                        'cost': 0,
                    },
                    caller_type='strategy_system',
                    caller_id=None,
                    strategy_execution_id=execution_id,
                    user_id=None,
                )
        
        # 转换为简单字典格式
        return {
            agent_name: {
                "signal": output.signal.value,
                "confidence": output.confidence,
                "reasoning": output.reasoning,
            }
            for agent_name, output in agent_outputs.items()
        }


# 全局实例
strategy_executor = StrategyExecutor()
```

---

### Task 2.4: 单元测试 ⏳

**文件**: `tests/unit/test_conviction_calculator.py`

```python
"""Test ConvictionCalculator"""

from app.services.decision.conviction_calculator import (
    ConvictionCalculator,
    ConvictionInput,
)


def test_conviction_calculator_bullish():
    """测试看多场景"""
    calculator = ConvictionCalculator()
    
    input_data = ConvictionInput(
        macro_output={"signal": "BULLISH", "confidence": 0.8},
        ta_output={"signal": "BULLISH", "confidence": 0.7},
        onchain_output={"signal": "BULLISH", "confidence": 0.75},
        market_data={
            "fear_greed": {"value": 60},
            "btc_price_change_24h": 3.5,
            "macro": {"dxy_index": 102},
        }
    )
    
    result = calculator.calculate(input_data)
    
    # 所有Agent看多 + 中等风险 -> 高信念分数
    assert result.score > 70
    assert result.score <= 100


def test_conviction_calculator_bearish():
    """测试看空场景"""
    calculator = ConvictionCalculator()
    
    input_data = ConvictionInput(
        macro_output={"signal": "BEARISH", "confidence": 0.75},
        ta_output={"signal": "BEARISH", "confidence": 0.8},
        onchain_output={"signal": "BEARISH", "confidence": 0.7},
        market_data={
            "fear_greed": {"value": 25},  # 恐惧
            "btc_price_change_24h": -8.0,  # 大跌
            "macro": {"dxy_index": 112},  # 美元强
        }
    )
    
    result = calculator.calculate(input_data)
    
    # 所有Agent看空 + 高风险 -> 低信念分数
    assert result.score < 30
    assert result.score >= 0


# 更多测试...
```

**文件**: `tests/unit/test_signal_generator.py`

```python
"""Test SignalGenerator"""

from app.services.decision.signal_generator import SignalGenerator, TradeSignal


def test_signal_generator_strong_buy():
    """测试强烈买入信号"""
    generator = SignalGenerator()
    
    result = generator.generate_signal(
        conviction_score=85.0,
        market_data={
            "fear_greed": {"value": 55},
            "btc_price_change_24h": 2.5,
            "macro": {"dxy_index": 103},
        },
        current_position=0.0,
    )
    
    assert result.signal == TradeSignal.BUY
    assert result.should_execute == True
    assert result.position_size > 0


def test_signal_generator_circuit_breaker():
    """测试熔断机制"""
    generator = SignalGenerator()
    
    result = generator.generate_signal(
        conviction_score=85.0,  # 高信念分数
        market_data={
            "fear_greed": {"value": 15},  # 但极度恐惧
            "btc_price_change_24h": 2.5,
            "macro": {"dxy_index": 103},
        },
        current_position=0.0,
    )
    
    # 熔断触发,应该HOLD
    assert result.signal == TradeSignal.HOLD
    assert result.should_execute == False
    assert len(result.warnings) > 0


# 更多测试...
```

---

### Phase 2 验收标准

- [ ] ConvictionCalculator正确计算信念分数
- [ ] 权重配置正确 (Macro 40%, OnChain 40%, TA 20%)
- [ ] 风险调整逻辑正确
- [ ] SignalGenerator正确生成交易信号
- [ ] 熔断机制正常工作
- [ ] 仓位计算合理 (0.2%-0.5%)
- [ ] StrategyExecutor编排流程正确
- [ ] ✅ Agent执行结果正确保存到agent_executions表 (通过strategy_execution_id关联)
- [ ] 单元测试覆盖率 > 80%

---

---

## Phase 3: Paper Trading引擎 💰

**目标**: 实现模拟交易执行、投资组合管理和盈亏计算

**工期**: 3-4天

### Task 3.1: Portfolio CRUD Service ⏳

**文件**: `app/services/trading/portfolio_service.py`

```python
"""Portfolio Service - 投资组合CRUD"""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Portfolio, PortfolioHolding
from app.schemas.strategy import PortfolioCreate, PortfolioResponse


class PortfolioService:
    """投资组合服务"""
    
    async def create_portfolio(
        self,
        db: AsyncSession,
        user_id: str,
        portfolio_data: PortfolioCreate
    ) -> Portfolio:
        """创建投资组合"""
        portfolio = Portfolio(
            user_id=user_id,
            name=portfolio_data.name,
            initial_balance=portfolio_data.initial_balance,
            current_balance=portfolio_data.initial_balance,
            total_value=portfolio_data.initial_balance,
            strategy_name=portfolio_data.strategy_name,
        )
        
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)
        
        return portfolio
    
    async def get_portfolio(
        self,
        db: AsyncSession,
        portfolio_id: str
    ) -> Optional[Portfolio]:
        """获取投资组合"""
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_portfolios(
        self,
        db: AsyncSession,
        user_id: str,
        active_only: bool = True
    ) -> List[Portfolio]:
        """获取用户的所有组合"""
        query = select(Portfolio).where(Portfolio.user_id == user_id)
        
        if active_only:
            query = query.where(Portfolio.is_active == True)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_portfolio_value(
        self,
        db: AsyncSession,
        portfolio: Portfolio,
        current_btc_price: Decimal,
        current_eth_price: Optional[Decimal] = None
    ):
        """更新投资组合总价值"""
        # 获取所有持仓
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio.id
            )
        )
        holdings = result.scalars().all()
        
        # 计算持仓市值
        holdings_value = Decimal("0")
        for holding in holdings:
            if holding.symbol == "BTC":
                holding.current_price = current_btc_price
            elif holding.symbol == "ETH" and current_eth_price:
                holding.current_price = current_eth_price
            
            holding.market_value = holding.amount * holding.current_price
            holding.unrealized_pnl = holding.market_value - holding.cost_basis
            holding.unrealized_pnl_percent = (
                float(holding.unrealized_pnl / holding.cost_basis * 100)
                if holding.cost_basis > 0 else 0
            )
            
            holdings_value += holding.market_value
        
        # 更新组合总价值
        portfolio.total_value = portfolio.current_balance + holdings_value
        portfolio.total_pnl = portfolio.total_value - portfolio.initial_balance
        portfolio.total_pnl_percent = (
            float(portfolio.total_pnl / portfolio.initial_balance * 100)
            if portfolio.initial_balance > 0 else 0
        )
        
        await db.commit()


portfolio_service = PortfolioService()
```

---

### Task 3.2: Paper Trading Engine ⏳

**文件**: `app/services/trading/paper_engine.py`

```python
"""Paper Trading Engine - 模拟交易引擎"""

from typing import Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Portfolio, PortfolioHolding, Trade
from app.schemas.strategy import TradeType, TradeCreate


class PaperTradingEngine:
    """
    模拟交易引擎
    
    功能:
    - 执行买入/卖出
    - 更新持仓
    - 计算手续费
    - 记录交易
    - 更新组合状态
    """
    
    # 手续费配置
    FEE_RATE = 0.001  # 0.1% (Binance Spot手续费)
    
    async def execute_trade(
        self,
        db: AsyncSession,
        portfolio_id: str,
        symbol: str,
        trade_type: TradeType,
        amount: Decimal,
        price: Decimal,
        execution_id: Optional[str] = None,
        conviction_score: Optional[float] = None,
        signal_strength: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> Trade:
        """
        执行交易
        
        Args:
            db: 数据库会话
            portfolio_id: 投资组合ID
            symbol: 交易币种 (BTC/ETH)
            trade_type: 交易类型 (BUY/SELL)
            amount: 交易数量
            price: 交易价格
            execution_id: 策略执行ID
            conviction_score: 信念分数
            signal_strength: 信号强度
            reason: 交易原因
            
        Returns:
            Trade: 交易记录
        """
        # 获取组合
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one()
        
        # 计算交易金额和手续费
        total_value = amount * price
        fee = total_value * Decimal(str(self.FEE_RATE))
        
        # 记录交易前状态
        balance_before = portfolio.current_balance
        holding_before = await self._get_holding_amount(db, portfolio_id, symbol)
        
        # 执行交易
        if trade_type == TradeType.BUY:
            trade = await self._execute_buy(
                db=db,
                portfolio=portfolio,
                symbol=symbol,
                amount=amount,
                price=price,
                fee=fee,
            )
        else:  # SELL
            trade = await self._execute_sell(
                db=db,
                portfolio=portfolio,
                symbol=symbol,
                amount=amount,
                price=price,
                fee=fee,
            )
        
        # 记录交易后状态
        balance_after = portfolio.current_balance
        holding_after = await self._get_holding_amount(db, portfolio_id, symbol)
        
        # 创建交易记录
        trade_record = Trade(
            portfolio_id=portfolio_id,
            execution_id=execution_id,
            symbol=symbol,
            trade_type=trade_type,
            amount=amount,
            price=price,
            total_value=total_value,
            fee=fee,
            fee_percent=float(self.FEE_RATE * 100),
            balance_before=balance_before,
            balance_after=balance_after,
            holding_before=holding_before,
            holding_after=holding_after,
            realized_pnl=trade.get("realized_pnl"),
            realized_pnl_percent=trade.get("realized_pnl_percent"),
            conviction_score=conviction_score,
            signal_strength=signal_strength,
            reason=reason,
            executed_at=datetime.utcnow(),
        )
        
        db.add(trade_record)
        
        # 更新组合统计
        portfolio.total_trades += 1
        if trade_record.realized_pnl and trade_record.realized_pnl > 0:
            portfolio.winning_trades += 1
        elif trade_record.realized_pnl and trade_record.realized_pnl < 0:
            portfolio.losing_trades += 1
        
        if portfolio.total_trades > 0:
            portfolio.win_rate = (
                float(portfolio.winning_trades / portfolio.total_trades * 100)
            )
        
        await db.commit()
        await db.refresh(trade_record)
        
        return trade_record
    
    async def _execute_buy(
        self,
        db: AsyncSession,
        portfolio: Portfolio,
        symbol: str,
        amount: Decimal,
        price: Decimal,
        fee: Decimal,
    ) -> dict:
        """执行买入"""
        total_cost = amount * price + fee
        
        # 检查余额
        if portfolio.current_balance < total_cost:
            raise ValueError(f"余额不足: 需要 {total_cost}, 但只有 {portfolio.current_balance}")
        
        # 扣除余额
        portfolio.current_balance -= total_cost
        
        # 更新或创建持仓
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio.id,
                PortfolioHolding.symbol == symbol,
            )
        )
        holding = result.scalar_one_or_none()
        
        if holding:
            # 更新现有持仓
            old_cost = holding.amount * holding.avg_buy_price
            new_cost = amount * price
            total_cost_basis = old_cost + new_cost
            holding.amount += amount
            holding.avg_buy_price = total_cost_basis / holding.amount
            holding.cost_basis = total_cost_basis
        else:
            # 创建新持仓
            holding = PortfolioHolding(
                portfolio_id=portfolio.id,
                symbol=symbol,
                amount=amount,
                avg_buy_price=price,
                current_price=price,
                market_value=amount * price,
                cost_basis=amount * price,
                first_buy_time=datetime.utcnow(),
            )
            db.add(holding)
        
        return {"realized_pnl": None, "realized_pnl_percent": None}
    
    async def _execute_sell(
        self,
        db: AsyncSession,
        portfolio: Portfolio,
        symbol: str,
        amount: Decimal,
        price: Decimal,
        fee: Decimal,
    ) -> dict:
        """执行卖出"""
        # 获取持仓
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio.id,
                PortfolioHolding.symbol == symbol,
            )
        )
        holding = result.scalar_one_or_none()
        
        if not holding:
            raise ValueError(f"没有 {symbol} 持仓")
        
        if holding.amount < amount:
            raise ValueError(
                f"持仓不足: 需要卖出 {amount}, 但只有 {holding.amount}"
            )
        
        # 计算已实现盈亏
        sell_value = amount * price - fee
        cost = amount * holding.avg_buy_price
        realized_pnl = sell_value - cost
        realized_pnl_percent = float(realized_pnl / cost * 100) if cost > 0 else 0
        
        # 增加余额
        portfolio.current_balance += sell_value
        
        # 更新持仓
        holding.amount -= amount
        holding.cost_basis -= cost
        
        if holding.amount == Decimal("0"):
            # 清空持仓
            await db.delete(holding)
        
        return {
            "realized_pnl": realized_pnl,
            "realized_pnl_percent": realized_pnl_percent,
        }
    
    async def _get_holding_amount(
        self,
        db: AsyncSession,
        portfolio_id: str,
        symbol: str
    ) -> Decimal:
        """获取持仓数量"""
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.symbol == symbol,
            )
        )
        holding = result.scalar_one_or_none()
        return holding.amount if holding else Decimal("0")


paper_engine = PaperTradingEngine()
```

---

### Task 3.3: 交易执行流程 ⏳

**文件**: `app/services/trading/trade_executor.py`

```python
"""Trade Executor - 执行完整的交易流程"""

from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.trading.paper_engine import paper_engine
from app.services.trading.portfolio_service import portfolio_service
from app.services.data_collectors.manager import data_manager
from app.schemas.strategy import TradeType


class TradeExecutor:
    """
    交易执行器
    
    完整流程:
    1. 验证交易信号
    2. 获取当前价格
    3. 执行Paper Trading
    4. 更新组合价值
    5. 创建快照 (可选)
    """
    
    async def execute_trade_signal(
        self,
        db: AsyncSession,
        portfolio_id: str,
        signal: str,  # BUY/SELL/HOLD
        position_size: float,  # 0-1
        execution_id: str,
        conviction_score: float,
        signal_strength: float,
        reasons: list,
    ) -> dict:
        """
        执行交易信号
        
        Args:
            db: 数据库会话
            portfolio_id: 投资组合ID
            signal: 交易信号
            position_size: 仓位大小
            execution_id: 策略执行ID
            conviction_score: 信念分数
            signal_strength: 信号强度
            reasons: 交易原因
            
        Returns:
            执行结果字典
        """
        # Step 1: HOLD信号不执行
        if signal == "HOLD":
            return {
                "executed": False,
                "reason": "HOLD信号,无需交易",
            }
        
        # Step 2: 获取组合和当前价格
        portfolio = await portfolio_service.get_portfolio(db, portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # 获取当前BTC价格
        price_data = await data_manager.binance.collect()
        current_price = Decimal(str(price_data["btc"]["price"]))
        
        # Step 3: 计算交易数量
        if signal == "BUY":
            # 买入: position_size * 当前余额 / 当前价格
            buy_amount_usd = portfolio.current_balance * Decimal(str(position_size))
            buy_amount_btc = buy_amount_usd / current_price
            
            if buy_amount_usd < Decimal("10"):  # 最小交易金额
                return {
                    "executed": False,
                    "reason": f"交易金额太小: ${buy_amount_usd:.2f}",
                }
            
            trade = await paper_engine.execute_trade(
                db=db,
                portfolio_id=portfolio_id,
                symbol="BTC",
                trade_type=TradeType.BUY,
                amount=buy_amount_btc,
                price=current_price,
                execution_id=execution_id,
                conviction_score=conviction_score,
                signal_strength=signal_strength,
                reason="; ".join(reasons),
            )
            
            return {
                "executed": True,
                "trade_id": str(trade.id),
                "trade_type": "BUY",
                "amount": float(buy_amount_btc),
                "price": float(current_price),
                "total_value": float(trade.total_value),
                "fee": float(trade.fee),
            }
        
        else:  # SELL
            # 卖出: 卖出所有BTC持仓
            holding_amount = await paper_engine._get_holding_amount(
                db, portfolio_id, "BTC"
            )
            
            if holding_amount == Decimal("0"):
                return {
                    "executed": False,
                    "reason": "没有BTC持仓",
                }
            
            trade = await paper_engine.execute_trade(
                db=db,
                portfolio_id=portfolio_id,
                symbol="BTC",
                trade_type=TradeType.SELL,
                amount=holding_amount,
                price=current_price,
                execution_id=execution_id,
                conviction_score=conviction_score,
                signal_strength=signal_strength,
                reason="; ".join(reasons),
            )
            
            return {
                "executed": True,
                "trade_id": str(trade.id),
                "trade_type": "SELL",
                "amount": float(holding_amount),
                "price": float(current_price),
                "total_value": float(trade.total_value),
                "fee": float(trade.fee),
                "realized_pnl": float(trade.realized_pnl) if trade.realized_pnl else 0,
                "realized_pnl_percent": trade.realized_pnl_percent,
            }
        
        # Step 4: 更新组合价值
        await portfolio_service.update_portfolio_value(
            db=db,
            portfolio=portfolio,
            current_btc_price=current_price,
        )


trade_executor = TradeExecutor()
```

---

### Task 3.4: 集成测试 ⏳

**文件**: `tests/integration/test_paper_trading.py`

```python
"""Test Paper Trading Engine"""

import pytest
from decimal import Decimal

from app.services.trading.paper_engine import paper_engine
from app.services.trading.portfolio_service import portfolio_service
from app.schemas.strategy import TradeType, PortfolioCreate


@pytest.mark.asyncio
async def test_buy_btc(db_session, test_user):
    """测试买入BTC"""
    # 创建组合
    portfolio = await portfolio_service.create_portfolio(
        db=db_session,
        user_id=test_user.id,
        portfolio_data=PortfolioCreate(
            name="测试组合",
            initial_balance=Decimal("10000"),
        )
    )
    
    # 执行买入
    trade = await paper_engine.execute_trade(
        db=db_session,
        portfolio_id=str(portfolio.id),
        symbol="BTC",
        trade_type=TradeType.BUY,
        amount=Decimal("0.1"),
        price=Decimal("45000"),
        reason="测试买入",
    )
    
    assert trade is not None
    assert trade.trade_type == TradeType.BUY
    assert trade.amount == Decimal("0.1")
    assert trade.balance_after < trade.balance_before


@pytest.mark.asyncio
async def test_sell_btc(db_session, test_user):
    """测试卖出BTC"""
    # 创建组合
    portfolio = await portfolio_service.create_portfolio(
        db=db_session,
        user_id=test_user.id,
        portfolio_data=PortfolioCreate(
            name="测试组合",
            initial_balance=Decimal("10000"),
        )
    )
    
    # 先买入
    await paper_engine.execute_trade(
        db=db_session,
        portfolio_id=str(portfolio.id),
        symbol="BTC",
        trade_type=TradeType.BUY,
        amount=Decimal("0.1"),
        price=Decimal("45000"),
    )
    
    # 再卖出
    trade = await paper_engine.execute_trade(
        db=db_session,
        portfolio_id=str(portfolio.id),
        symbol="BTC",
        trade_type=TradeType.SELL,
        amount=Decimal("0.1"),
        price=Decimal("46000"),  # 涨了1000
        reason="测试卖出",
    )
    
    assert trade is not None
    assert trade.trade_type == TradeType.SELL
    assert trade.realized_pnl > 0  # 有盈利


# 更多测试...
```

---

### Phase 3 验收标准

- [ ] Portfolio CRUD功能正常
- [ ] Paper Trading买入功能正常
- [ ] Paper Trading卖出功能正常
- [ ] 持仓更新正确
- [ ] 手续费计算正确 (0.1%)
- [ ] 盈亏计算正确
- [ ] 交易记录完整
- [ ] 余额检查正常
- [ ] 持仓检查正常
- [ ] 集成测试通过

---

---

## Phase 4: 策略调度系统 ⏰

**目标**: 实现定时策略执行和市场数据定期采集

**工期**: 2-3天

### Task 4.1: APScheduler配置 ⏳

**文件**: `app/services/scheduler/scheduler_config.py`

```python
"""APScheduler Configuration"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from app.core.config import settings


# JobStore配置 (使用Redis持久化)
jobstores = {
    'default': RedisJobStore(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
    )
}

# Executor配置
executors = {
    'default': AsyncIOExecutor(),
}

# Job默认配置
job_defaults = {
    'coalesce': True,  # 合并错过的任务
    'max_instances': 1,  # 每个job最多1个实例
    'misfire_grace_time': 300,  # 错过5分钟内的任务仍执行
}

# 创建调度器
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='Asia/Shanghai',
)
```

---

### Task 4.2: 策略执行Jobs ⏳

**文件**: `app/services/scheduler/strategy_jobs.py`

```python
"""Strategy Execution Jobs"""

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.services.decision.strategy_executor import strategy_executor
from app.services.trading.trade_executor import trade_executor
from app.services.trading.portfolio_service import portfolio_service


async def execute_hodl_wave_strategy():
    """
    执行HODL Wave策略
    
    调度: 每4小时执行一次
    """
    print(f"[{datetime.utcnow()}] 开始执行HODL Wave策略...")
    
    async with async_session_maker() as db:
        try:
            # 获取所有激活的组合
            # TODO: 这里需要查询用户表,获取启用策略的用户
            # 暂时硬编码一个测试用户
            test_user_id = "test-user-id"  # 从配置或数据库获取
            
            portfolios = await portfolio_service.get_user_portfolios(
                db=db,
                user_id=test_user_id,
                active_only=True,
            )
            
            for portfolio in portfolios:
                if portfolio.strategy_name != "HODL Wave":
                    continue
                
                print(f"  执行Portfolio: {portfolio.name} ({portfolio.id})")
                
                # Step 1: 执行策略分析
                strategy_result = await strategy_executor.execute_strategy(
                    user_id=test_user_id,
                    strategy_name="HODL Wave",
                    db=db,
                    current_position=0.0,  # TODO: 计算当前仓位
                )
                
                signal_output = strategy_result["signal"]
                
                print(f"    Signal: {signal_output['signal']}")
                print(f"    Conviction: {strategy_result['conviction']['score']:.1f}")
                print(f"    Should Execute: {signal_output['should_execute']}")
                
                # Step 2: 执行交易 (如果需要)
                if signal_output["should_execute"]:
                    trade_result = await trade_executor.execute_trade_signal(
                        db=db,
                        portfolio_id=str(portfolio.id),
                        signal=signal_output["signal"],
                        position_size=signal_output["position_size"],
                        execution_id=strategy_result["execution_id"],
                        conviction_score=strategy_result["conviction"]["score"],
                        signal_strength=signal_output["signal_strength"],
                        reasons=signal_output["reasons"],
                    )
                    
                    if trade_result["executed"]:
                        print(f"    ✅ 交易执行成功: {trade_result}")
                    else:
                        print(f"    ⏸️ 交易未执行: {trade_result['reason']}")
                else:
                    print(f"    ⏸️ 无需交易: {signal_output['reasons']}")
            
            print(f"[{datetime.utcnow()}] HODL Wave策略执行完成\n")
            
        except Exception as e:
            print(f"[{datetime.utcnow()}] ❌ 策略执行失败: {e}")
            import traceback
            traceback.print_exc()


async def collect_market_data():
    """
    采集市场数据
    
    调度: 每5分钟执行一次
    """
    print(f"[{datetime.utcnow()}] 采集市场数据...")
    
    try:
        from app.services.data_collectors.manager import data_manager
        
        snapshot = await data_manager.collect_all()
        
        print(f"  BTC: ${snapshot.btc_price.price:,.2f}")
        print(f"  Fear & Greed: {snapshot.fear_greed.value if snapshot.fear_greed else 'N/A'}")
        
    except Exception as e:
        print(f"❌ 数据采集失败: {e}")


async def create_portfolio_snapshots():
    """
    创建投资组合快照
    
    调度: 每天0点执行
    """
    print(f"[{datetime.utcnow()}] 创建组合快照...")
    
    async with async_session_maker() as db:
        try:
            # TODO: 实现快照逻辑
            pass
        except Exception as e:
            print(f"❌ 快照创建失败: {e}")
```

---

### Task 4.3: 调度器启动 ⏳

**文件**: `app/services/scheduler/scheduler.py`

```python
"""Scheduler Manager"""

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.scheduler.scheduler_config import scheduler
from app.services.scheduler.strategy_jobs import (
    execute_hodl_wave_strategy,
    collect_market_data,
    create_portfolio_snapshots,
)


def start_scheduler():
    """启动调度器"""
    
    # 1. HODL Wave策略 - 每4小时执行
    scheduler.add_job(
        execute_hodl_wave_strategy,
        trigger=IntervalTrigger(hours=4),
        id='hodl_wave_strategy',
        name='HODL Wave Strategy Execution',
        replace_existing=True,
    )
    
    # 2. 市场数据采集 - 每5分钟执行
    scheduler.add_job(
        collect_market_data,
        trigger=IntervalTrigger(minutes=5),
        id='collect_market_data',
        name='Market Data Collection',
        replace_existing=True,
    )
    
    # 3. 组合快照 - 每天0点执行
    scheduler.add_job(
        create_portfolio_snapshots,
        trigger=CronTrigger(hour=0, minute=0),
        id='create_snapshots',
        name='Portfolio Snapshots',
        replace_existing=True,
    )
    
    # 启动调度器
    scheduler.start()
    print("✅ APScheduler started")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown()
    print("✅ APScheduler shutdown")
```

---

### Task 4.4: 集成到FastAPI ⏳

**文件**: `app/main.py` (更新)

```python
"""FastAPI Application"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

# ... 其他导入 ...
from app.services.scheduler.scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 Starting AutoMoney Backend...")
    
    # 启动调度器
    start_scheduler()
    
    yield
    
    # 关闭时
    print("👋 Shutting down AutoMoney Backend...")
    
    # 关闭调度器
    shutdown_scheduler()


app = FastAPI(
    title="AutoMoney API",
    version="2.0.0",
    lifespan=lifespan,
)

# ... 其他配置 ...
```

---

### Task 4.5: Redis配置 ⏳

**更新**: `.env` 和 `docker-compose.yml`

**.env添加:**
```env
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**docker-compose.yml添加:**
```yaml
services:
  # ... 其他服务 ...
  
  redis:
    image: redis:7-alpine
    container_name: automoney_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  # ... 其他volumes ...
  redis_data:
```

---

### Phase 4 验收标准

- [ ] APScheduler正确配置
- [ ] Redis JobStore正常工作
- [ ] HODL Wave策略按时执行 (每4小时)
- [ ] 市场数据定期采集 (每5分钟)
- [ ] 组合快照定期创建 (每天0点)
- [ ] 调度器随应用启动/关闭
- [ ] 分布式锁机制正常 (同一job不重复执行)
- [ ] 错过的任务处理正确

---

---

## Phase 5: API和前端集成 🌐

**目标**: 创建RESTful API端点,前端集成WebSocket实时推送

**工期**: 3-4天

### Task 5.1: Portfolio API端点 ⏳

**文件**: `app/api/v1/endpoints/portfolio.py`

```python
"""Portfolio API Endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import User
from app.services.trading.portfolio_service import portfolio_service
from app.schemas.strategy import (
    PortfolioCreate,
    PortfolioResponse,
    HoldingResponse,
    TradeResponse,
    PortfolioSnapshotResponse,
)


router = APIRouter()


@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建投资组合"""
    portfolio = await portfolio_service.create_portfolio(
        db=db,
        user_id=str(current_user.id),
        portfolio_data=portfolio_data,
    )
    return portfolio


@router.get("/", response_model=List[PortfolioResponse])
async def get_portfolios(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的所有投资组合"""
    portfolios = await portfolio_service.get_user_portfolios(
        db=db,
        user_id=str(current_user.id),
        active_only=active_only,
    )
    return portfolios


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个投资组合"""
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return portfolio


@router.get("/{portfolio_id}/holdings", response_model=List[HoldingResponse])
async def get_holdings(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取投资组合的持仓"""
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return portfolio.holdings


@router.get("/{portfolio_id}/trades", response_model=List[TradeResponse])
async def get_trades(
    portfolio_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取交易记录"""
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 按时间倒序返回最近的交易
    trades = sorted(
        portfolio.trades,
        key=lambda t: t.executed_at,
        reverse=True
    )[offset:offset+limit]
    
    return trades
```

---

### Task 5.2: Strategy Execution API ⏳

**文件**: `app/api/v1/endpoints/strategy.py`

```python
"""Strategy Execution API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import User
from app.services.decision.strategy_executor import strategy_executor
from app.services.trading.trade_executor import trade_executor
from app.services.trading.portfolio_service import portfolio_service


router = APIRouter()


@router.post("/execute")
async def execute_strategy_manual(
    portfolio_id: str,
    strategy_name: str = "HODL Wave",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    手动执行策略
    
    用于测试和手动触发策略执行
    """
    # 验证组合权限
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 执行策略
    try:
        strategy_result = await strategy_executor.execute_strategy(
            user_id=str(current_user.id),
            strategy_name=strategy_name,
            db=db,
            current_position=0.0,  # TODO: 计算实际仓位
        )
        
        signal_output = strategy_result["signal"]
        
        # 如果应该执行交易
        trade_result = None
        if signal_output["should_execute"]:
            trade_result = await trade_executor.execute_trade_signal(
                db=db,
                portfolio_id=portfolio_id,
                signal=signal_output["signal"],
                position_size=signal_output["position_size"],
                execution_id=strategy_result["execution_id"],
                conviction_score=strategy_result["conviction"]["score"],
                signal_strength=signal_output["signal_strength"],
                reasons=signal_output["reasons"],
            )
        
        return {
            "success": True,
            "execution_id": strategy_result["execution_id"],
            "conviction_score": strategy_result["conviction"]["score"],
            "signal": signal_output["signal"],
            "should_execute": signal_output["should_execute"],
            "trade_result": trade_result,
            "reasons": signal_output["reasons"],
            "warnings": signal_output["warnings"],
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Task 5.3: 前端Portfolio页面 ⏳

**文件**: `AMfrontend/src/pages/Portfolio.tsx`

```typescript
/**
 * Portfolio页面 - 显示投资组合和交易记录
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Portfolio {
  id: string;
  name: string;
  total_value: number;
  current_balance: number;
  total_pnl: number;
  total_pnl_percent: number;
  total_trades: number;
  win_rate: number;
}

interface Trade {
  id: string;
  symbol: string;
  trade_type: string;
  amount: number;
  price: number;
  total_value: number;
  realized_pnl?: number;
  realized_pnl_percent?: number;
  executed_at: string;
}

export default function Portfolio() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    try {
      const response = await axios.get('/api/v1/portfolio/', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      setPortfolios(response.data);
      
      if (response.data.length > 0) {
        selectPortfolio(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to load portfolios:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectPortfolio = async (portfolio: Portfolio) => {
    setSelectedPortfolio(portfolio);
    
    // 加载交易记录
    try {
      const response = await axios.get(
        `/api/v1/portfolio/${portfolio.id}/trades`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      setTrades(response.data);
    } catch (error) {
      console.error('Failed to load trades:', error);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">投资组合</h1>

      {/* 组合列表 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {portfolios.map((portfolio) => (
          <div
            key={portfolio.id}
            onClick={() => selectPortfolio(portfolio)}
            className={`p-4 border rounded-lg cursor-pointer hover:shadow-lg transition ${
              selectedPortfolio?.id === portfolio.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300'
            }`}
          >
            <h3 className="font-bold text-lg mb-2">{portfolio.name}</h3>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-600">总价值:</span>
                <span className="font-semibold">
                  ${portfolio.total_value.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">盈亏:</span>
                <span
                  className={`font-semibold ${
                    portfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  ${portfolio.total_pnl.toFixed(2)} (
                  {portfolio.total_pnl_percent.toFixed(2)}%)
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">胜率:</span>
                <span>{portfolio.win_rate.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 交易记录 */}
      {selectedPortfolio && (
        <div>
          <h2 className="text-2xl font-bold mb-4">交易记录</h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    时间
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    类型
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    币种
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    数量
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    价格
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    盈亏
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {trades.map((trade) => (
                  <tr key={trade.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(trade.executed_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          trade.trade_type === 'BUY'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {trade.trade_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {trade.amount.toFixed(8)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      ${trade.price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      {trade.realized_pnl !== undefined && (
                        <span
                          className={`font-semibold ${
                            trade.realized_pnl >= 0
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}
                        >
                          ${trade.realized_pnl.toFixed(2)} (
                          {trade.realized_pnl_percent?.toFixed(2)}%)
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### Phase 5 验收标准

- [ ] Portfolio API端点正常工作
- [ ] Strategy Execution API正常工作
- [ ] 前端可以查看投资组合
- [ ] 前端可以查看交易记录
- [ ] 前端可以手动触发策略执行
- [ ] 盈亏显示正确
- [ ] 交易记录分页正常
- [ ] 权限控制正确 (用户只能看自己的组合)

---

---

## Phase 6: 测试和优化 🧪

**目标**: 完整测试、性能优化、文档完善

**工期**: 2-3天

### Task 6.1: 端到端测试 ⏳

**文件**: `tests/e2e/test_strategy_flow.py`

```python
"""End-to-End Strategy Flow Test"""

import pytest
from decimal import Decimal

from app.services.decision.strategy_executor import strategy_executor
from app.services.trading.trade_executor import trade_executor
from app.services.trading.portfolio_service import portfolio_service
from app.schemas.strategy import PortfolioCreate


@pytest.mark.asyncio
async def test_complete_strategy_flow(db_session, test_user):
    """
    测试完整的策略执行流程
    
    1. 创建投资组合
    2. 执行策略分析
    3. 执行交易
    4. 验证结果
    """
    # Step 1: 创建组合
    portfolio = await portfolio_service.create_portfolio(
        db=db_session,
        user_id=test_user.id,
        portfolio_data=PortfolioCreate(
            name="测试组合",
            initial_balance=Decimal("10000"),
            strategy_name="HODL Wave",
        )
    )
    
    assert portfolio.current_balance == Decimal("10000")
    
    # Step 2: 执行策略
    strategy_result = await strategy_executor.execute_strategy(
        user_id=test_user.id,
        strategy_name="HODL Wave",
        db=db_session,
        current_position=0.0,
    )
    
    assert "conviction" in strategy_result
    assert "signal" in strategy_result
    assert 0 <= strategy_result["conviction"]["score"] <= 100
    
    # Step 3: 执行交易 (如果信号是BUY且应该执行)
    signal_output = strategy_result["signal"]
    
    if signal_output["signal"] == "BUY" and signal_output["should_execute"]:
        trade_result = await trade_executor.execute_trade_signal(
            db=db_session,
            portfolio_id=str(portfolio.id),
            signal=signal_output["signal"],
            position_size=signal_output["position_size"],
            execution_id=strategy_result["execution_id"],
            conviction_score=strategy_result["conviction"]["score"],
            signal_strength=signal_output["signal_strength"],
            reasons=signal_output["reasons"],
        )
        
        assert trade_result["executed"] == True
        assert trade_result["trade_type"] == "BUY"
        
        # 验证组合余额减少
        await db_session.refresh(portfolio)
        assert portfolio.current_balance < Decimal("10000")


# 更多测试...
```

---

### Task 6.2: 性能测试 ⏳

**文件**: `tests/load/test_strategy_performance.py`

```python
"""Strategy Performance Test"""

import asyncio
import time
from statistics import mean, stdev


async def test_strategy_execution_performance():
    """测试策略执行性能"""
    
    execution_times = []
    
    for i in range(10):
        start = time.time()
        
        # 执行策略
        # TODO: 调用strategy_executor.execute_strategy
        
        end = time.time()
        execution_times.append(end - start)
    
    avg_time = mean(execution_times)
    std_time = stdev(execution_times)
    
    print(f"平均执行时间: {avg_time:.2f}s")
    print(f"标准差: {std_time:.2f}s")
    
    # 性能要求: 平均执行时间 < 30秒
    assert avg_time < 30


# 更多性能测试...
```

---

### Task 6.3: API文档 ⏳

**文件**: `docs/API_STRATEGY.md`

````markdown
# 策略和交易API文档

## 投资组合API

### 创建投资组合

```http
POST /api/v1/portfolio/
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "我的策略组合",
  "initial_balance": 10000.0,
  "strategy_name": "HODL Wave"
}
```

### 获取投资组合列表

```http
GET /api/v1/portfolio/
Authorization: Bearer <token>
```

### 获取持仓

```http
GET /api/v1/portfolio/{portfolio_id}/holdings
Authorization: Bearer <token>
```

### 获取交易记录

```http
GET /api/v1/portfolio/{portfolio_id}/trades?limit=50&offset=0
Authorization: Bearer <token>
```

## 策略执行API

### 手动执行策略

```http
POST /api/v1/strategy/execute
Content-Type: application/json
Authorization: Bearer <token>

{
  "portfolio_id": "xxx-xxx-xxx",
  "strategy_name": "HODL Wave"
}
```

Response:
```json
{
  "success": true,
  "execution_id": "xxx",
  "conviction_score": 75.5,
  "signal": "BUY",
  "should_execute": true,
  "trade_result": {
    "executed": true,
    "trade_id": "xxx",
    "trade_type": "BUY",
    "amount": 0.05,
    "price": 45000.0,
    "total_value": 2250.0
  },
  "reasons": ["强烈看多 (信念分数: 75.5/100)"],
  "warnings": []
}
```
````

---

### Task 6.4: 用户文档 ⏳

**文件**: `docs/USER_GUIDE_STRATEGY.md`

````markdown
# 策略系统用户指南

## 1. 什么是HODL Wave策略?

HODL Wave是基于Multi-Agent系统的自动化投资策略,通过分析:
- **宏观经济**: 利率、货币供应、美元强度、市场情绪
- **技术分析**: RSI, MACD, EMA, 布林带
- **链上数据**: 网络活跃度、交易费用、NVT比率

生成**信念分数** (0-100),自动执行买入/卖出/持币决策。

## 2. 如何使用?

### 2.1 创建投资组合

1. 进入"投资组合"页面
2. 点击"创建组合"
3. 输入名称和初始余额 (推荐$10,000起)
4. 选择策略: HODL Wave
5. 点击创建

### 2.2 策略自动执行

策略会**每4小时**自动执行:
1. 采集实时市场数据
2. 调用3个AI Agent分析
3. 计算信念分数 (0-100)
4. 生成交易信号 (BUY/SELL/HOLD)
5. 如果满足条件,自动执行交易

### 2.3 查看结果

在"投资组合"页面可以查看:
- 当前余额和持仓
- 累计盈亏和盈亏率
- 交易记录和胜率
- 策略执行历史

## 3. 策略规则

### 3.1 信念分数

| 分数范围 | 信号 | 操作 |
|---------|------|------|
| 0-30 | SELL | 卖出所有持仓 |
| 30-45 | HOLD | 持币观望 (偏空) |
| 45-55 | HOLD | 持币观望 (中性) |
| 55-70 | HOLD | 持币观望 (偏多) |
| 70-100 | BUY | 买入 (仓位0.2%-0.5%) |

### 3.2 熔断机制

以下情况**暂停交易**:
- ❌ 极度恐惧 (Fear & Greed < 20)
- ❌ 美元极强 (DXY > 115)
- ❌ 极度波动 (24h价格变化 > 15%)

### 3.3 风险控制

- 单次买入: 最多0.5%资金
- 手续费: 0.1% (模拟Binance手续费)
- 止损: 信念分数 < 30时自动卖出

## 4. 常见问题

### Q: 策略多久执行一次?
A: 每4小时自动执行一次,无需手动操作。

### Q: 可以修改仓位大小吗?
A: 目前仓位由策略自动决定 (0.2%-0.5%),后续版本将支持自定义。

### Q: 什么时候会买入?
A: 当信念分数 >= 70 且未触发熔断时,会自动买入。

### Q: 什么时候会卖出?
A: 当信念分数 < 30 时,会卖出所有持仓。

### Q: 盈亏如何计算?
A: 盈亏 = (当前总价值 - 初始余额) / 初始余额 × 100%

## 5. 风险提示

⚠️ **重要提示**:
1. 这是**模拟交易**系统,使用虚拟资金
2. 策略基于历史数据,**不保证未来收益**
3. 加密货币市场**高风险**,请谨慎投资
4. 正式投资前请充分了解风险
````

---

### Phase 6 验收标准

- [ ] 端到端测试通过
- [ ] 性能测试通过 (执行时间 < 30s)
- [ ] API文档完整
- [ ] 用户文档完整
- [ ] 代码注释完善
- [ ] 没有明显bug
- [ ] 所有API响应时间 < 3s
- [ ] 数据库查询优化完成

---

---

## 📋 总体进度追踪

### Phase进度总览

| Phase | 任务数 | 已完成 | 进行中 | 未开始 | 状态 |
|-------|-------|--------|--------|--------|------|
| Phase 1: 数据库设计 | 6 | 0 | 0 | 6 | ⏳ 未开始 |
| Phase 2: 决策引擎 | 4 | 0 | 0 | 4 | ⏳ 未开始 |
| Phase 3: Paper Trading | 4 | 0 | 0 | 4 | ⏳ 未开始 |
| Phase 4: 策略调度 | 5 | 0 | 0 | 5 | ⏳ 未开始 |
| Phase 5: API集成 | 3 | 0 | 0 | 3 | ⏳ 未开始 |
| Phase 6: 测试优化 | 4 | 0 | 0 | 4 | ⏳ 未开始 |
| **总计** | **26** | **0** | **0** | **26** | **0%** |

---

## 🗓️ 开发时间表

| 周次 | 日期 | 工作内容 | 交付物 |
|-----|------|---------|--------|
| Week 1 | Day 1-3 | Phase 1: 数据库设计 | 6个表 + 迁移脚本 + Models |
| Week 1 | Day 4-7 | Phase 2: 决策引擎 | Conviction + Signal + Executor |
| Week 2 | Day 8-11 | Phase 3: Paper Trading | Portfolio + Trading Engine |
| Week 2 | Day 12-14 | Phase 4: 策略调度 | APScheduler + Jobs |
| Week 3 | Day 15-17 | Phase 5: API集成 | API端点 + 前端页面 |
| Week 3 | Day 18-20 | Phase 6: 测试优化 | 测试 + 文档 + 优化 |

---

## 🎯 关键里程碑

### Milestone 1: 数据层完成 (Day 3)
- ✅ 6个数据表创建
- ✅ 数据模型验证通过
- ✅ 可以保存策略执行和交易记录

### Milestone 2: 决策层完成 (Day 7)
- ✅ ConvictionCalculator工作正常
- ✅ SignalGenerator生成正确信号
- ✅ 可以完整执行策略分析流程

### Milestone 3: 交易层完成 (Day 11)
- ✅ Paper Trading买卖功能正常
- ✅ 盈亏计算正确
- ✅ 投资组合管理完善

### Milestone 4: 自动化完成 (Day 14)
- ✅ 策略自动执行 (每4小时)
- ✅ 数据自动采集 (每5分钟)
- ✅ 调度器稳定运行

### Milestone 5: 产品化完成 (Day 17)
- ✅ 前端可以查看组合和交易
- ✅ 用户可以手动触发策略
- ✅ API完整可用

### Milestone 6: 上线准备 (Day 20)
- ✅ 所有测试通过
- ✅ 文档完整
- ✅ 性能优化完成
- ✅ 可以正式发布

---

## ⚠️ 风险和依赖

### 技术风险

1. **APScheduler稳定性** - 需要充分测试定时任务
2. **数据库性能** - 大量历史数据可能影响查询速度
3. **LLM调用延迟** - Agent分析可能需要10-20秒

### 外部依赖

1. **Redis** - APScheduler JobStore需要Redis
2. **Market Data APIs** - 数据采集依赖外部API稳定性
3. **LLM APIs** - Agent分析依赖Tuzi/OpenRouter

### 缓解措施

1. Redis配置持久化,防止任务丢失
2. 实现数据缓存机制,减少API调用
3. 设置合理的超时和重试机制
4. 数据库索引优化
5. 分页查询大数据集

---

## 📊 成功指标

### 功能指标

- [ ] 策略执行成功率 > 95%
- [ ] 交易执行成功率 > 99%
- [ ] 数据采集成功率 > 98%
- [ ] API响应时间 < 3s

### 性能指标

- [ ] 策略执行时间 < 30s
- [ ] 数据库查询 < 500ms
- [ ] 前端页面加载 < 2s

### 质量指标

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试覆盖率 > 70%
- [ ] 0个P0 bug
- [ ] < 5个P1 bug

---

## 📚 相关文档

- `PROGRESS.md` - 项目总进度
- `DATA_API_TODO.md` - 数据API对接记录
- `architecture-v2/` - 架构设计文档
- `BACKEND_CONVERSATION_ARCHITECTURE.md` - 对话持久化架构
- `API_STRATEGY.md` - API文档 (待创建)
- `USER_GUIDE_STRATEGY.md` - 用户指南 (待创建)

---

## 💡 后续优化方向

### Phase 7: 高级功能 (P2优先级)

1. **多策略支持**
   - DCA (定投)策略
   - Grid Trading (网格交易)
   - Momentum (动量)策略

2. **风险管理增强**
   - 动态止损
   - 最大回撤控制
   - 仓位管理优化

3. **性能分析**
   - 夏普比率计算
   - 最大回撤分析
   - 与BTC持有对比

4. **策略回测**
   - 历史数据回测
   - 策略参数优化
   - 性能评估报告

5. **WebSocket实时推送** (可选)
   - 实时推送策略执行结果
   - 实时推送交易通知
   - 实时更新组合净值

---

---

## 管理员功能 (Admin Feature) ✅

**状态**: ✅ 已完成 (2025-11-06)
**优先级**: P1
**开发时间**: 1天

### 功能概述

实现了管理员权限系统和策略管理功能，允许管理员用户查看和管理所有用户的策略。

### 后端实现

#### 1. 用户角色系统

**文件**: [app/models/user.py:18](app/models/user.py#L18)

在User模型中添加了role字段：
- 默认值: `"user"`
- 可选值: `"user"` | `"admin"`
- 索引: 已创建role字段索引以优化查询
- 权限控制: 通过role字段实现基于角色的访问控制(RBAC)

**数据库迁移**: [alembic/versions/45a7e756d0a8_add_role_field_to_user_model.py](alembic/versions/45a7e756d0a8_add_role_field_to_user_model.py)

迁移脚本采用三步法处理现有数据：
1. 添加nullable列并设置server_default='user'
2. 更新现有NULL值为'user'
3. 修改列为NOT NULL并移除server_default

**管理员权限中间件**: [app/core/deps.py:156-176](app/core/deps.py#L156-L176)

创建了`get_current_admin_user()`依赖函数：
- 验证用户是否具有admin角色
- 如果不是admin则返回403 Forbidden错误
- 用于保护管理员专用的API端点

#### 2. 管理员API端点

**文件**: [app/api/v1/endpoints/admin.py](app/api/v1/endpoints/admin.py)

创建了两个管理员API端点：

**GET /api/v1/admin/strategies** - 获取所有策略列表
- 返回系统中所有用户的策略(Portfolio)
- 包含统计信息: total_value, total_pnl, is_active等
- 按创建时间降序排列
- 仅管理员可访问

**PATCH /api/v1/admin/strategies/{portfolio_id}/toggle** - 切换策略状态
- 允许管理员启用/禁用任何用户的策略
- 更新Portfolio的is_active字段
- 记录操作日志(admin邮箱 + 策略ID + 状态变化)
- 仅管理员可访问

**Schemas**: [app/schemas/admin.py](app/schemas/admin.py)

定义了管理员功能的数据模型：
- `AdminStrategyItem` - 策略条目信息
- `AdminStrategyListResponse` - 策略列表响应
- `StrategyToggleRequest` - 切换请求
- `StrategyToggleResponse` - 切换响应

**路由注册**: [app/api/v1/api.py:5,53-57](app/api/v1/api.py#L5,L53-L57)

在API路由中注册了admin路由：
- 前缀: `/admin`
- 标签: `["admin"]`

### 前端实现

#### 1. Admin API Service

**文件**: [AMfrontend/src/lib/adminApi.ts](AMfrontend/src/lib/adminApi.ts)

创建了管理员API调用服务：
- `fetchAllStrategies()` - 获取所有策略
- `toggleStrategy(strategyId, isActive)` - 切换策略状态
- 使用统一的apiClient，自动添加Firebase Token

#### 2. Admin Panel组件

**文件**: [AMfrontend/src/components/AdminPanel.tsx](AMfrontend/src/components/AdminPanel.tsx)

实现了完整的管理员面板UI：

**功能特性**:
- 📊 统计卡片: 总策略数、活跃策略数、总价值、总盈亏
- 📋 策略列表表格: 显示所有策略详细信息
- 🔄 实时切换: Switch开关控制策略启用/禁用
- 🔒 权限验证: 非管理员显示"Access Denied"页面
- ⚡ 加载状态: 显示加载动画和错误提示
- 🎨 现代UI: 使用Tailwind CSS + shadcn/ui组件

**表格列**:
- Strategy Name - 策略名称
- User ID - 用户ID
- Type - 策略类型(badge)
- Status - 状态(Active/Inactive badge)
- Total Value - 总价值
- P&L - 盈亏金额
- P&L % - 盈亏百分比
- Actions - 操作(Switch切换)

#### 3. 导航集成

**文件**: [AMfrontend/src/App.tsx](AMfrontend/src/App.tsx)

更新了主应用以支持管理员功能：

**导入和状态管理**: Lines 1-13
- 导入AdminPanel组件和Shield图标
- 导入getCurrentUser API函数
- 添加useState和useEffect hooks

**Navigation组件更新**: Lines 42-78
- 添加`isAdmin`状态变量
- useEffect中调用getCurrentUser()检查用户角色
- 仅当`isAdmin === true`时显示Admin按钮
- Admin按钮使用紫色渐变主题

**NavButton组件更新**: Lines 80-120
- 添加`color`属性支持(blue/emerald/purple)
- 为Admin按钮添加purple配色方案

**路由配置**: Line 184
- 添加`/admin`路由指向AdminPanel组件

### 使用说明

#### 设置管理员权限

直接在数据库中修改用户role字段：

```sql
UPDATE "user" SET role = 'admin' WHERE email = 'admin@example.com';
```

当前测试管理员账户：
- Email: `yeheai9906@gmail.com`
- Role: `admin`

#### 访问管理员面板

1. 使用管理员账户登录
2. 导航栏会显示紫色"Admin"按钮
3. 点击进入管理员面板
4. 查看所有策略统计和列表
5. 使用Switch开关启用/禁用策略

#### 权限验证

- ✅ 管理员用户: 可以访问管理员面板，查看和管理所有策略
- ❌ 普通用户: 导航栏不显示Admin按钮，访问/admin会显示403错误

### 相关文件清单

**后端文件**:
- `app/models/user.py` - User模型(role字段)
- `alembic/versions/45a7e756d0a8_add_role_field_to_user_model.py` - 数据库迁移
- `app/core/deps.py` - 管理员权限中间件
- `app/api/v1/endpoints/admin.py` - Admin API端点
- `app/schemas/admin.py` - Admin数据schemas
- `app/api/v1/api.py` - API路由注册

**前端文件**:
- `AMfrontend/src/lib/adminApi.ts` - Admin API服务
- `AMfrontend/src/components/AdminPanel.tsx` - Admin面板组件
- `AMfrontend/src/App.tsx` - 应用主文件(导航和路由)

### Bug修复记录

在实现管理员功能过程中修复了以下预存bug：

#### 1. Research.py参数错误
**文件**: [app/api/v1/endpoints/research.py:34-36,55-56](app/api/v1/endpoints/research.py#L34-L36,L55-L56)
- **问题**: `current_user: Optional[User] = None`不是有效的FastAPI参数定义
- **修复**: 移除参数，设置`user_id = None`

#### 2. Marketplace.py导入错误
**文件**: [app/api/v1/endpoints/marketplace.py:8](app/api/v1/endpoints/marketplace.py#L8)
- **问题**: 从不存在的`app.core.database`导入
- **修复**: 改为从`app.core.deps`导入

### 测试状态

✅ 后端服务器运行正常(端口8000)
✅ 管理员用户角色已设置
✅ 测试数据已准备(2个portfolios)
✅ Admin API端点正常工作
✅ 前端管理员面板正常显示
✅ 权限控制验证通过

---

最后更新: 2025-11-06 23:45

