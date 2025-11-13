# Strategy页面前后端数据映射调研报告

> **调研日期**: 2025-11-06
> **调研范围**: `/marketplace` 和 `/strategy/:id` 两个页面
> **后端状态**: Phase 1-5 完成 + 真实数据集成完成

---

## 📊 完整数据映射表

### 1. Strategy Marketplace 列表页 (`/marketplace`)

| UI字段/功能 | 前端展示位置 | 数据来源/计算方式 | 后端API状态 | 替代方案 | 开发难度 | 优先级 |
|------------|------------|----------------|-----------|---------|---------|--------|
| **基础信息** |
| `name` | 卡片标题 | Portfolio.name | ✅ 已有 `/api/v1/portfolios` | - | - | P0 |
| `subtitle` | 卡片副标题 | Portfolio.strategy_name | ✅ 已有 | - | - | P0 |
| `id` | 路由参数 | Portfolio.id (UUID) | ✅ 已有 | - | - | P0 |
| `description` | 详情页描述 | 需新增字段 | ❌ 缺失 | 用strategy_name代替 | 🟢 简单 | P2 |
| **标签系统** |
| `tags[]` | Badge标签 | 根据strategy自动生成 | 🔶 部分可用 | 基于已有数据生成 | 🟡 中等 | P1 |
| - "Macro-Driven" | 策略类型标签 | 固定映射 | ✅ 可实现 | - | 🟢 简单 | P1 |
| - "BTC/ETH" | 资产类型标签 | 从holdings提取 | ✅ 已有数据 | - | 🟢 简单 | P1 |
| - "Long-Term" | 投资期限标签 | 固定配置 | ✅ 可实现 | - | 🟢 简单 | P2 |
| **性能指标** |
| `annualizedReturn` | 收益率 % | **缺失** | ❌ 需计算 | 用total_pnl_percent | 🟡 中等 | P0 |
| `maxDrawdown` | 最大回撤 % | Portfolio.max_drawdown | ✅ 已有 | - | - | P0 |
| `sharpeRatio` | 夏普比率 | Portfolio.sharpe_ratio | ✅ 已有 | - | - | P0 |
| `sortinoRatio` | 索提诺比率 | **缺失** | ❌ 需计算 | 暂不显示 | 🔴 困难 | P2 |
| `tvl` | 总锁仓量 | **缺失（多用户汇总）** | ❌ 需聚合 | 用单用户total_value | 🔴 困难 | P1 |
| **Squad信息** |
| `squadSize` | Agent数量 | 固定值3 | ✅ 已知 | - | 🟢 简单 | P0 |
| `squadAgents[]` | Agent列表 | 固定配置 | ✅ 已知 | - | 🟢 简单 | P0 |
| **历史数据** |
| `history[]` | 迷你图表数据 | PortfolioSnapshot.total_value | ✅ 已有API | - | 🟢 简单 | P0 |
| **风险等级** |
| `riskLevel` | 风险徽章 | 基于max_drawdown计算 | 🔶 可计算 | - | 🟢 简单 | P0 |

---

### 2. Strategy Details 详情页 (`/strategy/:id`)

| UI字段/功能 | 前端展示位置 | 数据来源/计算方式 | 后端API状态 | 替代方案 | 开发难度 | 优先级 |
|------------|------------|----------------|-----------|---------|---------|--------|
| **Squad Manager 洞察** |
| `managerSummary.conviction` | 置信度分数 | StrategyExecution.conviction_score | ✅ 已有 | - | - | P0 |
| `managerSummary.message` | Manager消息 | **需LLM生成或模板** | ❌ 缺失 | 用Agent reasoning汇总 | 🔴 困难 | P1 |
| `managerSummary.updated` | 更新时间 | StrategyExecution.execution_time | ✅ 已有 | - | - | P0 |
| **Squad Roster (Agent列表)** |
| `agent.name` | Agent名称 | 固定映射 | ✅ 已知 | - | 🟢 简单 | P0 |
| `agent.role` | Agent角色 | 固定映射 | ✅ 已知 | - | 🟢 简单 | P0 |
| `agent.weight` | 权重百分比 | 固定值 (40%/40%/20%) | ✅ 已知 | - | 🟢 简单 | P0 |
| `agent.icon` | Agent图标 | 前端固定 | ✅ 前端处理 | - | - | P0 |
| `agent.color` | Agent颜色 | 前端固定 | ✅ 前端处理 | - | - | P0 |
| **性能历史图表** |
| `performanceData[]` | 历史表现曲线 | PortfolioSnapshot + 时间序列 | ✅ 已有API | - | 🟢 简单 | P0 |
| `performanceData.strategy` | 策略收益曲线 | Snapshot.total_value归一化 | ✅ 可计算 | - | 🟢 简单 | P0 |
| `performanceData.btc` | BTC基准曲线 | Snapshot.btc_price归一化 | ✅ 已有数据 | - | 🟢 简单 | P0 |
| `performanceData.eth` | ETH基准曲线 | Snapshot.eth_price归一化 | ✅ 已有数据 | - | 🟢 简单 | P0 |
| **Deploy & Withdraw** |
| `availableBalance` | 可用余额 | User余额（需新增） | ❌ 缺失 | 用Portfolio.current_balance | 🟡 中等 | P0 |
| `currentInvestment` | 当前投资金额 | Portfolio.total_value | ✅ 已有 | - | - | P0 |
| `investAmount` | 投入金额输入 | 前端状态 | ✅ 前端处理 | - | - | P0 |
| `withdrawAmount` | 提现金额输入 | 前端状态 | ✅ 前端处理 | - | - | P0 |
| **Recent Activities (最近操作)** |
| `activities[].date` | 操作时间 | Trade.executed_at | ✅ 已有API | - | - | P0 |
| `activities[].signal` | 市场信号 | **需从Agent推理提取** | 🔶 部分可用 | 用Trade.reason | 🟡 中等 | P1 |
| `activities[].action` | 交易动作 | Trade.trade_type + amount | ✅ 已有 | - | 🟢 简单 | P0 |
| `activities[].result` | 交易结果 % | Trade.realized_pnl_percent | ✅ 已有 | - | - | P0 |
| `activities[].agent` | 执行Agent | **需从execution关联** | 🔶 可追溯 | 用"Multi-Agent" | 🟡 中等 | P1 |
| **Strategy Parameters** |
| `parameters.assets` | 资产配置 | 固定配置或从holdings计算 | 🔶 可计算 | - | 🟢 简单 | P1 |
| `parameters.rebalancePeriod` | 调仓周期 | 固定值 "Every 4 Hours" | ✅ 已知 | - | - | P1 |
| `parameters.riskLevel` | 风险等级 | 基于max_drawdown映射 | ✅ 可计算 | - | 🟢 简单 | P0 |
| `parameters.minInvestment` | 最小投资额 | 业务配置 | ✅ 固定值 | - | - | P2 |
| `parameters.lockupPeriod` | 锁定期 | 业务配置 | ✅ 固定值 | - | - | P2 |
| `parameters.managementFee` | 管理费 | 业务配置 | ✅ 固定值 | - | - | P2 |
| `parameters.performanceFee` | 业绩费 | 业务配置 | ✅ 固定值 | - | - | P2 |
| **Strategy Philosophy** |
| `philosophy` | 策略哲学文本 | **需人工编写或LLM生成** | ❌ 缺失 | 用固定模板 | 🟡 中等 | P2 |

---

## 🎯 总结分析

### ✅ 已完全可用的数据 (15项)

| 字段 | API端点 | 数据来源 |
|------|--------|---------|
| Portfolio基础信息 | `GET /api/v1/portfolios` | portfolios表 |
| Portfolio详情+持仓 | `GET /api/v1/portfolios/{id}` | portfolios + holdings |
| 历史快照 | `GET /api/v1/portfolios/{id}/snapshots` | portfolio_snapshots表 |
| 交易历史 | `GET /api/v1/trades?portfolio_id={id}` | trades表 |
| 策略执行记录 | `GET /api/v1/strategy?portfolio_id={id}` | strategy_executions表 |
| Conviction Score | StrategyExecution.conviction_score | 已计算并存储 |
| 最大回撤 | Portfolio.max_drawdown | Paper Trading引擎计算 |
| 夏普比率 | Portfolio.sharpe_ratio | Paper Trading引擎计算 |
| 总盈亏 | Portfolio.total_pnl / total_pnl_percent | 实时计算 |
| 胜率 | Portfolio.win_rate | 实时计算 |
| BTC/ETH价格 | Snapshot.btc_price / eth_price | 市场数据API |
| 交易详情 | Trade全部字段 | Paper Trading记录 |
| Agent数量 | 固定值3 | 系统配置 |
| Agent权重 | Macro 40% / OnChain 40% / TA 20% | 系统配置 |
| 风险等级映射 | 基于max_drawdown计算 | 可实时计算 |

### 🔶 部分可用/需简单处理 (8项)

| 字段 | 现状 | 解决方案 | 开发量 |
|------|-----|---------|--------|
| 年化收益率 | 只有累计收益 | 根据时间区间计算年化 | 1-2小时 |
| 标签系统 | 无预设标签 | 基于strategy_name和holdings生成 | 2-3小时 |
| TVL (总锁仓) | 只有单用户数据 | 暂时用single portfolio的total_value | 1小时 |
| 历史图表数据 | 有原始数据 | 归一化到100基准 | 1-2小时 |
| 市场信号文本 | Agent有reasoning | 提取关键词或用reasoning前50字 | 2-3小时 |
| 执行Agent名称 | 可通过execution_id追溯 | 关联agent_executions表 | 2-3小时 |
| 资产配置比例 | holdings有数据 | 计算BTC/ETH持仓占比 | 1-2小时 |
| 可用余额 | Portfolio.current_balance | 直接使用 | 1小时 |

**小计开发量**: 约1-2天

### ❌ 需额外开发的功能 (5项)

| 字段 | 缺失原因 | 替代方案 | 是否必须 | 开发难度 | 开发量 |
|------|---------|---------|---------|---------|--------|
| **Sortino Ratio** | 需要下行波动率计算 | 暂不显示或显示为N/A | ❌ 非必须 | 🔴 困难 | 1-2天 |
| **Manager消息生成** | 需要LLM或模板系统 | 用Agent reasoning汇总 | 🔶 建议有 | 🔴 困难 | 2-3天 |
| **Strategy Description** | 需要人工编写 | 用固定模板 | ❌ 非必须 | 🟡 中等 | 0.5天 |
| **Philosophy文本** | 需要人工编写 | 用固定模板 | ❌ 非必须 | 🟡 中等 | 0.5天 |
| **多用户TVL聚合** | 需要新的聚合查询 | 暂时显示单用户投资额 | ❌ 非必须 | 🔴 困难 | 1-2天 |

**如果全部开发**: 约5-9天
**如果跳过非必须项**: 约2-3天

---

## 📋 推荐实施方案

### 🚀 Phase 1: 核心功能对接 (2-3天) - **推荐优先实施**

#### 1.1 创建Strategy Marketplace API (1天)

**新端点**: `GET /api/v1/strategy/marketplace`

**返回数据**:
```json
{
  "strategies": [
    {
      "id": "uuid",
      "name": "HODL-Wave Squad",
      "subtitle": "Multi-Agent Strategy",
      "description": "Elite AI squad combining macro, onchain and technical analysis",
      "tags": ["Macro-Driven", "BTC/ETH", "Long-Term"],
      "annualized_return": 45.6,  // 计算年化
      "max_drawdown": 18.2,
      "sharpe_ratio": 2.1,
      "pool_size": 12500000,  // 暂用total_value
      "squad_size": 3,
      "risk_level": "medium",  // 基于max_drawdown映射
      "history": [
        {"date": "2024-07", "value": 100},
        {"date": "2024-08", "value": 105}
        // 从snapshots归一化
      ]
    }
  ]
}
```

**实现逻辑**:
- 查询所有active portfolios
- 从portfolio_snapshots计算年化收益
- 基于max_drawdown映射risk_level
- 生成标签（Macro-Driven, BTC/ETH从holdings计算）

#### 1.2 创建Strategy Details API (0.5天)

**新端点**: `GET /api/v1/strategy/marketplace/{portfolio_id}`

**返回数据**:
```json
{
  "id": "uuid",
  "name": "HODL-Wave Squad",
  "description": "...",
  "tags": ["..."],
  "performance_metrics": {
    "annualized_return": 45.6,
    "max_drawdown": 18.2,
    "sharpe_ratio": 2.1,
    "sortino_ratio": null  // 暂不支持
  },
  "conviction_summary": {
    "score": 78,
    "message": "综合Agent分析: Macro看多(75%), OnChain中性(60%), TA偏多(65%)",
    "updated_at": "2025-11-06T10:00:00Z"
  },
  "squad_agents": [
    {"name": "The Oracle", "role": "MacroAgent", "weight": "40%"},
    {"name": "Data Warden", "role": "OnChainAgent", "weight": "40%"},
    {"name": "Momentum Scout", "role": "TAAgent", "weight": "20%"}
  ],
  "performance_history": {
    "strategy": [...],
    "btc_benchmark": [...],
    "eth_benchmark": [...]
  },
  "recent_activities": [
    {
      "date": "2025-10-30 08:00 UTC",
      "signal": "Strong Bull Market",  // 从Agent reasoning提取
      "action": "Buy 0.5% BTC",
      "result": "+1.2%",
      "agent": "The Oracle"
    }
  ],
  "parameters": {
    "assets": "BTC 60% / ETH 40%",  // 从holdings计算
    "rebalance_period": "Every 4 Hours",
    "risk_level": "Low-Medium Risk",
    "min_investment": "100 USDT",
    "lockup_period": "No Lock-up",
    "management_fee": "2% Annual",
    "performance_fee": "20% on Excess Returns"
  },
  "philosophy": "固定模板文本..."
}
```

#### 1.3 前端API集成 (0.5天)

- 替换Mock数据为真实API调用
- 添加loading状态
- 添加error handling

### 🎨 Phase 2: 增强功能 (可选, 2-3天)

#### 2.1 Manager消息智能生成 (2天)

**方案A**: LLM生成（推荐）
```python
async def generate_manager_message(
    conviction_score: float,
    agent_outputs: Dict[str, Any],
    market_data: Dict[str, Any]
) -> str:
    prompt = f"""
    Based on the following data, generate a brief squad manager message:
    - Conviction Score: {conviction_score}%
    - Macro Signal: {agent_outputs['macro']['signal']}
    - OnChain Signal: {agent_outputs['onchain']['signal']}
    - TA Signal: {agent_outputs['ta']['signal']}
    - BTC Price: ${market_data['btc_price']}
    - Fear & Greed: {market_data['fear_greed']['value']}

    Write 2-3 sentences analyzing market conditions and strategy recommendation.
    """
    return await llm_manager.generate(prompt)
```

**方案B**: 模板系统（简单）
```python
def generate_manager_message_template(conviction_score: float) -> str:
    if conviction_score > 75:
        return "Market conditions are favorable. Our squad maintains a bullish stance..."
    elif conviction_score > 60:
        return "We're observing mixed signals across our data feeds..."
    else:
        return "Market sentiment is cautiously optimistic..."
```

#### 2.2 Sortino Ratio计算 (1天)

需要实现下行波动率计算，暂时可跳过。

---

## 🔧 API端点开发清单

### 需要新增的API

| 端点 | 方法 | 功能 | 优先级 | 开发量 |
|------|-----|------|--------|--------|
| `/api/v1/strategy/marketplace` | GET | 获取策略列表（带过滤排序） | P0 | 6-8h |
| `/api/v1/strategy/marketplace/{id}` | GET | 获取策略详情 | P0 | 4-6h |
| `/api/v1/strategy/marketplace/{id}/deploy` | POST | 部署资金到策略 | P0 | 2-3h |
| `/api/v1/strategy/marketplace/{id}/withdraw` | POST | 从策略提现 | P0 | 2-3h |
| `/api/v1/strategy/marketplace/{id}/activities` | GET | 获取最近操作记录 | P1 | 2-3h |

### 需要增强的现有API

| 端点 | 增强内容 | 优先级 | 开发量 |
|------|---------|--------|--------|
| `GET /api/v1/portfolios` | 添加年化收益计算 | P0 | 2h |
| `GET /api/v1/portfolios/{id}` | 添加资产配置比例 | P1 | 1h |
| `GET /api/v1/portfolios/{id}/snapshots` | 添加基准归一化 | P1 | 2h |
| `GET /api/v1/trades` | 添加Agent关联 | P1 | 2h |

---

## 💡 数据替换建议

### 高优先级替换 (必须实现)

| 前端Mock字段 | 后端真实数据 | 映射方式 |
|-------------|------------|---------|
| `strategies[]` | Portfolios列表 | 1:1映射 |
| `annualizedReturn` | 从snapshots计算 | (最新value / 初始value) ^ (365 / days) - 1 |
| `maxDrawdown` | Portfolio.max_drawdown | 直接使用 |
| `sharpeRatio` | Portfolio.sharpe_ratio | 直接使用 |
| `history[]` | PortfolioSnapshots | 归一化到100基准 |
| `recentActivities[]` | Trades列表 | 格式转换 |
| `conviction` | Latest StrategyExecution.conviction_score | 直接使用 |

### 中优先级替换 (建议实现)

| 前端Mock字段 | 后端真实数据 | 映射方式 |
|-------------|------------|---------|
| `tvl` | Portfolio.total_value | 暂时单用户，未来聚合 |
| `tags[]` | 基于strategy_name生成 | 映射表 |
| `managerMessage` | Agent reasoning汇总 | 模板或LLM生成 |
| `signal` (in activities) | Trade.reason | 关键词提取 |
| `agent` (in activities) | 通过execution_id追溯 | 关联查询 |

### 低优先级替换 (可暂时跳过)

| 前端Mock字段 | 处理方式 |
|-------------|---------|
| `sortinoRatio` | 暂时显示"N/A" |
| `description` | 使用固定模板 |
| `philosophy` | 使用固定模板 |
| `parameters.*` | 使用业务配置常量 |

---

## ⚠️ 开发难点与风险

### 1. 年化收益率计算 🟡

**难点**: Portfolio可能存活时间不足1年
**解决方案**:
```python
def calculate_annualized_return(initial_value, current_value, days):
    if days < 30:
        return None  # 数据不足
    return ((current_value / initial_value) ** (365 / days) - 1) * 100
```

### 2. 多用户TVL聚合 🔴

**难点**: 当前Paper Trading是单用户，没有多用户资金池概念
**解决方案**:
- Phase 1: 显示"Your Investment" ($45,000)
- Phase 2: 实现多用户资金池（需要架构调整）

### 3. Manager消息生成 🔴

**难点**: 需要自然语言生成
**解决方案**:
- Phase 1: 使用模板（5种固定模板基于conviction_score）
- Phase 2: LLM实时生成（需要额外LLM调用成本）

### 4. 历史数据不足 🟡

**难点**: 新Portfolio可能只有几个snapshot
**解决方案**:
- 显示"Insufficient Data"警告
- 最少需要7个数据点才显示图表

---

## 📊 开发时间估算

### 最小可行版本 (MVP)
- **新API开发**: 2天
- **数据计算逻辑**: 1天
- **前端集成**: 0.5天
- **测试调试**: 0.5天
- **总计**: **4天**

### 完整版本
- **MVP**: 4天
- **Manager消息生成**: 2天
- **Sortino Ratio**: 1天
- **多用户TVL**: 2天
- **总计**: **9天**

---

## ✅ 推荐实施路径

### Week 1: MVP上线 (4天)
1. ✅ 创建marketplace API端点
2. ✅ 实现年化收益计算
3. ✅ 实现历史数据归一化
4. ✅ 前端替换Mock数据
5. ✅ 基础测试

### Week 2: 增强功能 (可选)
1. Manager消息模板系统
2. Agent名称追溯
3. 资产配置计算
4. 完整测试

### Week 3+: 高级功能 (低优先级)
1. Manager消息LLM生成
2. Sortino Ratio计算
3. 多用户TVL聚合

---

## 🎯 最终建议

1. **立即实施**: Phase 1 (4天) - 可以让Strategy页面完全使用真实数据
2. **短期实施**: Manager消息模板 (0.5天) - 提升用户体验
3. **中期实施**: Agent追溯 (1天) - 完善操作历史
4. **长期实施**: Sortino + 多用户TVL (3-4天) - 高级功能

**总时间**: 核心功能4天，完整功能5-6天

---

最后更新: 2025-11-06 18:00
