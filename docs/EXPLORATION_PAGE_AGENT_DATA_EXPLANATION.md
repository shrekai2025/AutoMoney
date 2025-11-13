# Exploration页面Agent数据说明文档

## 1. Agent分数计算方式

### Agent Score的来源
- **Agent的score**是由LLM（大语言模型）在分析市场数据后生成的**投资建议分数**
- **范围**: -100.00 到 +100.00
  - `-100`: 强烈看跌（Strong Bearish）
  - `0`: 中性（Neutral）
  - `+100`: 强烈看涨（Strong Bullish）
- **存储位置**: `AgentExecution.score` 字段（数据库）
- **计算方式**: LLM根据Agent分析的市场数据（宏观、链上、技术指标）综合判断后输出

### 前端显示转换
- 前端显示时，通过 `normalize_score()` 函数将 `-100~+100` 转换为 `-1.0~+1.0`
- 转换公式: `score / 100.0`
- 例如: `score = 50` → 前端显示 `+0.50`

### Agent权重（用于Conviction Score计算）
- **MacroAgent (The Oracle)**: 40%
- **OnChainAgent (Data Warden)**: 40%
- **TAAgent (Momentum Scout)**: 20%

### Conviction Score计算流程
1. 获取每个Agent的score（-100到+100）
2. 应用权重计算加权分数
3. 根据风险指标调整（恐惧贪婪指数、波动率、美元指数）
4. 归一化到0-100范围

---

## 2. N/A数据的处理逻辑

### 当前显示N/A的原因
- 数据在 `agent_specific_data` 中不存在
- 数据值为 `None` 或 `0`
- Agent还未执行过（首次使用）

### 数据获取时机
- **Agent执行时**会从数据源获取最新数据
- **策略定时执行**时会触发Agent执行（默认4小时一次）
- **手动触发**策略执行时也会获取数据

### 数据更新流程
1. Agent执行 → 调用数据API获取最新数据
2. 数据存储到 `agent_specific_data` JSONB字段
3. 前端轮询（30秒）获取最新执行记录
4. 如果数据存在，自动替换N/A显示

### 示例
- **首次**: ETF Net Flow显示 "N/A"
- **Agent执行后**: 如果获取到数据，显示 "+$50M" 或 "-$30M"
- **数据源不可用**: 如果API返回空，继续显示 "N/A"

---

## 3. Agent卡片需要展示的额外数据

### MacroAgent (The Oracle) - 当前未展示的数据

#### 已展示
- ✅ ETF Net Flow
- ✅ Fed Rate

#### 未展示但可用的数据
```json
{
  "risk_assessment": "风险评估文本",  // 风险等级评估
  "key_factors": [                    // 关键影响因素列表
    "Factor 1",
    "Factor 2"
  ],
  "macro_indicators": {
    "dxy_index": 105.2,              // 美元指数
    "inflation_rate": 2.5,           // 通胀率
    "unemployment_rate": 3.7,        // 失业率
    // ... 其他宏观指标
  }
}
```

### OnChainAgent (Data Warden) - 当前未展示的数据

#### 已展示
- ✅ MVRV Z-Score
- ✅ Exchange Flow

#### 未展示但可用的数据
```json
{
  "network_health": "健康/警告/危险",  // 网络健康状态
  "key_observations": [                // 关键观察
    "Observation 1",
    "Observation 2"
  ],
  "onchain_metrics": {
    "active_addresses": 850000,      // 活跃地址数（已在Data Stream显示）
    "nvt_ratio": 45.2,                // NVT比率
    "transaction_volume": 125000,     // 交易量
    "hash_rate": 450000000,           // 算力
    // ... 其他链上指标
  }
}
```

### TAAgent (Momentum Scout) - 当前未展示的数据

#### 已展示
- ✅ RSI(14)
- ✅ Trend Status

#### 未展示但可用的数据
```json
{
  "support_levels": [45000, 42000],   // 支撑位
  "resistance_levels": [50000, 52000], // 阻力位
  "trend_analysis": "上升趋势/下降趋势", // 趋势分析文本
  "key_patterns": [                    // 识别的技术形态
    "Golden Cross",
    "Bull Flag"
  ],
  "technical_indicators": {
    "ema": {
      "ema_9": 48000,                  // EMA9
      "ema_20": 47000,                 // EMA20
      "ema_50": 46000,                 // EMA50
      "trend": "bullish"               // 趋势方向
    },
    "macd": {                          // MACD指标
      "value": 500,
      "signal": 450,
      "histogram": 50
    },
    "bollinger_bands": {               // 布林带
      "upper": 50000,
      "middle": 48000,
      "lower": 46000
    }
    // ... 其他技术指标
  }
}
```

### 建议展示的字段
1. **MacroAgent**: `risk_assessment`（风险评估）
2. **OnChainAgent**: `network_health`（网络健康）、`active_addresses`（活跃地址）
3. **TAAgent**: `support_levels`（支撑位）、`resistance_levels`（阻力位）、`key_patterns`（技术形态）

---

## 4. AI Commander 和 Active Directive 如何有信息

### AI Commander 数据来源

#### 数据表
- `StrategyExecution` 表
- 字段: `llm_summary`, `conviction_score`, `execution_time`

#### 数据生成条件
1. **必须有策略执行记录** (`StrategyExecution`)
2. **策略执行必须完成** (`status = 'completed'`)
3. **必须有Conviction Score** (`conviction_score` 不为空)
4. **最好有LLM总结** (`llm_summary` 不为空)

#### 如何生成数据
1. **创建Portfolio（投资组合）**
   - 在Portfolio页面创建新的投资组合
   - 选择策略定义（Strategy Definition）
   - 分配初始资金

2. **策略定时执行**
   - 系统会根据策略的 `rebalance_period_minutes`（默认240分钟=4小时）自动执行
   - 执行流程:
     ```
     触发执行 → 运行三个Agent → 计算Conviction Score → 生成LLM总结 → 保存到StrategyExecution
     ```

3. **手动触发执行**
   - 在策略详情页面可以手动触发执行
   - 或者通过API调用执行

#### 查询逻辑
```python
# 查询最新的策略执行记录
query = select(StrategyExecution).where(
    StrategyExecution.user_id == current_user.id
).order_by(desc(StrategyExecution.execution_time)).limit(1)
```

### Active Directive 数据来源

#### 数据表
- `StrategyExecution` 表
- 关联: `Portfolio` → `StrategyDefinition`

#### 数据生成条件
1. **必须有策略执行记录**
2. **必须有Portfolio关联**
3. **必须有StrategyDefinition信息**

#### 显示的数据
- **策略名称**: `StrategyDefinition.display_name`
- **策略描述**: `StrategyDefinition.description`
- **倒计时**: 基于 `execution_time` + `rebalance_period_minutes` 计算
- **状态**: 根据 `signal` 和 `conviction_score` 生成
- **操作**: `signal` (BUY/SELL/HOLD) + `position_size` (仓位大小)
- **描述**: 根据 `conviction_score` 生成

#### 如何有数据
1. **创建Portfolio**（同上）
2. **等待策略执行**（定时或手动）
3. **确保执行成功**（`status = 'completed'`）

---

## 5. Matrix Data Flow 数据展示逻辑

### 数据来源
- 从最新的Agent执行记录中提取数据
- 查询: `agent_execution_recorder.get_latest_executions(db)`

### 数据提取逻辑

#### Macro数据
```python
# 从 macro_agent 的最新执行记录提取
macro_execution = latest_executions.get("macro_agent")
if macro_execution:
    macro_indicators = macro_execution.agent_specific_data.get("macro_indicators", {})
    
    # Fed Rate
    fed_rate = macro_indicators.get("fed_funds_rate", {}).get("value")
    if fed_rate:
        stream_items.append({
            "type": "Macro",
            "text": f"Fed Rate: {fed_rate:.2f}%",
            "trend": "neutral"
        })
    
    # ETF Net Flow
    etf_flow = macro_indicators.get("etf_flow", 0)
    if etf_flow:
        stream_items.append({
            "type": "Macro",
            "text": f"ETF Net Flow: +${etf_flow/1e6:.0f}M" if etf_flow > 0 else f"ETF Net Flow: ${etf_flow/1e6:.0f}M",
            "trend": "up" if etf_flow > 0 else "down"
        })
```

#### OnChain数据
```python
# 从 onchain_agent 的最新执行记录提取
onchain_execution = latest_executions.get("onchain_agent")
if onchain_execution:
    onchain_metrics = onchain_execution.agent_specific_data.get("onchain_metrics", {})
    
    # Active Addresses
    active_addresses = onchain_metrics.get("active_addresses")
    if active_addresses:
        stream_items.append({
            "type": "OnChain",
            "text": f"Active Addresses: {active_addresses/1000:.0f}K",
            "trend": "up" if signal == "BULLISH" else "down" if signal == "BEARISH" else "neutral"
        })
    
    # Exchange Flow
    exchange_flow = onchain_metrics.get("exchange_netflow", 0)
    if exchange_flow:
        stream_items.append({
            "type": "OnChain",
            "text": f"Exchange Flow: {exchange_flow/1000:.0f}K BTC",
            "trend": "up" if exchange_flow < 0 else "down"  # 流出是看涨
        })
```

#### TA数据
```python
# 从 ta_agent 的最新执行记录提取
ta_execution = latest_executions.get("ta_agent")
if ta_execution:
    technical_indicators = ta_execution.agent_specific_data.get("technical_indicators", {})
    
    # RSI
    rsi_value = technical_indicators.get("rsi", {}).get("value")
    if rsi_value:
        stream_items.append({
            "type": "TA",
            "text": f"BTC RSI(14): {rsi_value:.2f}",
            "trend": "up" if rsi_value > 70 else "down" if rsi_value < 30 else "neutral"
        })
    
    # Trend Status
    ema_data = technical_indicators.get("ema", {})
    trend_status = get_trend_status(ema_data)
    if trend_status != "Unknown":
        stream_items.append({
            "type": "TA",
            "text": f"{trend_status} Active",
            "trend": "up" if "Golden" in trend_status or "Bullish" in trend_status else "down" if "Death" in trend_status or "Bearish" in trend_status else "neutral"
        })
```

### 显示规则
1. **只显示有值的数据**（不为None且不为0）
2. **按Agent分组**（Macro, OnChain, TA）
3. **自动判断趋势**（up/down/neutral）
4. **实时更新**（前端30秒轮询）

### 当前未实现的数据
- ❌ Fear & Greed Index（TODO注释中标记）
- ❌ Risk数据
- ❌ Sentiment数据

---

## 总结

### 快速检查清单

1. **Agent有数据但显示N/A**
   - ✅ 检查Agent是否执行过
   - ✅ 检查 `agent_specific_data` 中是否有对应字段
   - ✅ 等待下次Agent执行（4小时或手动触发）

2. **AI Commander没有信息**
   - ✅ 创建Portfolio
   - ✅ 等待策略执行完成
   - ✅ 检查 `StrategyExecution` 表中是否有记录

3. **Active Directive没有信息**
   - ✅ 同上，需要策略执行记录

4. **Matrix Data Flow为空**
   - ✅ 检查三个Agent是否都有执行记录
   - ✅ 检查 `agent_specific_data` 中是否有数据

### 建议改进
1. 在Agent卡片上展示更多数据（risk_assessment, network_health, support/resistance levels）
2. 添加数据更新时间显示
3. 添加数据源状态指示（数据是否可用）
4. 优化N/A的显示逻辑（区分"未执行"和"数据不可用"）

