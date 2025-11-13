# Exploration页面数据映射清单

## 一、页面功能概览

Exploration页面（Mind Hub）是一个实时监控面板，展示三个业务Agent的分析结果、AI Commander的综合决策，以及实时市场情报。

---

## 二、左侧：Squad Decision Core（三个Agent卡片）

### 2.1 MacroAgent - The Oracle（宏观分析Agent）

#### UI显示字段：
1. **Agent名称**: "The Oracle"
2. **权重**: "MacroAgent (40%)"
3. **Score**: `+0.80` (动态更新，范围: -1.0 ~ +1.0)
4. **核心输入指标**:
   - ETF Net Flow: `+$250M` (进度条75%)
   - Fed Cut Prob: `80%` (进度条80%)
5. **LLM结论**: "Global liquidity easing expectations strong, institutional funds continue to flow in."

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **Score** | `agent_executions.score` | ✅ 已有 | 数据库字段：`NUMERIC(5, 2)`，范围 -100 ~ +100，需转换为 -1.0 ~ +1.0 |
| **Reasoning** | `agent_executions.reasoning` | ✅ 已有 | 数据库字段：`Text`，LLM生成的推理过程 |
| **ETF Net Flow** | `agent_executions.agent_specific_data.etf_flow` | ⚠️ 部分 | 需要从外部API获取（CoinGlass/Farside），目前可能缺失 |
| **Fed Cut Prob** | `agent_executions.agent_specific_data.fed_rate_prob` | ⚠️ 部分 | 需要从CME FedWatch API获取，目前可能缺失 |
| **Confidence** | `agent_executions.confidence` | ✅ 已有 | 数据库字段：`NUMERIC(3, 2)`，范围 0.00 ~ 1.00 |
| **Signal** | `agent_executions.signal` | ✅ 已有 | 数据库字段：`BULLISH/BEARISH/NEUTRAL` |
| **执行时间** | `agent_executions.executed_at` | ✅ 已有 | 数据库字段：`TIMESTAMP` |

#### Agent查询但UI未展示的数据：

MacroAgent实际查询和存储的数据（存储在`agent_executions.agent_specific_data.macro_indicators`）：
1. **fed_funds_rate**: 联邦基金利率（从FRED API获取，已实现）✅
2. **m2_growth**: M2货币供应增长率（从FRED API获取，已实现）✅
3. **dxy**: 美元指数DXY（从FRED API获取，已实现）✅
4. **fear_greed**: 恐惧贪婪指数（从Alternative.me API获取，已实现）✅
5. **treasury_yield**: 10年期国债收益率（从FRED API获取，存储在metadata.dgs10_rate）✅
6. **key_factors**: 关键因素列表（LLM生成）
7. **risk_assessment**: 风险评估文本（LLM生成）

**注意**: 
- ETF Net Flow和Fed Cut Prob在UI中显示，但实际MacroAgent使用的是FRED的fed_rate_prob（联邦基金利率实际值，不是降息概率）
- ETF净流量数据目前未采集，需要外部API（CoinGlass/Farside）

#### 数据可用性检查：

| 字段 | 当前状态 | 替代方案 |
|------|---------|---------|
| **ETF Net Flow** | ❌ 未实现 | 可选：使用CoinGecko API的ETF数据（免费，但数据可能不完整）或暂时不显示 |
| **Fed Cut Prob** | ⚠️ 部分实现 | 当前使用FRED的fed_rate_prob（实际利率），不是降息概率。降息概率需要CME FedWatch API（需付费）或使用FRED的利率趋势作为替代指标 |
| **Fed Funds Rate** | ✅ 已实现 | FRED API - DFF系列 |
| **M2 Growth** | ✅ 已实现 | FRED API - M2SL系列 |
| **DXY Index** | ✅ 已实现 | FRED API - DTWEXBGS系列 |
| **Treasury Yield** | ✅ 已实现 | FRED API - DGS10系列 |

#### 需要开发的功能：
- [ ] **API端点**: `GET /api/v1/exploration/squad-decision-core`
  - 查询最新的三个Agent执行结果
  - 返回格式化的数据供前端使用
- [ ] **数据转换**: 将数据库中的score (-100~+100) 转换为UI显示的格式 (-1.0~+1.0)
- [ ] **数据映射**: 
  - ETF Net Flow: 暂时使用0或从market_data_snapshot获取（如果有）
  - Fed Cut Prob: 使用FRED的fed_rate_prob值，或计算利率变化趋势作为替代指标

---

### 2.2 OnChainAgent - Data Warden（链上分析Agent）

#### UI显示字段：
1. **Agent名称**: "Data Warden"
2. **权重**: "OnChainAgent (40%)"
3. **Score**: `+0.70` (动态更新)
4. **核心输入指标**:
   - MVRV Z-Score: `2.5` (进度条60%)
   - Exchange Flow: `-10K BTC` (进度条85%，负值表示流出)
5. **LLM结论**: "On-chain activity healthy, long-term holder accumulation signal strong."

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **Score** | `agent_executions.score` | ✅ 已有 | 数据库字段 |
| **Reasoning** | `agent_executions.reasoning` | ✅ 已有 | 数据库字段 |
| **MVRV Z-Score** | `agent_executions.agent_specific_data.mvrv_z_score` | ⚠️ 部分 | 需要Glassnode API（付费）或替代方案 |
| **Exchange Flow** | `agent_executions.agent_specific_data.exchange_netflow` | ⚠️ 部分 | 需要链上数据API（Glassnode/CryptoQuant） |
| **LTH Change** | `agent_executions.agent_specific_data.lth_supply_change` | ⚠️ 部分 | 长期持有者变化百分比 |
| **Confidence** | `agent_executions.confidence` | ✅ 已有 | 数据库字段 |
| **Signal** | `agent_executions.signal` | ✅ 已有 | 数据库字段 |

#### Agent查询但UI未展示的数据：

OnChainAgent实际查询和存储的数据（存储在`agent_executions.agent_specific_data.onchain_metrics`）：
1. **active_addresses**: 活跃地址数（从Blockchain.info API获取，已实现）✅
2. **daily_transactions**: 每日交易数（从Blockchain.info API获取，已实现）✅
3. **transaction_fees_sat_vb**: 交易费用（从Mempool.space API获取，已实现）✅
4. **mempool_tx_count**: Mempool待处理交易数（从Mempool.space API获取，已实现）✅
5. **nvt_ratio**: NVT比率（简化计算，从Blockchain.info数据计算）✅
6. **hash_rate_eh**: 哈希率（从Blockchain.info API获取，已实现）✅
7. **network_health**: 网络健康状态（HEALTHY/MODERATE/CONGESTED，LLM判断）✅
8. **key_observations**: 关键观察列表（LLM生成）

**注意**: 
- MVRV Z-Score在UI中显示，但实际OnChainAgent使用的是简化的NVT比率（免费计算）
- Exchange Flow在UI中显示，但实际OnChainAgent没有直接获取交易所流量数据
- LTH Change在UI中显示，但实际OnChainAgent没有长期持有者变化数据

#### 数据可用性检查：

| 字段 | 当前状态 | 替代方案 |
|------|---------|---------|
| **MVRV Z-Score** | ❌ 未实现 | 使用简化的NVT比率替代（已实现），或使用Blockchain.info的市值数据计算近似值 |
| **Exchange Flow** | ❌ 未实现 | 暂时不显示，或使用Mempool交易量变化作为替代指标 |
| **LTH Change** | ❌ 未实现 | 暂时不显示，或使用活跃地址数变化趋势作为替代指标 |
| **Active Addresses** | ✅ 已实现 | Blockchain.info API - 免费 |
| **Transaction Count** | ✅ 已实现 | Blockchain.info API - 免费 |
| **Transaction Fees** | ✅ 已实现 | Mempool.space API - 免费 |
| **Mempool Stats** | ✅ 已实现 | Mempool.space API - 免费 |
| **Hash Rate** | ✅ 已实现 | Blockchain.info API - 免费 |
| **NVT Ratio** | ✅ 已实现 | 从Blockchain.info数据计算 - 免费 |

#### 需要开发的功能：
- [ ] **数据映射**: 
  - MVRV Z-Score: 使用NVT比率替代，或计算近似值
  - Exchange Flow: 暂时显示为"N/A"或使用Mempool数据作为替代
  - LTH Change: 暂时显示为"N/A"或使用活跃地址趋势作为替代

---

### 2.3 TAAgent - Momentum Scout（技术分析Agent）

#### UI显示字段：
1. **Agent名称**: "Momentum Scout"
2. **权重**: "TAAgent (20%)"
3. **Score**: `+0.50` (动态更新)
4. **核心输入指标**:
   - RSI(14): `75` (进度条75%)
   - Trend Status: `Golden Cross` (Badge显示)
5. **LLM结论**: "Technical trend bullish, but short-term overbought risk requires caution."

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **Score** | `agent_executions.score` | ✅ 已有 | 数据库字段 |
| **Reasoning** | `agent_executions.reasoning` | ✅ 已有 | 数据库字段 |
| **RSI(14)** | `agent_executions.agent_specific_data.rsi` | ✅ 已有 | 通过`/api/v1/market/indicators`计算，存储在agent_specific_data |
| **EMA交叉** | `agent_executions.agent_specific_data.ema` | ✅ 已有 | 通过`IndicatorCalculator`计算，判断Golden Cross/Death Cross |
| **MACD** | `agent_executions.agent_specific_data.macd` | ✅ 已有 | 技术指标计算 |
| **Bollinger Bands** | `agent_executions.agent_specific_data.bollinger_bands` | ✅ 已有 | 技术指标计算 |
| **Confidence** | `agent_executions.confidence` | ✅ 已有 | 数据库字段 |
| **Signal** | `agent_executions.signal` | ✅ 已有 | 数据库字段 |

#### Agent查询但UI未展示的数据：

TAAgent实际查询和存储的数据（存储在`agent_executions.agent_specific_data.technical_indicators`）：
1. **ema**: EMA指标对象
   - ema_9, ema_20, ema_50, ema_200的值和相对价格位置（above/below）
   - trend: 趋势方向（bullish/bearish）
   - 各EMA的权重（weight）
2. **rsi**: RSI指标对象
   - value: RSI值（0-100）
   - status: 状态（oversold/neutral/overbought）
   - impact: 影响（BULLISH/BEARISH/NEUTRAL）
   - weight: 权重
3. **macd**: MACD指标对象
   - macd: MACD线值
   - signal: 信号线值
   - histogram: 柱状图值
   - status: 状态（bullish_crossover/bearish_crossover/neutral）
   - impact: 影响（BULLISH/BEARISH/NEUTRAL）
   - weight: 权重
4. **bollinger_bands**: 布林带对象
   - upper, middle, lower: 上中下轨
   - price_position: 价格位置（upper/middle/lower）
   - bandwidth: 带宽（normal/wide/narrow）
   - impact: 影响（BULLISH/BEARISH/NEUTRAL）
   - weight: 权重
5. **support_levels**: 支撑位数组（LLM识别）
6. **resistance_levels**: 阻力位数组（LLM识别）
7. **trend_analysis**: 趋势分析文本（LLM生成）
8. **key_patterns**: 关键模式列表（LLM识别）

**注意**: 
- UI只显示了RSI和Trend Status（Golden Cross），但实际TAAgent提供了更丰富的技术指标数据

#### 数据可用性检查：

| 字段 | 当前状态 | 说明 |
|------|---------|------|
| **RSI** | ✅ 已实现 | 从OHLCV数据计算，存储在agent_specific_data |
| **EMA** | ✅ 已实现 | 从OHLCV数据计算，存储在agent_specific_data |
| **MACD** | ✅ 已实现 | 从OHLCV数据计算，存储在agent_specific_data |
| **Bollinger Bands** | ✅ 已实现 | 从OHLCV数据计算，存储在agent_specific_data |
| **Support/Resistance** | ✅ 已实现 | LLM识别，存储在agent_specific_data |
| **Trend Status** | ⚠️ 需计算 | 需要从EMA数据判断Golden Cross/Death Cross |

#### 需要开发的功能：
- [ ] **趋势状态判断**: 
  - 从EMA数据判断Golden Cross（EMA-9 > EMA-20 > EMA-50）或Death Cross
  - 将趋势状态存储到`agent_specific_data.trend_status`或实时计算
- [ ] **数据格式化**: 确保RSI值正确显示在UI上

---

## 三、中间：AI Commander Analysis

### 3.1 AI Commander卡片

#### UI显示字段：
1. **Commander名称**: "Commander Nova"
2. **状态**: "ONLINE" (Badge)
3. **Conviction Score**: `75` (0-100范围)
4. **Conviction等级**: "🔥 Strong" (Badge)
5. **市场分析总结**: 综合三个Agent的分析，生成一段文字总结
6. **AI头像**: 图片显示

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **Conviction Score** | `strategy_executions.conviction_score` | ✅ 已有 | 数据库字段：`Float`，范围 0-100 |
| **市场分析总结** | `strategy_executions.llm_summary` | ✅ 已有 | 数据库字段：`Text`，LLM生成的总结 |
| **Signal** | `strategy_executions.signal` | ✅ 已有 | 数据库字段：`BUY/SELL/HOLD/PAUSE` |
| **Signal Strength** | `strategy_executions.signal_strength` | ✅ 已有 | 数据库字段：`Float` |
| **Risk Level** | `strategy_executions.risk_level` | ✅ 已有 | 数据库字段：`String` |

#### 需要开发的功能：
- [ ] **API端点**: `GET /api/v1/exploration/commander-analysis`
  - 查询最新的策略执行记录（按用户或全局）
  - 返回Conviction Score和LLM总结
- [ ] **Conviction等级映射**: 
  - 0-40: "Weak"
  - 40-70: "Moderate"
  - 70-100: "Strong"
- [ ] **多策略支持**: 如果用户有多个策略实例，需要选择显示哪个（或显示最新/最活跃的）

---

### 3.2 Active Directive（当前指令）

#### UI显示字段：
1. **策略名称**: "HODL-Wave Squad" (Badge)
2. **策略副标题**: "Macro Swing Strategy"
3. **倒计时**: `01:35:50` (格式: HH:MM:SS，4小时周期)
4. **当前动作**: "Accelerate Accumulation" (状态文本)
5. **交易指令**: "BUY 0.75% BTC" (动作类型 + 百分比 + 资产)
6. **说明**: "All agents aligned • Maximum confidence deployment"

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **策略名称** | `strategy_definitions.display_name` | ✅ 已有 | 数据库字段 |
| **策略副标题** | `strategy_definitions.description` | ✅ 已有 | 数据库字段 |
| **Signal** | `strategy_executions.signal` | ✅ 已有 | BUY/SELL/HOLD/PAUSE |
| **Position Size** | `strategy_executions.position_size` | ✅ 已有 | 数据库字段：`Float`，持仓比例 |
| **Conviction Score** | `strategy_executions.conviction_score` | ✅ 已有 | 数据库字段 |
| **执行时间** | `strategy_executions.execution_time` | ✅ 已有 | 数据库字段：`TIMESTAMP` |
| **倒计时** | 计算字段 | ⚠️ 需开发 | 基于执行时间和策略周期（默认4小时）计算剩余时间 |

#### 需要开发的功能：
- [ ] **倒计时计算**: 
  - 获取策略执行周期（从`strategy_definitions.execution_interval`或默认4小时）
  - 计算：`剩余时间 = 执行周期 - (当前时间 - 上次执行时间)`
- [ ] **状态文本映射**:
  - BUY + Conviction > 70: "Accelerate Accumulation"
  - BUY + Conviction 40-70: "Gradual Accumulation"
  - HOLD: "Hold Position"
  - SELL: "Reduce Exposure"
  - PAUSE: "Defensive Mode"
- [ ] **交易指令格式化**: 
  - 从`signal`和`position_size`生成 "BUY 0.75% BTC" 格式
  - 需要知道交易资产（从策略定义或市场数据获取）

---

### 3.3 Directive History（指令历史）

#### UI显示字段：
1. **历史记录列表**: 显示最近100条指令
2. **每条记录包含**:
   - 策略名称和副标题
   - 时间戳（格式: "Xd Yh ago"）
   - 状态（"Accelerate Accumulation", "Reduce Exposure"等）
   - 动作（BUY/SELL/HOLD + 百分比 + 资产）
   - Conviction分数（Badge显示，颜色根据分数变化）
   - 结果（"+2.5%" 或 "-1.2%"，表示执行后的收益）

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **策略名称** | `strategy_definitions.display_name` | ✅ 已有 | 关联查询 |
| **执行时间** | `strategy_executions.execution_time` | ✅ 已有 | 数据库字段 |
| **Signal** | `strategy_executions.signal` | ✅ 已有 | 数据库字段 |
| **Position Size** | `strategy_executions.position_size` | ✅ 已有 | 数据库字段 |
| **Conviction Score** | `strategy_executions.conviction_score` | ✅ 已有 | 数据库字段 |
| **执行结果** | `trades`表关联查询 | ⚠️ 需开发 | 需要计算执行后的收益百分比 |

#### 需要开发的功能：
- [ ] **API端点**: `GET /api/v1/exploration/directive-history`
  - 查询最近100条策略执行记录
  - 关联查询策略定义信息
  - 计算每条记录的执行结果（收益百分比）
- [ ] **时间戳格式化**: 将`execution_time`转换为相对时间（"2d 5h ago"）
- [ ] **收益计算**: 
  - 查询执行后的交易记录（`trades`表）
  - 计算：`收益 = (当前持仓价值 - 执行时持仓价值) / 执行时持仓价值 * 100`
  - 如果还没有交易记录，显示 "-" 或 "Pending"

---

## 四、右侧：Real-Time Intel（实时情报）

### 4.1 Sentiment Filter（情绪过滤器）

#### UI显示字段：
1. **Fear & Greed Index**: `20 - Extreme Fear` (Badge)
2. **进度条**: 20% (红色)
3. **警告信息**: "⚠️ Sentiment Filter Active: Extreme fear detected, strategy conservatively de-weighted by 10%."

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **Fear & Greed Index** | `/api/v1/market/fear-greed` | ✅ 已有 | Alternative.me API，已实现 |
| **Value** | `fear_greed_index.value` | ✅ 已有 | 0-100范围 |
| **Classification** | `fear_greed_index.classification` | ✅ 已有 | "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed" |
| **降权逻辑** | `conviction_calculator._calculate_risk_factor` | ✅ 已有 | 如果fear_index < 20，降权30% |

#### 需要开发的功能：
- [ ] **实时更新**: 前端每3秒轮询`/api/v1/market/fear-greed`获取最新数据
- [ ] **降权提示**: 如果fear_index < 20，显示警告信息

---

### 4.2 Matrix Data Flow（数据流）

#### UI显示字段：
1. **实时数据流**: 滚动显示不同类型的数据更新
2. **数据项格式**: `[类型] 数据内容 趋势图标`
3. **数据类型**:
   - Macro: "CME Rate Prob: 80%", "ETF Net Flow: +$250M"
   - OnChain: "LTH Change: +2.01%", "Exchange Flow: -10,000 BTC"
   - TA: "BTC RSI(14): 75.25", "Golden Cross Active"
   - Risk: "ATR Volatility: 6.1% [High Freq]"
   - Sentiment: "Fear & Greed: 20 [Extreme Fear]"

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **Macro数据** | `agent_executions.agent_specific_data` (macro_agent) | ✅ 已有 | 从最新MacroAgent执行结果获取 |
| **OnChain数据** | `agent_executions.agent_specific_data` (onchain_agent) | ✅ 已有 | 从最新OnChainAgent执行结果获取 |
| **TA数据** | `agent_executions.agent_specific_data` (ta_agent) | ✅ 已有 | 从最新TAAgent执行结果获取 |
| **Fear & Greed** | `/api/v1/market/fear-greed` | ✅ 已有 | 实时API |
| **波动率** | `market_data_snapshot` | ⚠️ 需开发 | 需要计算ATR或24h波动率 |

#### 需要开发的功能：
- [ ] **API端点**: `GET /api/v1/exploration/data-stream`
  - 返回格式化的数据流数组
  - 包含类型、文本、趋势（up/down/neutral）
- [ ] **数据格式化**: 
  - Macro: "ETF Net Flow: +$250M" (从agent_specific_data.etf_flow格式化)
  - OnChain: "Exchange Flow: -10K BTC" (从agent_specific_data.exchange_netflow格式化)
  - TA: "RSI(14): 75" (从agent_specific_data.rsi格式化)
- [ ] **趋势判断**: 
  - 根据数值变化判断up/down/neutral
  - 需要对比历史数据（或使用agent的signal）

---

### 4.3 External Intelligence Feed（外部情报流）

#### UI显示字段：
1. **Twitter/X推文列表**: 显示相关KOL的推文（暂时使用假数据）

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **Twitter数据** | 假数据 | ⚠️ 暂时不接真实数据 | 根据用户要求，暂时不集成Twitter API |

#### 需要开发的功能：
- [ ] **暂时不开发**: 根据用户要求，External Intelligence Feed暂时不接真实数据，保持假数据

---

## 五、页面顶部功能

### 5.1 策略选择器

#### UI显示字段：
1. **当前选中策略**: "HODL-Wave Squad"
2. **下拉选项**: 
   - HODL-Wave Squad (可用)
   - ArbitrageX Squad (锁定)
   - MomentumPro Squad (锁定)
   - StableGuard Squad (锁定)
   - DeFiYield Squad (锁定)
   - AIPredict Squad (锁定)

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **策略列表** | `strategy_definitions` | ✅ 已有 | 数据库表 |
| **策略状态** | `strategy_definitions.is_active` | ✅ 已有 | 数据库字段 |
| **用户权限** | `user.role` 或策略实例权限 | ⚠️ 需开发 | 需要检查用户是否有权限使用该策略 |

#### 需要开发的功能：
- [ ] **API端点**: `GET /api/v1/exploration/available-strategies`
  - 返回所有已激活的策略列表（不判断权限，所有用户可见）
  - 标记哪些已激活（is_active=true）
- [ ] **策略切换**: 切换策略后，更新页面显示的数据（Agent结果、指令等）

---

### 5.2 LIVE状态指示器

#### UI显示字段：
1. **LIVE Badge**: 显示"LIVE"文字和脉冲动画
2. **状态**: 根据轮询刷新是否正常执行判断是否"LIVE"

#### 数据来源分析：

| 字段 | 数据来源 | 状态 | 说明 |
|------|---------|------|------|
| **轮询状态** | 前端轮询机制 | ⚠️ 需开发 | 前端每30秒轮询一次，如果轮询正常执行则显示LIVE |
| **最后更新时间** | API响应中的timestamp | ✅ 已有 | 从API响应获取，用于显示最后更新时间 |

#### 需要开发的功能：
- [ ] **前端轮询机制**: 
  - 每30秒轮询一次所有API端点
  - 如果轮询正常执行（无错误），显示LIVE状态
  - 如果轮询失败或超时，显示错误状态
- [ ] **API响应时间戳**: 
  - 所有API端点返回`last_updated`字段
  - 前端显示最后更新时间

---

## 六、数据获取优先级

### 6.1 可直接获取的数据（✅ 已完成）

1. **Agent执行结果**:
   - Score, Confidence, Signal, Reasoning
   - 从`agent_executions`表查询
   - API: `GET /api/v1/exploration/squad-decision-core` (需创建)

2. **技术指标**:
   - RSI, EMA, MACD, Bollinger Bands
   - 从`agent_executions.agent_specific_data`获取
   - 或从`/api/v1/market/indicators`实时计算

3. **Fear & Greed Index**:
   - 从`/api/v1/market/fear-greed`获取
   - 已实现Alternative.me API集成

4. **策略执行记录**:
   - Conviction Score, Signal, Position Size
   - 从`strategy_executions`表查询

5. **市场数据快照**:
   - BTC/ETH价格
   - 从`/api/v1/market/snapshot`获取

---

### 6.2 需要开发的数据采集（⚠️ 待实现）

1. **ETF净流量**:
   - 数据源: CoinGlass API 或 Farside Investors
   - 优先级: 高（MacroAgent核心指标）
   - 实现难度: 中等（需要API集成）

2. **CME FedWatch降息概率**:
   - 数据源: CME Group API
   - 优先级: 高（MacroAgent核心指标）
   - 实现难度: 中等（需要API集成）

3. **链上指标**:
   - MVRV Z-Score: Glassnode API（付费）或替代方案
   - 交易所净流量: Glassnode/CryptoQuant API
   - 长期持有者变化: Glassnode API
   - 优先级: 高（OnChainAgent核心指标）
   - 实现难度: 高（需要付费API或寻找免费替代）

4. **Twitter推文**:
   - 数据源: Twitter API v2 或第三方服务
   - 优先级: 低（非核心功能）
   - 实现难度: 高（需要API密钥和认证）

---

### 6.3 需要计算/格式化的数据（⚠️ 待实现）

1. **倒计时**: 基于执行时间和策略周期计算
2. **收益百分比**: 基于交易记录计算
3. **趋势判断**: 基于数据变化判断up/down/neutral
4. **状态文本映射**: 基于Signal和Conviction Score生成
5. **时间戳格式化**: 转换为相对时间（"2d 5h ago"）

---

## 七、API端点开发清单

### 7.1 必须实现的端点

1. **`GET /api/v1/exploration/squad-decision-core`**
   - 返回三个Agent的最新执行结果
   - 包含Score, Confidence, Reasoning, 核心指标
   - 响应时间: < 200ms

2. **`GET /api/v1/exploration/commander-analysis`**
   - 返回AI Commander的综合分析
   - 包含Conviction Score, LLM总结, Signal
   - 响应时间: < 200ms

3. **`GET /api/v1/exploration/active-directive`**
   - 返回当前活跃的指令
   - 包含策略信息, Signal, Position Size, 倒计时
   - 响应时间: < 200ms

4. **`GET /api/v1/exploration/directive-history`**
   - 返回最近100条指令历史
   - 包含策略信息, 执行结果, 收益百分比
   - 响应时间: < 500ms

5. **`GET /api/v1/exploration/data-stream`**
   - 返回格式化的数据流数组
   - 包含Macro, OnChain, TA, Risk, Sentiment数据
   - 响应时间: < 200ms

6. **`GET /api/v1/exploration/available-strategies`**
   - 返回用户可用的策略列表
   - 标记解锁/锁定状态
   - 响应时间: < 200ms

---

### 7.2 可选实现的端点

1. **`GET /api/v1/exploration/twitter-feed`**
   - 返回Twitter推文列表
   - 优先级: 低

2. **`GET /api/v1/exploration/live-status`**
   - 返回LIVE状态和最后更新时间
   - 优先级: 低（可以在其他端点中返回）

---

## 八、开发优先级建议

### Phase 1: 核心功能（高优先级）
1. ✅ 实现`/squad-decision-core`端点
2. ✅ 实现`/commander-analysis`端点
3. ✅ 实现`/active-directive`端点
4. ✅ 实现倒计时计算
5. ✅ 实现状态文本映射

### Phase 2: 数据采集增强（中优先级）
1. ⚠️ 集成ETF净流量API（CoinGlass/Farside）
2. ⚠️ 集成CME FedWatch API
3. ⚠️ 集成链上数据API（Glassnode或替代方案）

### Phase 3: 历史记录和高级功能（中优先级）
1. ⚠️ 实现`/directive-history`端点
2. ⚠️ 实现收益百分比计算
3. ⚠️ 实现`/data-stream`端点

### Phase 4: 外部集成（低优先级）
1. ⚠️ 集成Twitter API
2. ⚠️ 实现策略切换功能

---

## 九、数据库查询优化建议

1. **索引优化**:
   - `agent_executions`表已有索引：`idx_agent_executions_latest`
   - 确保`strategy_executions.execution_time`有索引
   - 确保`strategy_executions.portfolio_id`有索引

2. **查询优化**:
   - 使用`LIMIT 1`和`ORDER BY executed_at DESC`获取最新记录
   - 使用`JOIN`关联查询策略定义信息
   - 考虑使用Redis缓存最新数据（TTL: 30秒）

3. **数据聚合**:
   - 考虑在`agent_executions`表中添加计算字段（如趋势状态）
   - 或使用视图（View）预计算常用查询

---

## 十、前端集成建议

1. **实时更新**:
   - 使用WebSocket或Server-Sent Events (SSE)推送实时更新
   - 或使用轮询（每3-5秒）获取最新数据

2. **数据缓存**:
   - 前端缓存最新数据，避免频繁请求
   - 使用React Query或SWR管理数据获取和缓存

3. **错误处理**:
   - 如果API失败，显示缓存的旧数据
   - 显示错误提示和重试按钮

---

## 十一、总结

### 已完成的功能：
- ✅ Agent执行结果存储（`agent_executions`表）
- ✅ 策略执行记录存储（`strategy_executions`表）
- ✅ Fear & Greed Index API集成
- ✅ 技术指标计算（RSI, EMA, MACD等）
- ✅ 市场数据快照API

### 需要开发的功能：
- ⚠️ Exploration页面专用API端点（6个核心端点）
- ⚠️ ETF净流量数据采集
- ⚠️ CME FedWatch降息概率采集
- ⚠️ 链上数据采集（MVRV, Exchange Flow等）
- ⚠️ 倒计时和收益计算逻辑
- ⚠️ Twitter推文集成（可选）

### 数据可用性：
- **可直接使用**: 60%的数据已可从数据库获取
- **需要API集成**: 30%的数据需要外部API
- **需要计算**: 10%的数据需要计算/格式化

