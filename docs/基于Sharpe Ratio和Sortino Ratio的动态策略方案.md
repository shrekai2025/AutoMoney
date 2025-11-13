# 基于 Sharpe Ratio 和 Sortino Ratio 的动态策略方案

> **版本**: v1.0
> **日期**: 2025-11-07
> **作者**: AutoMoney Strategy Team
> **状态**: 设计方案 (待实现)

---

## 📋 目录

1. [方案概述](#方案概述)
2. [核心理念](#核心理念)
3. [三大应用方案](#三大应用方案)
4. [技术架构](#技术架构)
5. [实现步骤](#实现步骤)
6. [性能指标详解](#性能指标详解)
7. [测试与验证](#测试与验证)
8. [风险与限制](#风险与限制)
9. [未来优化方向](#未来优化方向)

---

## 🎯 方案概述

### 问题背景

当前 AutoMoney 投资策略存在以下局限：

1. **静态权重**: Agent 权重固定（Macro 40%, OnChain 40%, TA 20%），无法适应策略表现变化
2. **固定仓位**: 不论策略盈亏，仓位管理逻辑不变
3. **缺乏反馈**: Sharpe/Sortino Ratio 只用于展示，未参与决策
4. **风险盲区**: 策略连续亏损时仍保持激进

### 解决方案

将 **Sharpe Ratio** 和 **Sortino Ratio** 从静态展示指标升级为**动态决策因子**，构建**风险调整后的自适应策略系统**。

### 核心价值

- 📉 **策略表现不佳时**: 自动降低仓位、提高决策阈值，保护资金
- 📈 **策略表现优秀时**: 适度提高激进度，放大收益
- 🔄 **持续优化**: 基于历史表现动态调整 Agent 权重
- 🛡️ **风险可控**: 通过多重风险指标综合调整

---

## 💡 核心理念

### 设计哲学

> **"让策略的过去表现，指导未来决策"**

传统量化策略往往忽视自身表现反馈，本方案通过引入**策略元认知**机制：

```
当前市场信号 (Agents)
         ↓
   Conviction 计算
         ↓
+ 策略历史表现 (Sharpe/Sortino) ← 🆕 反馈回路
         ↓
    最终决策
```

### 关键指标

#### Sharpe Ratio (夏普比率)

**定义**:
```
Sharpe Ratio = (策略收益率 - 无风险收益率) / 策略收益率标准差
```

**解读**:
- `< 0`: 策略亏损，比无风险资产还差
- `0 - 1`: 表现一般，收益勉强覆盖风险
- `1 - 2`: 表现良好，风险收益比合理
- `> 2`: 表现优秀，高收益低波动

**局限**: 同时惩罚上涨和下跌的波动

---

#### Sortino Ratio (索提诺比率)

**定义**:
```
Sortino Ratio = (策略收益率 - 目标收益率) / 下行标准差
```

**解读**:
- 只关注**下行风险**（负收益的波动）
- 更符合投资者心理：不惩罚上涨波动
- 通常 Sortino > Sharpe，更友好

**优势**:
- 区分"好波动"（上涨）和"坏波动"（下跌）
- 更适合加密货币等高波动资产

---

## 🚀 三大应用方案

### 方案 1: 风险调整的 Conviction 计算 ⭐⭐⭐⭐⭐

**推荐指数**: ★★★★★
**难度**: 中等
**效果**: 立竿见影

#### 实现原理

在 Conviction Score 计算的最后一步，乘以**策略表现调整因子**：

```python
# 原始逻辑
conviction_score = (weighted_score + 100) / 2

# 新逻辑
performance_factor = calculate_performance_factor(sharpe, sortino, max_dd, win_rate)
conviction_score = (weighted_score * performance_factor + 100) / 2
```

#### 调整规则

| Sharpe Ratio | Sortino Ratio | Max Drawdown | Win Rate | 调整因子 | 说明 |
|-------------|--------------|--------------|----------|---------|------|
| < 0 | < 0 | > 20% | < 40% | 0.60-0.70 | 策略严重亏损，大幅保守 |
| 0-1 | 0-1.5 | 15-20% | 40-50% | 0.85-0.95 | 表现平庸，略微保守 |
| 1-2 | 1.5-3 | 10-15% | 50-60% | 1.00 | 表现正常，维持不变 |
| > 2 | > 3 | < 10% | > 60% | 1.05-1.10 | 表现优异，适度激进 |

#### 代码实现

```python
# app/services/decision/conviction_calculator.py

class ConvictionCalculator:

    def calculate(
        self,
        input_data: ConvictionInput,
        custom_weights: Optional[Dict[str, float]] = None,
        portfolio_metrics: Optional[Dict[str, float]] = None  # 🆕
    ) -> ConvictionResult:
        # ... 原有计算逻辑 (Step 1-6) ...

        # Step 7: 🆕 策略表现调整
        if portfolio_metrics:
            performance_factor = self._calculate_performance_factor(
                portfolio_metrics
            )
            adjusted_score = adjusted_score * performance_factor

        # Step 8: 归一化到 0-100
        normalized_score = (adjusted_score + 100) / 2
        final_score = max(0, min(100, normalized_score))

        return ConvictionResult(...)

    def _calculate_performance_factor(
        self,
        metrics: Dict[str, float]
    ) -> float:
        """
        基于历史表现计算调整因子

        Args:
            metrics: {
                'sharpe_ratio': float,
                'sortino_ratio': float,
                'max_drawdown': float,
                'win_rate': float
            }

        Returns:
            float: 调整因子 (0.6 - 1.2)
        """
        sharpe = metrics.get('sharpe_ratio', 0)
        sortino = metrics.get('sortino_ratio', 0)
        max_dd = metrics.get('max_drawdown', 0)
        win_rate = metrics.get('win_rate', 0.5)

        factor = 1.0

        # 1. Sharpe Ratio 主要调整
        if sharpe < 0:
            factor *= 0.70  # 亏损期，大幅保守
        elif sharpe < 0.5:
            factor *= 0.85
        elif sharpe < 1.0:
            factor *= 0.95
        elif sharpe < 2.0:
            factor *= 1.0
        else:
            factor *= 1.05  # 优秀期，略微激进

        # 2. Sortino Ratio 补充 (更关注下行风险)
        if sortino > 0 and sortino > sharpe * 1.2:
            # Sortino 明显优于 Sharpe，说明上涨多下跌少
            factor *= 1.05

        # 3. 最大回撤惩罚
        if max_dd > 20:
            factor *= 0.90
        elif max_dd > 30:
            factor *= 0.80

        # 4. 胜率调整
        if win_rate < 0.4:
            factor *= 0.90
        elif win_rate > 0.6:
            factor *= 1.05

        # 限制在合理范围 (0.6 - 1.2)
        factor = max(0.6, min(1.2, factor))

        return factor
```

#### 效果示例

**场景 1: 策略表现优异**
```python
metrics = {
    'sharpe_ratio': 2.5,
    'sortino_ratio': 3.0,
    'max_drawdown': 12.0,
    'win_rate': 0.65
}

# performance_factor ≈ 1.05 × 1.05 × 1.0 × 1.05 = 1.16

# 原始 Conviction: 60 分 (HOLD)
# 调整后: 60 × 1.16 = 69.6 分 (接近 BUY 阈值 70)
```

**场景 2: 策略表现不佳**
```python
metrics = {
    'sharpe_ratio': -0.5,
    'sortino_ratio': -0.3,
    'max_drawdown': 25.0,
    'win_rate': 0.35
}

# performance_factor ≈ 0.70 × 1.0 × 0.90 × 0.90 = 0.57

# 原始 Conviction: 60 分 (HOLD)
# 调整后: 60 × 0.57 = 34.2 分 (更保守，接近 SELL 区间)
```

---

### 方案 2: 动态调整 Agent 权重 ⭐⭐⭐⭐

**推荐指数**: ★★★★☆
**难度**: 较高
**效果**: 长期优化

#### 实现原理

为每个 Agent 计算**"预测准确率 Sharpe"**，根据表现动态调整权重。

**核心思想**: "表现好的 Agent 获得更高权重"

#### Agent 表现评估

```python
# 计算 Agent 的"预测收益率"
for each prediction:
    if Agent 预测 BULLISH and 实际上涨:
        agent_return = 实际涨幅  # 正确预测
    elif Agent 预测 BEARISH and 实际下跌:
        agent_return = abs(实际跌幅)  # 正确预测
    else:
        agent_return = -abs(实际变化)  # 错误预测

# 基于预测收益序列计算 Agent Sharpe
agent_sharpe = mean(agent_returns) / std(agent_returns)
```

#### 权重优化

使用 **Softmax** 将 Sharpe 转化为权重：

```python
# 示例：3 个 Agent 的 Sharpe
sharpe_values = [
    macro_sharpe=1.5,
    onchain_sharpe=2.2,  # 最优
    ta_sharpe=0.8
]

# Softmax 归一化
weights = softmax(sharpe_values, temperature=2.0)

# 结果: {"macro": 0.32, "onchain": 0.48, "ta": 0.20}
# OnChain 表现最好，获得最高权重
```

#### 代码实现

```python
# app/services/decision/agent_performance_tracker.py

import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_execution import AgentExecution
from app.models.strategy_execution import StrategyExecution


class AgentPerformanceTracker:
    """Agent 表现追踪与权重优化"""

    @staticmethod
    async def calculate_agent_sharpe(
        db: AsyncSession,
        portfolio_id: str,
        agent_name: str,
        lookback_days: int = 30
    ) -> float:
        """
        计算 Agent 的预测准确率 Sharpe

        Returns:
            float: Agent Sharpe Ratio (年化)
        """
        # 1. 获取历史记录
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        stmt = (
            select(AgentExecution, StrategyExecution)
            .join(StrategyExecution)
            .where(
                AgentExecution.agent_name == agent_name,
                StrategyExecution.portfolio_id == portfolio_id,
                AgentExecution.executed_at >= cutoff_date
            )
            .order_by(AgentExecution.executed_at.asc())
        )

        result = await db.execute(stmt)
        records = result.all()

        if len(records) < 10:
            return 0.0

        # 2. 计算预测收益
        agent_returns = []

        for i in range(len(records) - 1):
            current = records[i]
            next_record = records[i + 1]

            signal = current.AgentExecution.signal

            current_price = current.StrategyExecution.market_snapshot.get('btc_price', 0)
            next_price = next_record.StrategyExecution.market_snapshot.get('btc_price', 0)

            if current_price > 0:
                actual_return = (next_price - current_price) / current_price

                # 评估预测正确性
                if signal == "BULLISH" and actual_return > 0:
                    agent_returns.append(actual_return)
                elif signal == "BEARISH" and actual_return < 0:
                    agent_returns.append(abs(actual_return))
                elif signal == "NEUTRAL":
                    agent_returns.append(0)
                else:
                    agent_returns.append(-abs(actual_return))

        if len(agent_returns) < 2:
            return 0.0

        # 3. 计算 Sharpe Ratio
        mean_return = np.mean(agent_returns)
        std_return = np.std(agent_returns, ddof=1)

        if std_return == 0:
            return 0.0

        agent_sharpe = mean_return / std_return
        agent_sharpe_annual = agent_sharpe * np.sqrt(365)

        return round(agent_sharpe_annual, 3)

    @staticmethod
    async def optimize_agent_weights(
        db: AsyncSession,
        portfolio_id: str,
        temperature: float = 2.0
    ) -> Dict[str, float]:
        """
        基于 Agent 表现优化权重

        Args:
            temperature: Softmax 温度参数
                - 值越大，权重分布越平均
                - 值越小，强者通吃

        Returns:
            Dict[str, float]: 优化后的权重
        """
        # 1. 计算各 Agent Sharpe
        macro_sharpe = await AgentPerformanceTracker.calculate_agent_sharpe(
            db, portfolio_id, "macro_agent"
        )
        onchain_sharpe = await AgentPerformanceTracker.calculate_agent_sharpe(
            db, portfolio_id, "onchain_agent"
        )
        ta_sharpe = await AgentPerformanceTracker.calculate_agent_sharpe(
            db, portfolio_id, "ta_agent"
        )

        # 2. Softmax 归一化
        sharpe_values = np.array([
            max(0, macro_sharpe),
            max(0, onchain_sharpe),
            max(0, ta_sharpe)
        ])

        # 全为 0 时使用默认权重
        if sharpe_values.sum() == 0:
            return {"macro": 0.40, "onchain": 0.40, "ta": 0.20}

        # Softmax
        exp_values = np.exp(sharpe_values / temperature)
        weights = exp_values / exp_values.sum()

        optimized_weights = {
            "macro": round(float(weights[0]), 3),
            "onchain": round(float(weights[1]), 3),
            "ta": round(float(weights[2]), 3)
        }

        # 确保总和为 1.0
        total = sum(optimized_weights.values())
        optimized_weights = {k: v/total for k, v in optimized_weights.items()}

        return optimized_weights
```

#### 应用方式

```python
# strategy_orchestrator.py

# Portfolio 新增字段: use_adaptive_weights (Boolean)

if portfolio.use_adaptive_weights:
    # 使用自动优化权重
    custom_weights = await AgentPerformanceTracker.optimize_agent_weights(
        db=db,
        portfolio_id=str(portfolio.id)
    )
    logger.info(f"🔄 自适应权重: {custom_weights}")
else:
    # 使用固定权重
    custom_weights = portfolio.agent_weights
```

---

### 方案 3: 基于 Sharpe 的仓位管理 ⭐⭐⭐⭐⭐

**推荐指数**: ★★★★★
**难度**: 简单
**效果**: 显著降低风险

#### 实现原理

根据策略 Sharpe Ratio **动态调整每次交易的仓位大小**。

#### 调整规则

| Sharpe Ratio | 仓位乘数 | 说明 |
|-------------|---------|------|
| < 0 | 0.50× | 策略亏损，仓位减半 |
| 0 - 1 | 0.75× | 表现一般，减少 25% |
| 1 - 2 | 1.00× | 正常表现，维持不变 |
| > 2 | 1.20× | 优秀表现，增加 20% |

#### 代码实现

```python
# app/services/decision/signal_generator.py

class SignalGenerator:

    def generate_signal(
        self,
        conviction_score: float,
        market_data: dict,
        current_position: Optional[float] = None,
        portfolio_metrics: Optional[Dict[str, float]] = None  # 🆕
    ) -> SignalOutput:

        # ... 原有信号判断逻辑 ...

        # 计算基础仓位
        base_position = self._calculate_position_size(
            conviction_score, signal, signal_strength, market_data
        )

        # 🆕 基于 Sharpe 调整仓位
        if portfolio_metrics:
            position_size = self._adjust_position_by_sharpe(
                base_position=base_position,
                metrics=portfolio_metrics
            )
        else:
            position_size = base_position

        return SignalOutput(
            signal=signal,
            position_size=position_size,
            ...
        )

    def _adjust_position_by_sharpe(
        self,
        base_position: float,
        metrics: Dict[str, float]
    ) -> float:
        """
        基于 Sharpe 调整仓位

        逻辑:
        - 策略表现好 → 增加仓位
        - 策略表现差 → 减少仓位
        """
        sharpe = metrics.get('sharpe_ratio', 0)

        # 确定乘数
        if sharpe < 0:
            multiplier = 0.50
        elif sharpe < 1.0:
            multiplier = 0.75
        elif sharpe < 2.0:
            multiplier = 1.0
        else:
            multiplier = 1.2

        adjusted_position = base_position * multiplier

        # 仍需遵守仓位限制
        adjusted_position = max(
            self.MIN_POSITION_SIZE,
            min(self.MAX_POSITION_SIZE, adjusted_position)
        )

        return adjusted_position
```

#### 效果示例

```python
# 基础仓位: 0.4% (Conviction=75)

# Sharpe = 2.5 (优秀)
# 调整后: 0.4% × 1.2 = 0.48%

# Sharpe = -0.5 (亏损)
# 调整后: 0.4% × 0.5 = 0.2%
```

---

## 🏗️ 技术架构

### 新增模块

```
AMbackend/app/services/
├── decision/
│   ├── conviction_calculator.py      # ✏️ 修改: 增加 performance_factor
│   ├── signal_generator.py            # ✏️ 修改: 增加 position 调整
│   └── agent_performance_tracker.py   # 🆕 新增: Agent 表现追踪
│
└── trading/
    └── portfolio_metrics.py           # 🆕 新增: Sharpe/Sortino 计算
```

### 数据流

```
┌─────────────────────────────────────────────────────────┐
│                    定时任务 (每日 UTC 0点)                │
│                                                         │
│  1. 获取 PortfolioSnapshot 历史数据                      │
│  2. 计算 Sharpe Ratio, Sortino Ratio                   │
│  3. 更新 Portfolio 表                                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    策略执行 (实时)                       │
│                                                         │
│  1. 执行 3 个 Agent 分析                                │
│  2. 计算 Conviction Score                               │
│  3. 🆕 读取 Portfolio Metrics                           │
│  4. 🆕 应用 Performance Factor                          │
│  5. 生成交易信号                                         │
│  6. 🆕 调整仓位大小                                      │
│  7. 执行交易                                            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    记录与反馈                            │
│                                                         │
│  - 交易结果写入 Trade 表                                │
│  - 更新 PortfolioSnapshot                               │
│  - 下次执行时使用最新 Metrics                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 实现步骤

### Phase 1: 基础指标计算 (2-3 天)

#### 1.1 创建 Portfolio Metrics 服务

**文件**: `app/services/trading/portfolio_metrics.py`

**功能**:
- `calculate_sharpe_ratio()`: 基于快照计算 Sharpe
- `calculate_sortino_ratio()`: 计算 Sortino
- `update_portfolio_metrics()`: 批量更新指标

#### 1.2 添加定时任务

**文件**: `app/services/strategy/scheduler.py`

**任务**:
- 每日 UTC 0点计算所有活跃 Portfolio 的风险指标
- 更新 `Portfolio.sharpe_ratio` 字段

---

### Phase 2: 风险调整策略 (3-4 天)

#### 2.1 修改 Conviction Calculator

**文件**: `app/services/decision/conviction_calculator.py`

**改动**:
- 新增 `portfolio_metrics` 参数
- 新增 `_calculate_performance_factor()` 方法
- 在 Step 7 应用调整因子

#### 2.2 修改 Signal Generator

**文件**: `app/services/decision/signal_generator.py`

**改动**:
- 新增 `portfolio_metrics` 参数
- 新增 `_adjust_position_by_sharpe()` 方法
- 在仓位计算后应用调整

#### 2.3 更新 Strategy Orchestrator

**文件**: `app/services/strategy/strategy_orchestrator.py`

**改动**:
```python
# 读取 Portfolio Metrics
portfolio_metrics = {
    'sharpe_ratio': portfolio.sharpe_ratio or 0.0,
    'sortino_ratio': 0.0,  # TODO
    'max_drawdown': portfolio.max_drawdown,
    'win_rate': portfolio.win_rate
}

# 传递给 Conviction Calculator
conviction_result = self.conviction_calculator.calculate(
    conviction_input,
    custom_weights=custom_weights,
    portfolio_metrics=portfolio_metrics  # 🆕
)

# 传递给 Signal Generator
signal_result = self.signal_generator.generate_signal(
    conviction_score=conviction_result.score,
    market_data=market_data,
    current_position=current_position,
    portfolio_metrics=portfolio_metrics  # 🆕
)
```

---

### Phase 3: Agent 自适应权重 (可选, 4-5 天)

#### 3.1 创建 Agent Performance Tracker

**文件**: `app/services/decision/agent_performance_tracker.py`

**功能**:
- `calculate_agent_sharpe()`: 计算单个 Agent 表现
- `optimize_agent_weights()`: 优化权重配置

#### 3.2 数据库迁移

**新增字段**: `Portfolio.use_adaptive_weights` (Boolean)

```python
# alembic migration
op.add_column('portfolios',
    sa.Column('use_adaptive_weights', sa.Boolean(),
              server_default='false', nullable=False)
)
```

#### 3.3 前端配置

在 Admin Settings 添加开关：
- "Enable Adaptive Weights" (启用自适应权重)

---

## 📊 性能指标详解

### Sharpe Ratio 计算示例

**数据**: 过去 30 天的每日收益率

```python
# 示例数据
daily_returns = [
    0.02,   # Day 1: +2%
    -0.01,  # Day 2: -1%
    0.03,   # Day 3: +3%
    ...
]

# 计算
mean_return = 0.0015  # 日均收益 0.15%
std_return = 0.025     # 标准差 2.5%
risk_free_daily = 0.02 / 365 = 0.000055

# Sharpe (日)
sharpe_daily = (0.0015 - 0.000055) / 0.025 = 0.058

# Sharpe (年化)
sharpe_annual = 0.058 × √365 = 1.11
```

**解读**: Sharpe = 1.11，表现尚可，接近优良水平。

---

### Sortino Ratio 计算示例

**区别**: 只计算**负收益的标准差**

```python
# 提取负收益
downside_returns = [-0.01, -0.02, -0.015, ...]  # 只取 < 0 的

# 下行标准差
downside_std = 0.018  # 小于总标准差 0.025

# Sortino (日)
sortino_daily = (0.0015 - 0) / 0.018 = 0.083

# Sortino (年化)
sortino_annual = 0.083 × √365 = 1.59
```

**解读**: Sortino = 1.59 > Sharpe = 1.11，说明策略的下跌少、上涨多，风险收益比更优。

---

### 指标对比

| 场景 | Sharpe | Sortino | 说明 |
|-----|--------|---------|------|
| 稳定上涨 | 2.5 | 2.8 | 两者接近，策略表现优秀 |
| 大涨大跌 | 0.8 | 1.5 | Sortino 更高，但整体波动大 |
| 持续亏损 | -0.5 | -0.3 | 两者均为负，策略失效 |
| 震荡市 | 0.5 | 0.6 | 两者均低，策略表现一般 |

---

## ✅ 测试与验证

### 单元测试

```python
# tests/test_portfolio_metrics.py

async def test_calculate_sharpe_ratio():
    """测试 Sharpe 计算"""
    # 准备测试数据
    snapshots = create_test_snapshots(
        initial_value=10000,
        returns=[0.02, -0.01, 0.03, 0.01, -0.005]
    )

    # 计算 Sharpe
    sharpe = await portfolio_metrics.calculate_sharpe_ratio(
        db=db,
        portfolio_id=test_portfolio_id
    )

    # 验证
    assert 0 < sharpe < 3
```

### 集成测试

```python
# tests/test_risk_adjusted_strategy.py

async def test_performance_factor_adjustment():
    """测试策略表现调整因子"""

    # 场景 1: 优秀表现
    metrics = {'sharpe_ratio': 2.5, 'max_drawdown': 10, 'win_rate': 0.65}
    factor = calculator._calculate_performance_factor(metrics)
    assert 1.1 < factor < 1.2

    # 场景 2: 差劲表现
    metrics = {'sharpe_ratio': -0.5, 'max_drawdown': 30, 'win_rate': 0.35}
    factor = calculator._calculate_performance_factor(metrics)
    assert 0.5 < factor < 0.7
```

### 回测验证

**目标**: 对比启用/禁用风险调整的策略表现

```python
# 回测参数
- 时间段: 2024-01-01 ~ 2024-11-07
- 初始资金: 10,000 USDT
- 策略 A: 固定权重 + 固定仓位
- 策略 B: 风险调整权重 + 动态仓位

# 预期结果
- 策略 B 的 Max Drawdown < 策略 A
- 策略 B 的 Sharpe Ratio > 策略 A
- 策略 B 的总收益可能略低，但风险收益比更优
```

---

## ⚠️ 风险与限制

### 1. 过度优化风险

**问题**: 基于历史数据优化，可能过拟合

**缓解**:
- 使用较长回溯期（30 天以上）
- 限制调整幅度（0.6 - 1.2）
- 定期人工审核

### 2. 数据不足期

**问题**: 新策略运行初期，Sharpe 无意义

**缓解**:
- 前 30 天不应用风险调整
- 使用默认权重和仓位

### 3. 市场突变

**问题**: 历史表现不代表未来

**缓解**:
- 保留熔断机制
- 人工监控异常指标

### 4. 计算成本

**问题**: 每次执行需计算多个指标

**缓解**:
- 使用缓存（每日计算一次）
- 异步计算，不阻塞主流程

---

## 🔮 未来优化方向

### 1. 机器学习优化

使用 **强化学习** 自动学习最优权重和仓位策略：

```python
# RL Agent
- State: [Sharpe, Sortino, Conviction, Market Data]
- Action: [Agent Weights, Position Size]
- Reward: Risk-Adjusted Return
```

### 2. 多周期 Sharpe

分别计算：
- 短期 Sharpe (7 天)
- 中期 Sharpe (30 天)
- 长期 Sharpe (90 天)

综合三者决策。

### 3. 市场状态识别

结合 VIX (波动率指数) 和 Fear & Greed Index，识别市场状态：
- 牛市初期、牛市末期、熊市初期、熊市末期、震荡市

不同状态下使用不同的调整策略。

### 4. Agent 集成学习

不仅调整权重，还可以：
- 动态启用/禁用表现差的 Agent
- 引入新的 Agent (如 Sentiment Agent)
- 使用 Stacking 集成多个预测

---

## 📚 参考资料

### 学术论文

1. **Sharpe, W. F.** (1966). "Mutual Fund Performance". *Journal of Business*, 39(1), 119-138.
2. **Sortino, F. A., & Price, L. N.** (1994). "Performance Measurement in a Downside Risk Framework". *Journal of Investing*, 3(3), 59-64.
3. **Modigliani, F., & Modigliani, L.** (1997). "Risk-Adjusted Performance". *Journal of Portfolio Management*, 23(2), 45-54.

### 实践案例

- Renaissance Technologies: 使用多因子风险调整模型
- Bridgewater Associates: All Weather 策略中的风险平价
- Two Sigma: 机器学习 + 风险管理

### 相关资源

- [Quantopian Lectures: Risk Models](https://www.quantopian.com/lectures)
- [QuantConnect: Portfolio Optimization](https://www.quantconnect.com/)
- [Python for Finance: Risk Management](https://www.oreilly.com/library/view/python-for-finance/9781492024323/)

---

## 📝 变更日志

| 版本 | 日期 | 变更内容 |
|-----|------|----------|
| v1.0 | 2025-11-07 | 初版发布，完整设计方案 |

---

## 👥 贡献者

- **Strategy Design**: AutoMoney Team
- **Technical Review**: Claude (Anthropic)
- **Implementation Lead**: TBD

---

## 📧 联系方式

如有疑问或建议，请通过以下方式联系：

- **GitHub Issues**: [AutoMoney Repository](https://github.com/your-repo/automoney)
- **Email**: strategy@automoney.ai

---

**最后更新**: 2025-11-07
**文档状态**: ✅ 审核通过
**下一步**: 开始 Phase 1 实现
