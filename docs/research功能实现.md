# Research Chat 功能实现文档

## 目录
1. [整体架构](#整体架构)
2. [多层 Agent 调用流程](#多层-agent-调用流程)
3. [对话历史传输逻辑](#对话历史传输逻辑)
4. [LLM 模型配置](#llm-模型配置)
5. [数据流详解](#数据流详解)

---

## 整体架构

### 系统组成

```
Frontend (React + SSE)
    ↓
Backend API Endpoint (/api/v1/research/chat)
    ↓
ResearchWorkflow (工作流编排)
    ↓
Multi-Agent System (多层 Agent 协作)
    ↓
LLM Manager (模型调用管理)
    ↓
External LLM Providers (Tuzi/OpenRouter)
```

### 核心文件位置

**Backend:**
- `/AMbackend/app/api/v1/endpoints/research.py` - API 端点
- `/AMbackend/app/workflows/research_workflow.py` - 工作流编排
- `/AMbackend/app/agents/` - 各层 Agent 实现
- `/AMbackend/app/services/llm/manager.py` - LLM 配置管理

**Frontend:**
- `/AMfrontend/src/components/ResearchChat.tsx` - UI 组件
- `/AMfrontend/src/lib/api.ts` - API 调用工具

---

## 多层 Agent 调用流程

### 完整调用链

```
用户提问
    ↓
1. SuperAgent (路由层)
    ├─ 决策：DIRECT_ANSWER → 直接回答（结束）
    └─ 决策：COMPLEX_ANALYSIS → 继续流程
        ↓
2. PlanningAgent (规划层)
    ├─ 分析问题
    ├─ 选择需要的 Business Agents
    └─ 制定执行策略
        ↓
3. DataCollectionManager (数据收集)
    └─ 收集市场数据（BTC价格、宏观指标、情绪指数等）
        ↓
4. Business Agents (业务分析层) - **并行执行**
    ├─ MacroAgent (宏观经济分析) ✅ 已实现
    ├─ TAAgent (技术分析) ❌ 未实现
    └─ OnChainAgent (链上数据分析) ❌ 未实现
        ↓
5. GeneralAnalysisAgent (综合层)
    └─ 整合所有 Agent 结果，生成最终答案
```

### 各层 Agent 详解

#### 1. SuperAgent (路由层)

**文件**: `app/agents/super_agent.py`

**职责**:
- 快速判断问题复杂度
- 决定是直接回答还是启动复杂分析

**LLM 配置**:
```python
"super_agent": {
    "provider": ProviderType.TUZI,
    "model": "chatgpt-4o-latest",  # GPT-4o for fast routing
    "temperature": 0.3,
    "max_tokens": 2048,
}
```

**输入**:
- `user_message`: 用户问题
- `chat_history`: 最近 5 条对话历史

**输出**:
```python
{
    "decision": "DIRECT_ANSWER" | "COMPLEX_ANALYSIS",
    "reasoning": "决策原因",
    "confidence": 0.85,
    "direct_answer": "直接答案（如果选择 DIRECT_ANSWER）"
}
```

#### 2. PlanningAgent (规划层)

**文件**: `app/agents/planning_agent.py`

**职责**:
- 分析问题需要哪些维度的分析
- 选择合适的 Business Agents
- 制定执行策略（并行/串行）

**LLM 配置**:
```python
"planning_agent": {
    "provider": ProviderType.TUZI,
    "model": "claude-sonnet-4-5-thinking-all",  # Claude Thinking for strategic planning
    "temperature": 0.5,
    "max_tokens": 4096,
}
```

**输入**:
- `user_message`: 用户问题
- `chat_history`: 最近 5 条对话历史

**输出**:
```python
{
    "task_breakdown": {
        "analysis_phase": [
            {
                "agent": "macro_agent",
                "reason": "需要分析宏观经济环境",
                "priority": "high",
                "data_required": ["macro", "fear_greed"]
            }
        ],
        "decision_phase": "综合各维度分析结果"
    },
    "execution_strategy": {
        "parallel_agents": ["macro_agent"],
        "sequential_after": [],
        "estimated_time": "15-30秒"
    },
    "reasoning": "规划推理过程"
}
```

#### 3. Business Agents (业务分析层)

这一层的 Agent **不接收对话历史**，只接收实时市场数据。

##### MacroAgent (宏观经济分析)

**文件**: `app/agents/macro_agent.py`

**职责**:
- 分析宏观经济指标对 BTC 的影响
- 评估流动性、利率、美元强度等因素

**LLM 配置**:
```python
"macro_agent": {
    "provider": ProviderType.TUZI,
    "model": "claude-sonnet-4-5-thinking-all",
    "temperature": 1.0,
    "max_tokens": 50000,
    "fallback": {
        "provider": ProviderType.OPENROUTER,
        "model": "anthropic/claude-3.5-sonnet",
    },
}
```

**输入**: `market_data` 字典
```python
{
    "btc_price": 95234.50,
    "price_change_24h": 2.34,
    "macro": {
        "fed_rate_prob": 3.87,
        "m2_growth": 0.47,
        "dxy_index": 121.77,
        "metadata": {"dgs10_rate": 4.2}
    },
    "fear_greed": {
        "value": 23,
        "classification": "Extreme Fear"
    }
}
```

**输出**: `MacroAnalysisOutput`
```python
{
    "agent_name": "macro_agent",
    "signal": "BULLISH" | "BEARISH" | "NEUTRAL",
    "confidence": 0.75,
    "confidence_level": "HIGH",
    "reasoning": "详细分析过程...",
    "macro_indicators": {
        "fed_funds_rate": {
            "value": 3.87,
            "impact": "BEARISH",
            "weight": 0.3
        },
        "m2_growth": {...},
        "dxy": {...},
        "fear_greed": {...},
        "treasury_yield": {...}
    },
    "key_factors": [
        "High interest rates reducing liquidity",
        "Strong dollar creating headwinds"
    ],
    "risk_assessment": "High risk environment",
    "prompt_sent": "完整的发送给 LLM 的 prompt",
    "llm_response": "LLM 的完整响应"
}
```

##### TAAgent (技术分析) - 未实现

**计划数据源**:
- OHLCV 数据
- 移动平均线 (EMA, SMA)
- RSI, MACD, 布林带
- 成交量分析
- 支撑/阻力位

##### OnChainAgent (链上分析) - 未实现

**计划数据源**:
- 交易所流入/流出
- 巨鲸交易
- 活跃地址数
- MVRV 比率
- 网络活跃度

#### 4. GeneralAnalysisAgent (综合层)

**文件**: `app/agents/general_analysis_agent.py`

**职责**:
- 整合所有 Business Agent 的分析结果
- 结合对话历史理解用户意图
- 生成最终的综合答案

**LLM 配置**:
```python
"general_analysis_agent": {
    "provider": ProviderType.TUZI,
    "model": "claude-sonnet-4-5-thinking-all",
    "temperature": 0.6,
    "max_tokens": 8192,
}
```

**输入**:
- `user_message`: 用户问题
- `agent_outputs`: 所有 Business Agent 的分析结果
- `chat_history`: 最近 3 条对话历史

**输出**:
```python
{
    "answer": "综合分析结果...",
    "summary": "核心要点总结",
    "key_insights": [
        "关键洞察1",
        "关键洞察2"
    ],
    "confidence": 0.82,
    "sources": ["macro_agent"],
    "metadata": {...}
}
```

---

## 对话历史传输逻辑

### 前端发送逻辑

**文件**: `AMfrontend/src/components/ResearchChat.tsx`

```typescript
// 第 115-118 行
chat_history: messages.map((m) => ({
  role: m.role,
  content: m.content,  // ← 只发送最终答案文本
}))
```

**关键点**:
- ✅ 发送所有历史对话的 `content` (最终答案)
- ❌ **不发送** `processSteps` (分析过程的详细步骤)
- ❌ **不发送** `metadata` (元数据信息)

### 后端接收逻辑

**文件**: `AMbackend/app/api/v1/endpoints/research.py`

```python
class ResearchChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
```

**API 端点** (第 45-49 行):
```python
chat_history = []
if request.chat_history:
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.chat_history
    ]
```

### 各层 Agent 的历史接收情况

| Agent 层级 | 是否接收历史 | 接收条数 | 内容完整度 | 代码位置 |
|-----------|------------|----------|----------|---------|
| **SuperAgent** | ✅ 是 | 最近 5 条 | 完整 content | `super_agent.py:116` |
| **PlanningAgent** | ✅ 是 | 最近 5 条 | 完整 content | `planning_agent.py:185` |
| **MacroAgent** | ❌ **否** | 0 条 | **不接收** | `macro_agent.py:83` |
| **TAAgent** | ❌ **否** | 0 条 | **不接收** | 未实现 |
| **OnChainAgent** | ❌ **否** | 0 条 | **不接收** | 未实现 |
| **GeneralAnalysisAgent** | ✅ 是 | 最近 3 条 | 截断前 80 字符 | `general_analysis_agent.py:229` |

### 详细分析

#### SuperAgent 的历史使用

**文件**: `app/agents/super_agent.py:114-117`

```python
if chat_history:
    prompt += "\n**Recent Chat History:**\n"
    for msg in chat_history[-5:]:  # Last 5 messages
        prompt += f"- {msg['role']}: {msg['content']}\n"
```

**特点**:
- 取最近 5 条消息
- 完整显示每条消息的 content
- 用于判断是否需要复杂分析

#### PlanningAgent 的历史使用

**文件**: `app/agents/planning_agent.py:183-186`

```python
if chat_history:
    prompt += "\n**Chat Context (for reference):**\n"
    for msg in chat_history[-5:]:
        prompt += f"- {msg['role']}: {msg['content']}\n"
```

**特点**:
- 取最近 5 条消息
- 完整显示每条消息的 content
- 用于理解问题的上下文背景

#### MacroAgent 的历史使用

**文件**: `app/agents/macro_agent.py:83-96`

```python
async def analyze(self, market_data: Dict[str, Any]) -> MacroAnalysisOutput:
    # 只接收 market_data，不接收 chat_history
    analysis_prompt = self._build_analysis_prompt(market_data)
    # ...
```

**特点**:
- ❌ **完全不接收对话历史**
- 只分析当前的市场数据
- 保持客观性，不受历史对话影响

#### GeneralAnalysisAgent 的历史使用

**文件**: `app/agents/general_analysis_agent.py:227-232`

```python
if chat_history:
    prompt += "\n**Chat Context:**\n"
    for msg in chat_history[-3:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt += f"- {role}: {content[:80]}...\n"  # ← 只取前 80 字符
```

**特点**:
- 取最近 3 条消息
- **截断**每条消息为前 80 字符
- 用于理解用户的具体问题意图

### 对话历史示例

假设用户进行以下对话：

**第一轮**:
```
用户: "分析当前BTC市场趋势"
助手: "根据当前宏观经济分析，联邦利率维持在 3.87%，M2 增长放缓，美元指数强势，恐慌贪婪指数为 23（极度恐慌）。综合来看，当前宏观环境对 BTC 呈现 BEARISH 信号，建议谨慎观望..."
```

**第二轮提问**: "你认为这种情况下可以囤BTC吗？"

各层 Agent 实际看到的内容：

#### SuperAgent 看到:
```
Recent Chat History:
- user: 分析当前BTC市场趋势
- assistant: 根据当前宏观经济分析，联邦利率维持在 3.87%，M2 增长放缓...
- user: 你认为这种情况下可以囤BTC吗？
```

#### PlanningAgent 看到:
```
Chat Context (for reference):
- user: 分析当前BTC市场趋势
- assistant: 根据当前宏观经济分析，联邦利率维持在 3.87%，M2 增长放缓...
- user: 你认为这种情况下可以囤BTC吗？
```

#### MacroAgent 看到:
```
(不接收对话历史，只看到实时市场数据)
{
    "btc_price": 95234.50,
    "price_change_24h": 2.34,
    "macro": {...},
    "fear_greed": {...}
}
```

#### GeneralAnalysisAgent 看到:
```
Chat Context:
- user: 分析当前BTC市场趋势
- assistant: 根据当前宏观经济分析，联邦利率维持在 3.87%，M2 增长放缓，美元指数强势，恐慌贪婪指数为 23（极度恐慌）... (前80字符)
- user: 你认为这种情况下可以囤BTC吗？
```

### 设计理念

这种分层设计有明确的目的：

1. **SuperAgent & PlanningAgent**: 需要完整历史来理解问题背景和用户意图
2. **Business Agents**: 不接收历史，保持客观性，只基于实时数据分析
3. **GeneralAnalysisAgent**: 接收精简历史，用于在综合答案时考虑对话上下文

---

## LLM 模型配置

### 模型配置汇总

**文件**: `app/services/llm/manager.py:24-72`

```python
AGENT_CONFIGS = {
    "system_layer": {
        "provider": ProviderType.OPENROUTER,
        "model": "openai/gpt-4o-mini",
        "temperature": 0.3,
    },

    # Research Chat Agents
    "super_agent": {
        "provider": ProviderType.TUZI,
        "model": "chatgpt-4o-latest",
        "temperature": 0.3,
        "max_tokens": 2048,
    },

    "planning_agent": {
        "provider": ProviderType.TUZI,
        "model": "claude-sonnet-4-5-thinking-all",
        "temperature": 0.5,
        "max_tokens": 4096,
    },

    "general_analysis_agent": {
        "provider": ProviderType.TUZI,
        "model": "claude-sonnet-4-5-thinking-all",
        "temperature": 0.6,
        "max_tokens": 8192,
    },

    # Business Agents
    "macro_agent": {
        "provider": ProviderType.TUZI,
        "model": "claude-sonnet-4-5-thinking-all",
        "temperature": 1.0,
        "max_tokens": 50000,
        "fallback": {
            "provider": ProviderType.OPENROUTER,
            "model": "anthropic/claude-3.5-sonnet",
        },
    },

    "onchain_agent": {
        "provider": ProviderType.TUZI,
        "model": "claude-sonnet-4-5-thinking-all",
        "temperature": 0.7,
        "max_tokens": 8192,
    },

    "ta_agent": {
        "provider": ProviderType.TUZI,
        "model": "claude-sonnet-4-5-thinking-all",
        "temperature": 0.6,
        "max_tokens": 8192,
    },
}
```

### 模型选择策略

| Agent | 模型 | 原因 |
|-------|------|------|
| SuperAgent | GPT-4o | 快速路由，响应速度优先 |
| PlanningAgent | Claude Sonnet 4.5 Thinking | 需要深度思考和策略规划 |
| MacroAgent | Claude Sonnet 4.5 Thinking | 需要复杂的经济分析推理 |
| GeneralAnalysisAgent | Claude Sonnet 4.5 Thinking | 需要综合推理和逻辑整合 |

### Temperature 设置说明

- **0.3** (SuperAgent): 低随机性，确保路由决策稳定
- **0.5** (PlanningAgent): 平衡创造性和稳定性
- **1.0** (MacroAgent): 高创造性，鼓励多维度思考
- **0.6** (GeneralAnalysisAgent): 轻微创造性，保持答案质量

### Fallback 机制

MacroAgent 配置了备用模型：
```python
"fallback": {
    "provider": ProviderType.OPENROUTER,
    "model": "anthropic/claude-3.5-sonnet",
}
```

当主模型调用失败时，自动切换到备用模型，确保服务可用性。

---

## 数据流详解

### 完整数据流程图

```
用户输入
    ↓
[前端 ResearchChat.tsx]
    ├─ 构建 chat_history (只含 content)
    └─ POST /api/v1/research/chat
        ↓
[后端 API research.py]
    └─ 调用 research_workflow.process_question()
        ↓
[ResearchWorkflow]
    ├─ 1. SuperAgent.route(message, history) → 路由决策
    │   └─ 如果 DIRECT_ANSWER → 直接返回答案
    │
    ├─ 2. PlanningAgent.plan(message, history) → 制定计划
    │   └─ 返回需要的 agents 列表
    │
    ├─ 3. DataCollectionManager.collect_all() → 收集市场数据
    │   └─ 返回 market_data
    │
    ├─ 4. 并行执行 Business Agents
    │   └─ MacroAgent.analyze(market_data) → 无历史
    │       └─ 返回 MacroAnalysisOutput
    │
    └─ 5. GeneralAnalysisAgent.synthesize(message, outputs, history)
        └─ 返回最终答案
            ↓
[SSE Stream]
    ├─ status: 各阶段状态更新
    ├─ super_agent_decision: 路由结果
    ├─ planning_result: 规划结果
    ├─ data_collected: 数据收集完成
    ├─ agent_result: 各 Agent 分析结果
    └─ final_answer: 最终答案
        ↓
[前端接收]
    ├─ 逐步显示 process steps
    ├─ 存储完整的 processSteps 到 message
    └─ 显示最终答案
```

### SSE 事件类型

**文件**: `app/workflows/research_workflow.py`

所有通过 SSE 流式传输的事件类型：

#### 1. status
```python
{
    "type": "status",
    "data": {
        "stage": "routing" | "planning" | "data_collection" | "analysis" | "synthesis",
        "message": "AI思考中...",
        "timestamp": "2025-01-05T10:30:00"
    }
}
```

#### 2. super_agent_decision
```python
{
    "type": "super_agent_decision",
    "data": {
        "decision": "DIRECT_ANSWER" | "COMPLEX_ANALYSIS",
        "reasoning": "这是一个需要多维度分析的复杂问题",
        "confidence": 0.85,
        "timestamp": "2025-01-05T10:30:01"
    }
}
```

#### 3. planning_result
```python
{
    "type": "planning_result",
    "data": {
        "task_breakdown": {
            "analysis_phase": [...],
            "decision_phase": "..."
        },
        "execution_strategy": {
            "parallel_agents": ["macro_agent"],
            "sequential_after": [],
            "estimated_time": "15-30秒"
        },
        "reasoning": "...",
        "timestamp": "2025-01-05T10:30:02"
    }
}
```

#### 4. data_collected
```python
{
    "type": "data_collected",
    "data": {
        "btc_price": 95234.50,
        "price_change_24h": 2.34,
        "timestamp": "2025-01-05T10:30:03"
    }
}
```

#### 5. agent_result
```python
{
    "type": "agent_result",
    "data": {
        "agent_name": "macro_agent",
        "signal": "BULLISH" | "BEARISH" | "NEUTRAL",
        "confidence": 0.75,
        "reasoning": "分析推理（前200字符）...",
        "timestamp": "2025-01-05T10:30:10",

        // 完整数据（包括以下字段）
        "prompt_sent": "发送给 LLM 的完整 prompt",
        "llm_response": "LLM 返回的完整响应",
        "macro_indicators": {...},
        "key_factors": [...],
        "risk_assessment": "..."
    }
}
```

#### 6. final_answer
```python
{
    "type": "final_answer",
    "data": {
        "answer": "综合分析结果...",
        "summary": "核心要点",
        "key_insights": ["洞察1", "洞察2"],
        "confidence": 0.82,
        "sources": ["macro_agent"],
        "metadata": {...},
        "timestamp": "2025-01-05T10:30:15"
    }
}
```

#### 7. error
```python
{
    "type": "error",
    "data": {
        "error": "错误详情",
        "message": "分析过程中发生错误，请稍后重试",
        "timestamp": "2025-01-05T10:30:05"
    }
}
```

### 前端处理 SSE

**文件**: `AMfrontend/src/components/ResearchChat.tsx:120-155`

```typescript
const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split("\n");

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const jsonStr = line.substring(6);
      const event = JSON.parse(jsonStr);

      if (event.type === "done") {
        // 完成
      } else if (event.type === "final_answer") {
        // 最终答案
        const assistantMessage: Message = {
          role: "assistant",
          content: event.data.answer || event.data,
          timestamp: event.data.timestamp,
          processSteps: processSteps,  // ← 保存完整的 process steps
          metadata: event.data,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        // 其他事件 → 添加到 processSteps
        setCurrentProcessSteps((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            type: event.type,
            data: event.data,
            timestamp: event.data.timestamp,
          },
        ]);
      }
    }
  }
}
```

### 前端存储结构

**Message 类型**:
```typescript
type Message = {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  processSteps?: ProcessStep[];  // ← 包含完整的分析过程
  metadata?: any;
};
```

**ProcessStep 类型**:
```typescript
type ProcessStep = {
  id: string;
  type: "status" | "super_agent_decision" | "planning_result" | "agent_result" | "data_collected";
  data: any;
  timestamp: string;
};
```

**关键点**:
- `processSteps` 存储在每条 assistant message 中
- 用户下一次提问时，**不会**将 `processSteps` 发送回后端
- 只发送 `content` (最终答案文本)

---

## 总结

### 核心特点

1. **分层架构**: SuperAgent → PlanningAgent → Business Agents → GeneralAnalysisAgent
2. **智能路由**: SuperAgent 快速判断是否需要复杂分析
3. **并行执行**: Business Agents 同时运行，提高效率
4. **对话感知**: 上层和综合层能理解对话上下文
5. **客观分析**: Business Agents 不受历史影响，保持客观性
6. **实时反馈**: SSE 流式传输，用户实时看到进度

### 未来扩展

1. **新增 TAAgent**: 技术分析维度
2. **新增 OnChainAgent**: 链上数据分析维度
3. **优化对话历史**: 考虑传递更多上下文给 GeneralAnalysisAgent
4. **智能摘要**: 压缩长对话历史，保留关键信息
5. **Agent 权重**: 根据问题类型动态调整各 Agent 的权重

---

**文档版本**: v1.0
**最后更新**: 2025-01-05
**维护者**: AutoMoney Team
