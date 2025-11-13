# Multi-Agent架构设计

> 版本: 2.0  
> 更新日期: 2025-11-05  
> 目标: 详细解释三层Agent架构的运作逻辑

---

## 一、架构总览

### 1.1 三层架构设计理念

**设计哲学**: 分层解耦 + 职责单一 + 并行优化

```
用户触发方式：
┌─────────────────┐     ┌─────────────────┐
│  用户主动对话   │     │  策略定时触发   │
│ (SuperAgent)    │     │ (直达分析层)    │
└────────┬────────┘     └────────┬────────┘
         ↓                       ↓
┌────────────────────────────────────────┐
│    System Layer (系统层)                │
│  仅用户对话时触发                       │
│  ┌──────────┐    ┌──────────┐         │
│  │SuperAgent│ →  │Planning  │         │
│  └──────────┘    └──────────┘         │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│    Analysis Layer (分析层)              │
│  核心智能 - 并行执行                    │
│  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │Macro │  │OnChain│  │  TA  │        │
│  │ 40%  │  │ 40%  │  │ 20%  │        │
│  └──────┘  └──────┘  └──────┘        │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│    Decision Layer (决策层)              │
│  汇总结果 + 生成信号                    │
│  ┌────────────┐   ┌────────────┐      │
│  │Conviction  │ → │  Signal    │      │
│  │Calculator  │   │ Generator  │      │
│  └────────────┘   └────────────┘      │
└────────────────────────────────────────┘
```

### 1.2 核心设计原则

| 原则 | 含义 | 实现方式 |
|-----|------|---------|
| **职责单一** | 每个Agent只做一件事 | MacroAgent只分析宏观，不碰技术指标 |
| **并行优化** | 独立Agent并行执行 | 3个分析Agent同时调用LLM |
| **状态共享** | Agent间通过状态机通信 | LangGraph State传递数据 |
| **容错设计** | 单Agent失败不影响整体 | 缺失数据可降级决策 |
| **可追溯性** | 每步决策可回溯 | 记录所有Agent输入输出 |

---

## 二、System Layer 设计（系统层）

### 2.1 角色定位

**触发条件**: **仅当用户主动对话时触发**

**职责**:
1. 理解用户自然语言意图
2. 将意图转换为Agent调用计划
3. 协调Agent执行
4. 将结果转换为自然语言返回

**不触发场景**:
- ❌ 策略定时执行（直接到分析层）
- ❌ 系统自动任务

---

### 2.2 SuperAgent 详细设计

#### 2.2.1 功能职责

**输入**: 用户自然语言问题
- "分析一下BTC当前行情"
- "我的投资组合表现如何？"
- "HODL策略最近赚了多少？"

**输出**: 结构化意图
```python
{
    "intent_type": "ANALYZE_MARKET",  # 意图类型
    "entities": {
        "asset": "BTC",
        "timeframe": "current"
    },
    "confidence": 0.95  # 意图识别置信度
}
```

#### 2.2.2 意图分类体系

| 意图类型 | 描述 | 需要调用的Agent |
|---------|------|----------------|
| `ANALYZE_MARKET` | 分析市场行情 | Macro + OnChain + TA |
| `QUERY_PORTFOLIO` | 查询投资组合 | 无（直接查数据库） |
| `ADJUST_STRATEGY` | 调整策略参数 | RiskManager（未来） |
| `EXPLAIN_DECISION` | 解释历史决策 | 无（查历史记录） |
| `GENERAL_CHAT` | 闲聊 | 仅SuperAgent回复 |

#### 2.2.3 Prompt设计原则

**SuperAgent Prompt结构**:
```
[角色定义]
你是AutoMoney的AI投资顾问

[能力边界]
- 可以：分析市场、解释策略
- 不可以：给出绝对建议、保证收益

[输出格式]
JSON格式，包含intent_type和entities

[示例]
用户: "BTC现在能买吗？"
输出: {"intent_type": "ANALYZE_MARKET", "entities": {"asset": "BTC"}}
```

---

### 2.3 PlanningAgent 详细设计

#### 2.3.1 功能职责

**输入**: SuperAgent识别的意图

**输出**: Agent执行计划
```python
{
    "agents": ["MacroAgent", "OnChainAgent", "TAAgent"],
    "execution_mode": "parallel",  # 并行执行
    "timeout": 15,  # 超时时间（秒）
    "fallback_strategy": "use_cache"  # 失败降级策略
}
```

#### 2.3.2 决策规则表

| 意图类型 | Agent组合 | 执行方式 | 决策层 |
|---------|----------|---------|--------|
| `ANALYZE_MARKET` | Macro+OnChain+TA | 并行 | ✅ 需要 |
| `QUERY_PORTFOLIO` | 无 | 直接查询 | ❌ 不需要 |
| `ADJUST_STRATEGY` | RiskManager | 串行 | ⚠️ 可选 |

#### 2.3.3 并行 vs 串行决策逻辑

**并行执行条件**:
- ✅ Agent间无依赖关系
- ✅ 可以同时调用LLM
- ✅ 示例：MacroAgent和OnChainAgent独立

**串行执行条件**:
- ✅ Agent有前后依赖
- ✅ 后续Agent需要前者结果
- ✅ 示例：DecisionAgent需等待所有分析完成

---

## 三、Analysis Layer 设计（分析层）

### 3.1 通用Agent设计规范

#### 3.1.1 标准输入格式

所有分析Agent遵循统一接口：

```python
class AgentInput:
    timestamp: datetime        # 分析时间
    market_data: dict          # 市场数据
    context: dict              # 上下文（可选）
```

#### 3.1.2 标准输出格式

```python
class AgentOutput:
    score: float               # -1.0 ~ +1.0
    confidence: float          # 0 ~ 1 (置信度)
    reasoning: str             # LLM推理过程
    signals: dict              # 细分信号
    execution_time: int        # 执行耗时（ms）
    tokens_used: int           # LLM Token消耗
```

**关键字段说明**:
- **score**: 标准化分数，-1极度看空，+1极度看多，0中性
- **confidence**: 对这个判断的确信程度（数据质量）
- **reasoning**: 可读的推理过程，给用户展示透明度

---

### 3.2 MacroAgent 详细设计

#### 3.2.1 职责定义

**专注领域**: 宏观经济环境对加密市场的影响

**输入数据来源**:
| 指标 | 数据源 | 更新频率 | 权重 |
|-----|--------|---------|------|
| ETF净流入 | CoinGlass API | 日 | 35% |
| CME期货持仓 | CME Group API | 周 | 20% |
| 美联储利率预期 | FRED API | 日 | 30% |
| 全球M2增长率 | FRED API | 月 | 15% |

#### 3.2.2 评分逻辑规则

**规则引擎**（在LLM推理前预处理）:

```python
def preprocess_macro_data(data):
    score_components = []
    
    # 规则1: ETF流量
    if data.etf_net_flow > 100_000_000:  # >$100M
        score_components.append(0.35)  # 强烈看多
    elif data.etf_net_flow < -100_000_000:
        score_components.append(-0.35)  # 强烈看空
    else:
        score_components.append(0)  # 中性
    
    # 规则2: 降息预期
    if data.fed_rate_cut_prob > 70:
        score_components.append(0.30)  # 宽松预期
    elif data.fed_rate_cut_prob < 30:
        score_components.append(-0.30)  # 紧缩预期
    
    # ... 其他规则
    
    return sum(score_components)
```

**LLM角色**:
- 不是计算score（规则已算好）
- 是解释为什么这个score合理
- 是综合考虑规则未覆盖的因素

#### 3.2.3 Prompt设计（简化版）

```
你是宏观经济分析师，评估加密市场宏观环境。

输入数据：
- ETF净流入: {etf_flow}
- 降息概率: {rate_prob}%
- M2增长: {m2_growth}%

规则引擎已计算初步score: {preliminary_score}

请你：
1. 验证这个score是否合理
2. 考虑规则未覆盖的因素（地缘政治、突发事件等）
3. 给出最终score（可微调±0.2）
4. 用3-5句话解释reasoning

输出JSON格式。
```

---

### 3.3 OnChainAgent 详细设计

#### 3.3.1 职责定义

**专注领域**: 区块链链上数据的健康度

**输入数据**:
| 指标 | 数据源 | 更新频率 | 意义 |
|-----|--------|---------|------|
| MVRV Z-Score | Glassnode | 日 | 估值水平 |
| NVT Ratio | Glassnode | 日 | 网络价值 |
| 交易所流量 | Glassnode | 小时 | 抛压/囤币 |
| 长期持有者变化 | Glassnode | 日 | 聪明钱行为 |
| 活跃地址数 | Glassnode | 日 | 网络活跃度 |

#### 3.3.2 关键指标解读规则

**MVRV Z-Score阈值**:
- **>7**: 🔴 泡沫区，历史顶部信号
- **3-7**: 🟡 过热区，谨慎
- **1-3**: 🟢 健康区，正常估值
- **<1**: 🔵 低估区，历史底部信号

**交易所净流量**:
- **大量流出（<-10,000 BTC/天）**: 🟢 看涨（囤币行为）
- **大量流入（>+10,000 BTC/天）**: 🔴 看跌（准备卖出）

**长期持有者（LTH）变化**:
- **持续增持（>+2%）**: 🟢 强烈看涨
- **持续减持（<-2%）**: 🔴 强烈看跌

#### 3.3.3 与MacroAgent的互补关系

| 场景 | MacroAgent | OnChainAgent | 结论 |
|-----|-----------|--------------|------|
| **牛市顶部** | 看多（ETF流入） | 看空（MVRV>7） | 决策层会降权 |
| **熊市底部** | 看空（恐慌） | 看多（MVRV<1） | 决策层识别机会 |
| **震荡市** | 中性 | 中性 | 等待明确信号 |

---

### 3.4 TAAgent 详细设计

#### 3.4.1 职责定义

**专注领域**: 技术分析和市场趋势

**输入数据**:
| 指标 | 计算方式 | 周期 | 意义 |
|-----|---------|------|------|
| EMA21/EMA55 | 本地计算 | 周线 | 趋势方向 |
| RSI(14) | 本地计算 | 周线 | 超买/超卖 |
| MACD | 本地计算 | 周线 | 动能强度 |
| Bollinger Bands | 本地计算 | 周线 | 波动率 |

#### 3.4.2 技术指标优先级

**主要指标** (权重70%):
1. **EMA金叉/死叉**: 趋势确认
   - EMA21上穿EMA55: 🟢 金叉（看涨）
   - EMA21下穿EMA55: 🔴 死叉（看跌）

2. **RSI超买/超卖**:
   - RSI>70: ⚠️ 超买（警惕回调）
   - RSI<30: ✅ 超卖（关注机会）
   - RSI 40-60: 🟢 健康区间

**辅助指标** (权重30%):
3. **MACD柱状图**: 动能变化
4. **Bollinger Bands**: 波动率判断

#### 3.4.3 为什么权重只有20%？

**理由**:
1. **滞后性**: 技术指标基于历史价格，滞后于基本面
2. **噪音多**: 短期技术面容易被操纵
3. **长期视角**: 本项目是中长期策略（4小时周期），不是高频交易

**但不能没有TA**:
- TA用于**确认趋势**，不是主导决策
- TA用于**识别超买超卖**，做风险控制
- TA用于**提供进场时机**，优化成本

---

## 四、Decision Layer 设计（决策层）

### 4.1 ConvictionCalculator 设计

#### 4.1.1 核心公式

**Step 1: 加权汇总**
```
Base Score = Macro * 0.4 + OnChain * 0.4 + TA * 0.2
```
范围: -1.0 ~ +1.0

**Step 2: 归一化到0-100**
```
Conviction Score = (Base Score + 1) * 50
```
范围: 0 ~ 100

**Step 3: 风险调整**
```python
if volatility > 6%:
    Conviction Score *= 0.8  # 高波动降权20%

if fear_index < 20:
    Conviction Score *= 0.7  # 极度恐慌降权30%

if MVRV > 7:
    Conviction Score *= 0.5  # 泡沫区强制降权50%
```

**Step 4: 截断**
```
Final Score = max(0, min(100, Adjusted Score))
```

#### 4.1.2 示例计算

**场景**: 宏观看多、链上健康、技术超买

```
输入:
- Macro Score: +0.8 (看多)
- OnChain Score: +0.7 (健康)
- TA Score: -0.2 (超买警惕)

计算:
Base = 0.8*0.4 + 0.7*0.4 + (-0.2)*0.2
     = 0.32 + 0.28 - 0.04
     = 0.56

Normalized = (0.56 + 1) * 50 = 78

风险调整:
- 波动率5%（正常）: 不调整
- 恐慌指数65（正常）: 不调整
- MVRV 2.5（健康）: 不调整

Final Conviction Score = 78
```

**结论**: 78 > 70，生成BUY信号

---

### 4.2 SignalGenerator 设计

#### 4.2.1 信号规则

**主规则** (基于Conviction Score):
| Score范围 | 信号 | 仓位建议 | 说明 |
|----------|------|---------|------|
| **>70** | BUY | 0.5-0.75% | 强信念买入 |
| **40-70** | HOLD | 维持 | 中性观望 |
| **<40** | SELL | 减仓50% | 看空减仓 |

**熔断规则** (优先级最高):
| 条件 | 动作 | 理由 |
|-----|------|------|
| Fear Index < 20 | 强制SELL | 极度恐慌，止损 |
| MVRV > 7 | 强制SELL | 泡沫区，获利了结 |
| 波动率 > 10% | 暂停交易 | 风险过高 |

#### 4.2.2 仓位管理规则

**动态仓位计算**:
```python
def calculate_position_size(conviction_score, current_capital):
    # 基础仓位
    if conviction_score > 80:
        base_ratio = 0.0075  # 0.75%
    elif conviction_score > 70:
        base_ratio = 0.005   # 0.5%
    else:
        base_ratio = 0.0025  # 0.25%
    
    # 风险调整
    if volatility > 6%:
        base_ratio *= 0.5  # 高波动减半
    
    return current_capital * base_ratio
```

**单笔交易限制**:
- 最大仓位: 5% (防止单笔巨亏)
- 最小仓位: $100 (避免手续费占比过高)

---

## 五、LangGraph工作流实现

### 5.1 状态机定义

**StrategyState结构**:
```python
class StrategyState(TypedDict):
    # 输入数据
    strategy_id: str
    user_id: str
    market_data: dict
    
    # 分析层输出
    macro_score: float | None
    macro_reasoning: str | None
    onchain_score: float | None
    onchain_reasoning: str | None
    ta_score: float | None
    ta_reasoning: str | None
    
    # 决策层输出
    conviction_score: float | None
    signal: str | None  # BUY/SELL/HOLD
    reasoning: str | None
    
    # 元数据
    timestamp: datetime
    errors: list[str]
```

### 5.2 节点定义

**分析层节点** (并行):
```python
workflow.add_node("macro", macro_agent_node)
workflow.add_node("onchain", onchain_agent_node)
workflow.add_node("ta", ta_agent_node)
```

**决策层节点** (串行):
```python
workflow.add_node("conviction", conviction_calculator_node)
workflow.add_node("signal", signal_generator_node)
```

### 5.3 边与条件

**无条件边** (必经之路):
```python
# 开始 → 3个分析节点 (并行)
workflow.set_entry_point("macro")
workflow.set_entry_point("onchain")
workflow.set_entry_point("ta")

# 3个分析 → 决策
workflow.add_edge("macro", "conviction")
workflow.add_edge("onchain", "conviction")
workflow.add_edge("ta", "conviction")

# 决策 → 信号
workflow.add_edge("conviction", "signal")
```

**条件边** (错误处理):
```python
def should_proceed_to_decision(state):
    # 至少2个Agent成功才继续
    success_count = sum([
        state.macro_score is not None,
        state.onchain_score is not None,
        state.ta_score is not None
    ])
    return success_count >= 2

workflow.add_conditional_edges(
    "macro",
    should_proceed_to_decision,
    {
        True: "conviction",
        False: "error_handler"
    }
)
```

### 5.4 错误处理策略

**Agent失败处理**:
1. **单个Agent失败**: 使用缓存的上次结果（标记为降级）
2. **2个Agent失败**: 跳过本次决策，等待下次
3. **全部失败**: 触发告警，人工介入

**LLM超时处理**:
- 超时时间: 10秒/Agent
- 重试策略: 立即重试1次
- 降级: 切换到备用LLM

---

## 六、Agent间通信机制

### 6.1 数据流图

```
[开始执行]
    ↓
[数据收集模块]
    ├─ 获取ETF数据
    ├─ 获取链上数据
    └─ 计算技术指标
    ↓
[写入State]
state.market_data = {
    "macro": {...},
    "onchain": {...},
    "ta": {...}
}
    ↓
[MacroAgent读State] ← 并行 → [OnChainAgent读State] ← 并行 → [TAAgent读State]
    ↓                              ↓                            ↓
[写入State]                   [写入State]                   [写入State]
state.macro_score = 0.8      state.onchain_score = 0.7    state.ta_score = 0.5
state.macro_reasoning = ".." state.onchain_reasoning=".." state.ta_reasoning=".."
    ↓
[ConvictionCalculator读State]
    ├─ 读取3个score
    ├─ 计算加权
    └─ 风险调整
    ↓
[写入State]
state.conviction_score = 75
    ↓
[SignalGenerator读State]
    ├─ 判断熔断条件
    ├─ 生成信号
    └─ 计算仓位
    ↓
[写入State]
state.signal = "BUY"
state.position_size = 0.005
    ↓
[执行层]
```

### 6.2 状态持久化

**每次执行都保存**:
- 完整的State快照
- 每个Agent的输入输出
- 执行时间和Token消耗
- 最终决策信号

**用途**:
- 回溯分析: "为什么当时做了这个决策？"
- 策略优化: 分析哪些信号准确率高
- 成本统计: 追踪LLM费用

---

## 七、性能优化策略

### 7.1 并行执行

**收益**:
- 串行执行: 3个Agent × 5秒 = 15秒
- 并行执行: max(5秒, 5秒, 5秒) = 5秒
- **提速**: 3倍

**实现**:
- LangGraph自动并行独立节点
- 使用asyncio并发调用LLM API

### 7.2 结果缓存

**缓存策略**:
| Agent | 缓存时长 | 理由 |
|-------|---------|------|
| MacroAgent | 4小时 | 宏观数据更新慢 |
| OnChainAgent | 1小时 | 链上数据更新快 |
| TAAgent | 15分钟 | 价格波动快 |

**缓存命中率预估**: 70%（用户重复查询）

### 7.3 Token优化

**Prompt优化**:
- 避免冗余描述
- 使用简洁的JSON格式
- 预处理数据（减少LLM计算）

**预估Token消耗**:
- MacroAgent: 2000 input + 800 output
- OnChainAgent: 2000 input + 800 output
- TAAgent: 1500 input + 600 output
- **总计**: 约7000 tokens/次执行

---

## 八、监控与可观测性

### 8.1 关键指标

| 指标 | 目标 | 告警阈值 |
|-----|------|---------|
| Agent成功率 | >95% | <90% |
| 平均执行时间 | <10s | >15s |
| LLM Token消耗 | 7K/次 | >10K |
| 决策信号准确率 | >60% | <50% |

### 8.2 日志记录

**每次执行记录**:
```json
{
  "execution_id": "exec_123abc",
  "strategy_id": "macro-wave-hodl",
  "timestamp": "2025-11-05T12:00:00Z",
  "agents": {
    "macro": {
      "success": true,
      "score": 0.8,
      "execution_time_ms": 4500,
      "tokens_used": 2800
    },
    "onchain": {...},
    "ta": {...}
  },
  "decision": {
    "conviction_score": 75,
    "signal": "BUY",
    "reasoning": "..."
  }
}
```

---

## 九、测试策略

### 9.1 单元测试

**测试覆盖**:
- [ ] MacroAgent输入输出验证
- [ ] OnChainAgent规则引擎测试
- [ ] TAAgent技术指标计算
- [ ] ConvictionCalculator公式正确性
- [ ] SignalGenerator熔断逻辑

**Mock策略**:
- Mock LLM API调用（避免实际费用）
- Mock数据源API
- 使用固定测试数据

### 9.2 集成测试

**测试场景**:
1. 完整工作流执行（正常流程）
2. 单个Agent失败处理
3. LLM超时处理
4. 熔断规则触发

### 9.3 回测

**历史数据验证**:
- 使用过去1年的历史数据
- 模拟策略执行
- 计算Sharpe Ratio、Max Drawdown
- 目标: Sharpe > 1.5, Max DD < 25%

---

## 十、未来扩展方向

### Phase 2: 增强Agent能力

- [ ] **SentimentAgent**: 分析Twitter/Reddit情绪
- [ ] **NewsAgent**: 解读新闻事件影响
- [ ] **RiskAgent**: 动态调整仓位

### Phase 3: 用户自定义

- [ ] 用户调整Agent权重（Macro 30% → 50%）
- [ ] 用户设置风险偏好
- [ ] 用户自定义熔断条件

### Phase 4: 自我学习

- [ ] Agent决策准确率追踪
- [ ] 自动调整提示词
- [ ] 强化学习优化权重

---

**📌 关键Takeaway**: 
- 三层架构清晰分工
- 并行优化提速3倍
- LangGraph管理复杂工作流
- 状态机实现Agent通信

**下一步**: 阅读 `03-数据流与调度机制.md` 了解数据如何流转


