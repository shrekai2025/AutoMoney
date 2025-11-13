# Research Chat 功能设计文档

## 📋 目录
1. [系统架构](#系统架构)
2. [Agent层级设计](#agent层级设计)
3. [前端交互设计](#前端交互设计)
4. [后端API设计](#后端api设计)
5. [数据流设计](#数据流设计)
6. [实现细节](#实现细节)

---

## 系统架构

### 总体架构图

```
用户提问
    ↓
SuperAgent (路由层)
    ├─→ 简单问题 → 直接回答 → 返回用户
    └─→ 复杂金融问题
            ↓
        PlanningAgent (规划层)
            ├─→ 任务分解
            │   - 确定需要哪些业务Agent
            │   - 规划调用顺序（支持并行）
            │   - 定义数据需求
            └─→ 决策规划
                    ↓
        业务Agent并行调用 (分析层)
            ├─→ MacroAgent (宏观分析)
            ├─→ OnChainAgent (链上分析)
            └─→ TAAgent (技术分析)
                    ↓
        GeneralAnalysisAgent (整合层)
            ├─→ 理解用户问题上下文
            ├─→ 整合各业务Agent结果
            └─→ 生成最终答复
                    ↓
                返回用户
```

### 架构特点

1. **业务Agent完全复用**
   - MacroAgent, OnChainAgent, TAAgent 保持现有接口不变
   - 既支持Research Chat调用，也支持策略系统调用
   - 输出格式统一（SignalType + 结构化分析）

2. **分层设计**
   - SuperAgent: 问题分类路由
   - PlanningAgent: 任务分解和规划
   - 业务Agent: 数据获取和专业分析
   - GeneralAnalysisAgent: 整合和总结

3. **支持并行调用**
   - PlanningAgent可决策同时调用多个业务Agent
   - 使用asyncio并发提升效率

---

## Agent层级设计

### 1. SuperAgent (路由层)

**职责**: 问题分类和路由

**输入**:
```json
{
  "user_message": "现在适合买BTC吗？",
  "chat_history": [...] // 最近5轮对话
}
```

**输出**:
```json
{
  "decision": "ROUTE_TO_PLANNING" | "DIRECT_ANSWER",
  "reasoning": "这是一个需要综合市场分析的复杂金融问题，涉及宏观经济、技术面和情绪面分析",
  "confidence": 0.95,
  "direct_answer": null // 如果是DIRECT_ANSWER则包含答案
}
```

**判断标准**:
- **简单问题** (直接回答):
  - 知识性问题: "什么是比特币"、"什么是MACD"
  - 信息查询: "BTC当前价格"、"Fear & Greed指数"
  - 概念解释: "解释什么是链上数据"

- **复杂金融问题** (转交Planning):
  - 市场分析: "分析当前市场趋势"
  - 投资决策: "现在适合买BTC吗"
  - 综合研究: "为什么BTC最近下跌"
  - 预测性问题: "BTC未来会涨吗"

**LLM配置**:
```python
"super_agent": {
    "provider": ProviderType.TUZI,
    "model": "chatgpt-4o-latest",  # Tuzi GPT-5 - 快速、成本低
    "temperature": 0.3,
    "max_tokens": 2048,
    "api_format": "openai"  # 使用OpenAI Chat Completions API格式
}
```

**API格式说明**:
- SuperAgent使用GPT-5: `/v1/chat/completions` (OpenAI格式)
- 其他Agent使用Claude: `/v1/messages` (Anthropic格式)

**GPT-5 请求格式**:
```python
{
    "model": "chatgpt-4o-latest",
    "messages": [
        {"role": "user", "content": "现在适合买BTC吗？"}
    ],
    "temperature": 0.3,
    "max_tokens": 2048,
    "stream": false
}
```

**GPT-5 响应格式**:
```python
{
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "{\"decision\": \"ROUTE_TO_PLANNING\", ...}"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 45, "completion_tokens": 120, "total_tokens": 165}
}

# 提取内容
content = response["choices"][0]["message"]["content"]
```

---

### 2. PlanningAgent (规划层)

**职责**: 任务分解、Agent选择、执行规划

**输入**:
```json
{
  "user_message": "分析当前BTC市场，应该买入还是观望？",
  "chat_history": [...],
  "available_agents": ["macro_agent", "onchain_agent", "ta_agent"]
}
```

**输出**:
```json
{
  "plan": {
    "task_breakdown": {
      "analysis_phase": [
        {
          "agent": "macro_agent",
          "reason": "需要分析宏观经济环境（美联储利率、美元指数、市场情绪）",
          "data_required": ["fed_rate", "dxy", "fear_greed", "m2_growth"],
          "priority": "high"
        },
        {
          "agent": "ta_agent",
          "reason": "需要技术面分析（趋势、支撑阻力、指标信号）",
          "data_required": ["ohlcv", "ema", "rsi", "macd", "bollinger"],
          "priority": "high"
        },
        {
          "agent": "onchain_agent",
          "reason": "链上数据可提供持币者行为洞察",
          "data_required": ["exchange_flow", "whale_activity"],
          "priority": "medium",
          "note": "链上数据暂不可用，将基于价格和交易量分析"
        }
      ],
      "decision_phase": {
        "agent": "general_analysis_agent",
        "reason": "整合以上分析，结合用户问题给出明确建议",
        "synthesis_required": true
      }
    },
    "execution_strategy": {
      "parallel_agents": ["macro_agent", "ta_agent"],
      "sequential_after": ["general_analysis_agent"],
      "estimated_time": "20-30秒"
    }
  },
  "reasoning": "这是一个典型的投资决策问题，需要多维度分析..."
}
```

**LLM配置**:
```python
"planning_agent": {
    "provider": ProviderType.TUZI,
    "model": "claude-sonnet-4-5-thinking-all",
    "temperature": 0.5,
    "max_tokens": 4096
}
```

---

### 3. 业务Agent (分析层)

#### 3.1 MacroAgent (已实现)

**保持现有接口不变**

**输入**:
```python
market_data = {
    "btc_price": 101584.19,
    "price_change_24h": -2.64,
    "macro": {...},  # FRED数据
    "fear_greed": {...}  # Alternative.me数据
}
```

**输出**:
```python
MacroAnalysisOutput(
    signal=SignalType.BEARISH,
    confidence=0.72,
    reasoning="宏观环境显示...",
    macro_indicators={...},
    key_factors=[...],
    risk_assessment="..."
)
```

#### 3.2 OnChainAgent (待实现)

**接口设计**:
```python
async def analyze(self, market_data: Dict[str, Any]) -> OnChainAnalysisOutput:
    """
    分析链上数据和持币者行为

    市场数据包括:
    - btc_price: 当前价格
    - volume_24h: 24小时交易量
    - onchain: 链上指标 (如可用)
    """
```

**输出**:
```python
OnChainAnalysisOutput(
    signal=SignalType.NEUTRAL,
    confidence=0.65,
    reasoning="基于交易量和价格行为分析...",
    onchain_metrics={...},
    whale_activity="...",
    network_health="..."
)
```

#### 3.3 TAAgent (待实现)

**接口设计**:
```python
async def analyze(self, market_data: Dict[str, Any]) -> TechnicalAnalysisOutput:
    """
    技术面分析

    市场数据包括:
    - btc_price: 当前价格
    - ohlcv: K线数据
    - indicators: 技术指标
    """
```

**输出**:
```python
TechnicalAnalysisOutput(
    signal=SignalType.BEARISH,
    confidence=0.78,
    reasoning="技术面显示...",
    technical_indicators={...},
    support_levels=[...],
    resistance_levels=[...],
    trend_analysis="..."
)
```

---

### 4. GeneralAnalysisAgent (整合层)

**职责**: 理解用户问题 + 整合业务Agent结果 + 生成最终答复

**输入**:
```json
{
  "user_message": "分析当前BTC市场，应该买入还是观望？",
  "chat_history": [...],
  "agent_results": {
    "macro_agent": {
      "signal": "BEARISH",
      "confidence": 0.72,
      "reasoning": "...",
      "macro_indicators": {...},
      "key_factors": [...],
      "risk_assessment": "..."
    },
    "ta_agent": {
      "signal": "BEARISH",
      "confidence": 0.78,
      "reasoning": "...",
      "technical_indicators": {...},
      "support_levels": [95000, 92000],
      "resistance_levels": [105000, 108000]
    },
    "onchain_agent": null  // 不可用
  },
  "market_context": {
    "btc_price": 101584.19,
    "price_change_24h": -2.64
  }
}
```

**输出**:
```json
{
  "answer": {
    "recommendation": "WAIT_AND_SEE",  // BUY | SELL | WAIT_AND_SEE
    "confidence": 0.75,
    "summary": "基于当前多维度分析，建议观望...",
    "detailed_analysis": {
      "macro_perspective": "宏观层面，美元指数处于高位(121.77)...",
      "technical_perspective": "技术面显示下行趋势...",
      "risk_factors": [
        "强势美元持续施压",
        "技术面破位风险",
        "市场情绪极度恐慌"
      ],
      "opportunity_factors": [
        "价格已有较大回调",
        "RSI接近超卖区域"
      ]
    },
    "action_plan": {
      "immediate": "观望，等待市场企稳信号",
      "entry_conditions": [
        "美元指数回落至118以下",
        "RSI回升至40以上",
        "价格站稳10万美元"
      ],
      "risk_management": "如考虑入场，建议分批买入，设置止损于95000"
    }
  },
  "consensus": false,  // 各Agent是否一致
  "agent_signals_summary": {
    "macro": "BEARISH (72%)",
    "ta": "BEARISH (78%)",
    "onchain": "N/A"
  },
  "metadata": {
    "analysis_timestamp": "2025-11-05T10:30:00Z",
    "data_sources": ["Binance", "FRED", "Alternative.me"],
    "agents_used": ["macro_agent", "ta_agent"]
  }
}
```

**LLM配置**:
```python
"general_analysis_agent": {
    "provider": ProviderType.TUZI,
    "model": "claude-sonnet-4-5-thinking-all",
    "temperature": 0.7,
    "max_tokens": 8192
}
```

---

## 前端交互设计

### UI布局

```
┌─────────────────────────────────────────────────────────┐
│  Research Chat                                     [···]│
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [用户] 分析当前BTC市场，应该买入还是观望？            │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ 🤖 AI思考中...                                  │    │  ← 临时等待提示
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ [SuperAgent 决策]                               │    │
│  │ ✓ 我将转交给Planning Agent处理这个复杂问题    │    │
│  │ 📊 查看原始JSON ▼                              │    │  ← 可展开/折叠
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ [Planning Agent 规划]                           │    │
│  │ 📋 任务涉及：宏观分析、技术分析                │    │
│  │ 🎯 将调用：MacroAgent、TAAgent                 │    │
│  │ 📝 最后由：GeneralAnalysisAgent 总结           │    │
│  │ 📊 查看任务规划JSON ▼                          │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ [业务Agent分析] (2个并行)                       │    │
│  │                                                  │    │
│  │ ┌──────────────────────┐ ┌──────────────────┐│    │
│  │ │ 📊 MacroAgent        │ │ 📈 TAAgent       ││    │
│  │ │ ⏳ 数据收集中...      │ │ ⏳ 数据收集中...  ││    │
│  │ │ └> 获取FRED数据      │ │ └> 获取OHLCV    ││    │
│  │ │ └> 获取Fear&Greed    │ │ └> 计算指标      ││    │
│  │ │ ✓ 分析完成           │ │ ✓ 分析完成       ││    │
│  │ │                       │ │                  ││    │
│  │ │ 信号: BEARISH (72%)  │ │ 信号: BEARISH   ││    │
│  │ │ 📊 查看详细分析 ▼    │ │ 📊 查看详细分析 ││    │
│  │ └──────────────────────┘ └──────────────────┘│    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ 🤖 AI思考中...                                  │    │  ← 整合阶段等待
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ [AI助手] 最终分析                               │    │
│  │                                                  │    │
│  │ 💡 建议：观望 (置信度: 75%)                     │    │
│  │                                                  │    │
│  │ 📊 综合分析：                                   │    │
│  │ 基于宏观和技术面的多维度分析，当前市场呈现    │    │
│  │ 明显的看跌信号...                              │    │
│  │                                                  │    │
│  │ 🔍 宏观视角：                                   │    │
│  │ 美元指数处于高位(121.77)，对BTC形成压力...    │    │
│  │                                                  │    │
│  │ 📈 技术视角：                                   │    │
│  │ 技术面显示下行趋势，价格跌破关键支撑...        │    │
│  │                                                  │    │
│  │ ⚠️ 风险因素：                                   │    │
│  │ • 强势美元持续施压                             │    │
│  │ • 技术面破位风险                               │    │
│  │ • 市场情绪极度恐慌                             │    │
│  │                                                  │    │
│  │ 💰 行动建议：                                   │    │
│  │ 建议观望，等待以下信号后再考虑入场：           │    │
│  │ • 美元指数回落至118以下                        │    │
│  │ • RSI回升至40以上                              │    │
│  │ • 价格站稳10万美元                             │    │
│  │                                                  │    │
│  │ 📊 查看完整分析JSON ▼                          │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  [输入框] 继续提问...                           [发送] │
└─────────────────────────────────────────────────────────┘
```

### 消息类型定义

```typescript
// 前端消息类型
enum MessageType {
  USER_MESSAGE = 'user_message',           // 用户消息
  THINKING = 'thinking',                   // AI思考中 (临时)
  SUPER_DECISION = 'super_decision',       // SuperAgent决策
  PLANNING = 'planning',                   // Planning规划
  AGENT_ANALYSIS = 'agent_analysis',       // 业务Agent分析
  FINAL_ANSWER = 'final_answer'            // 最终答案
}

// 消息结构
interface ChatMessage {
  id: string;
  type: MessageType;
  timestamp: string;
  content: any;
  metadata?: {
    persistent: boolean;      // 是否持久化（刷新后保留）
    includedInHistory: boolean; // 是否作为上下文传给LLM
  };
}
```

### 详细交互流程

#### 1. 用户发送消息

```typescript
// 用户发送
{
  id: "msg_001",
  type: "user_message",
  timestamp: "2025-11-05T10:30:00Z",
  content: {
    text: "分析当前BTC市场，应该买入还是观望？"
  },
  metadata: {
    persistent: true,           // 刷新后保留
    includedInHistory: true     // 传给LLM
  }
}
```

#### 2. SuperAgent处理阶段

**临时等待提示** (不持久化):
```typescript
{
  id: "thinking_001",
  type: "thinking",
  timestamp: "2025-11-05T10:30:01Z",
  content: {
    text: "AI思考中..."
  },
  metadata: {
    persistent: false,          // 临时消息
    includedInHistory: false
  }
}
```

**SuperAgent决策结果** (持久化但不传LLM):
```typescript
{
  id: "super_001",
  type: "super_decision",
  timestamp: "2025-11-05T10:30:03Z",
  content: {
    decision: "ROUTE_TO_PLANNING",
    displayText: "✓ 我将转交给Planning Agent处理这个复杂问题",
    reasoning: "这是一个需要综合市场分析的复杂金融问题...",
    rawJson: {
      decision: "ROUTE_TO_PLANNING",
      reasoning: "...",
      confidence: 0.95
    }
  },
  metadata: {
    persistent: true,           // 刷新后保留
    includedInHistory: false    // 不传给后续LLM
  }
}
```

#### 3. PlanningAgent规划阶段

**规划结果** (持久化但不传LLM):
```typescript
{
  id: "planning_001",
  type: "planning",
  timestamp: "2025-11-05T10:30:08Z",
  content: {
    displayText: "📋 任务涉及：宏观分析、技术分析\n🎯 将调用：MacroAgent、TAAgent\n📝 最后由：GeneralAnalysisAgent 总结",
    agentsToCall: ["macro_agent", "ta_agent"],
    synthesisAgent: "general_analysis_agent",
    estimatedTime: "20-30秒",
    rawJson: {
      plan: {...},
      reasoning: "..."
    }
  },
  metadata: {
    persistent: true,
    includedInHistory: false
  }
}
```

#### 4. 业务Agent分析阶段

**业务Agent容器**:
```typescript
{
  id: "agent_analysis_001",
  type: "agent_analysis",
  timestamp: "2025-11-05T10:30:10Z",
  content: {
    agents: [
      {
        name: "macro_agent",
        displayName: "📊 MacroAgent",
        status: "running",  // pending | running | completed | failed
        stages: [
          {
            stage: "data_collection",
            status: "completed",
            displayText: "✓ 数据收集完成",
            details: [
              "└> 获取FRED宏观数据",
              "└> 获取Fear & Greed指数"
            ],
            timestamp: "2025-11-05T10:30:12Z"
          },
          {
            stage: "analysis",
            status: "completed",
            displayText: "✓ 分析完成",
            result: {
              signal: "BEARISH",
              confidence: 0.72,
              summary: "宏观环境显示强势美元和极度恐慌情绪...",
              rawOutput: {...}  // 完整的MacroAnalysisOutput
            },
            timestamp: "2025-11-05T10:30:18Z"
          }
        ]
      },
      {
        name: "ta_agent",
        displayName: "📈 TAAgent",
        status: "completed",
        stages: [
          {
            stage: "data_collection",
            status: "completed",
            displayText: "✓ 数据收集完成",
            details: [
              "└> 获取OHLCV K线数据",
              "└> 计算技术指标"
            ],
            timestamp: "2025-11-05T10:30:13Z"
          },
          {
            stage: "analysis",
            status: "completed",
            displayText: "✓ 分析完成",
            result: {
              signal: "BEARISH",
              confidence: 0.78,
              summary: "技术面显示明显下行趋势...",
              rawOutput: {...}
            },
            timestamp: "2025-11-05T10:30:20Z"
          }
        ]
      }
    ]
  },
  metadata: {
    persistent: true,
    includedInHistory: false
  }
}
```

#### 5. GeneralAnalysisAgent整合阶段

**整合中等待**:
```typescript
{
  id: "thinking_002",
  type: "thinking",
  timestamp: "2025-11-05T10:30:21Z",
  content: {
    text: "AI思考中..."
  },
  metadata: {
    persistent: false,
    includedInHistory: false
  }
}
```

**最终答案**:
```typescript
{
  id: "final_001",
  type: "final_answer",
  timestamp: "2025-11-05T10:30:35Z",
  content: {
    recommendation: "WAIT_AND_SEE",
    confidence: 0.75,
    summary: "基于宏观和技术面的多维度分析，当前市场呈现明显的看跌信号...",
    sections: [
      {
        title: "💡 建议",
        content: "观望 (置信度: 75%)"
      },
      {
        title: "📊 综合分析",
        content: "基于宏观和技术面的多维度分析..."
      },
      {
        title: "🔍 宏观视角",
        content: "美元指数处于高位(121.77)..."
      },
      {
        title: "📈 技术视角",
        content: "技术面显示下行趋势..."
      },
      {
        title: "⚠️ 风险因素",
        items: [
          "强势美元持续施压",
          "技术面破位风险",
          "市场情绪极度恐慌"
        ]
      },
      {
        title: "💰 行动建议",
        content: "建议观望，等待以下信号...",
        items: [
          "美元指数回落至118以下",
          "RSI回升至40以上",
          "价格站稳10万美元"
        ]
      }
    ],
    agentSignals: {
      macro: { signal: "BEARISH", confidence: 0.72 },
      ta: { signal: "BEARISH", confidence: 0.78 }
    },
    rawJson: {...}
  },
  metadata: {
    persistent: true,
    includedInHistory: true  // 作为历史传给下一轮对话
  }
}
```

### 前端状态管理

```typescript
interface ChatState {
  messages: ChatMessage[];
  currentThinking: ThinkingMessage | null;
  isProcessing: boolean;
  currentStage: 'idle' | 'super' | 'planning' | 'agents' | 'synthesis';
}

// 消息过滤逻辑
function getDisplayMessages(messages: ChatMessage[]): ChatMessage[] {
  // 显示所有persistent的消息 + 当前thinking消息
  return messages.filter(msg =>
    msg.metadata.persistent || msg.type === 'thinking'
  );
}

function getHistoryForLLM(messages: ChatMessage[]): ChatMessage[] {
  // 只传递includedInHistory=true的消息给后端
  return messages.filter(msg =>
    msg.metadata.includedInHistory
  );
}
```

---

## 后端API设计

### API端点

#### 1. 创建Research会话

```
POST /api/v1/research/sessions
```

**Request**:
```json
{
  "user_id": "user_123"
}
```

**Response**:
```json
{
  "session_id": "session_abc123",
  "created_at": "2025-11-05T10:30:00Z"
}
```

#### 2. 发送消息 (主要接口)

```
POST /api/v1/research/sessions/{session_id}/messages
```

**Request**:
```json
{
  "message": "分析当前BTC市场，应该买入还是观望？",
  "chat_history": [
    // 最近5轮对话的用户消息和最终答案
  ]
}
```

**Response** (Server-Sent Events):
```
event: thinking
data: {"stage": "super_agent", "message": "AI思考中..."}

event: super_decision
data: {"decision": "ROUTE_TO_PLANNING", "reasoning": "...", ...}

event: thinking
data: {"stage": "planning_agent", "message": "AI思考中..."}

event: planning
data: {"plan": {...}, "agents_to_call": [...], ...}

event: agent_start
data: {"agent": "macro_agent", "stage": "data_collection"}

event: agent_progress
data: {"agent": "macro_agent", "stage": "data_collection", "details": ["获取FRED数据"]}

event: agent_complete
data: {"agent": "macro_agent", "stage": "analysis", "result": {...}}

event: thinking
data: {"stage": "synthesis", "message": "AI思考中..."}

event: final_answer
data: {"recommendation": "WAIT_AND_SEE", "confidence": 0.75, ...}

event: done
data: {"status": "completed"}
```

#### 3. 获取会话历史

```
GET /api/v1/research/sessions/{session_id}/messages
```

**Response**:
```json
{
  "messages": [
    // 所有persistent消息
  ]
}
```

### 后端工作流实现

```python
# app/services/research/workflow.py

from typing import Dict, Any, AsyncGenerator
from app.agents.super_agent import super_agent
from app.agents.planning_agent import planning_agent
from app.agents.general_analysis_agent import general_analysis_agent
from app.agents.macro_agent import macro_agent
from app.agents.ta_agent import ta_agent
from app.agents.onchain_agent import onchain_agent
from app.services.data_collectors.manager import data_manager

class ResearchWorkflow:
    """Research Chat工作流"""

    async def process_message(
        self,
        user_message: str,
        chat_history: list,
        session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理用户消息，生成SSE流式响应

        Yields:
            事件字典 {"event": "...", "data": {...}}
        """

        # Stage 1: SuperAgent路由
        yield {"event": "thinking", "data": {"stage": "super_agent"}}

        super_result = await super_agent.classify(user_message, chat_history)
        yield {"event": "super_decision", "data": super_result.dict()}

        # 如果是简单问题，直接返回
        if super_result.decision == "DIRECT_ANSWER":
            yield {"event": "final_answer", "data": {
                "recommendation": "INFO",
                "content": super_result.direct_answer
            }}
            yield {"event": "done", "data": {"status": "completed"}}
            return

        # Stage 2: PlanningAgent规划
        yield {"event": "thinking", "data": {"stage": "planning_agent"}}

        planning_result = await planning_agent.plan(
            user_message=user_message,
            chat_history=chat_history,
            available_agents=["macro_agent", "ta_agent", "onchain_agent"]
        )
        yield {"event": "planning", "data": planning_result.dict()}

        # Stage 3: 并行调用业务Agent
        agents_to_call = planning_result.plan.execution_strategy.parallel_agents
        agent_results = {}

        # 收集市场数据
        market_data = await data_manager.collect_all()

        # 并行执行业务Agent
        tasks = []
        for agent_name in agents_to_call:
            yield {"event": "agent_start", "data": {
                "agent": agent_name,
                "stage": "data_collection"
            }}

            if agent_name == "macro_agent":
                task = self._run_macro_agent(market_data)
            elif agent_name == "ta_agent":
                task = self._run_ta_agent(market_data)
            elif agent_name == "onchain_agent":
                task = self._run_onchain_agent(market_data)

            tasks.append((agent_name, task))

        # 等待所有Agent完成
        import asyncio
        for agent_name, task in tasks:
            result = await task
            agent_results[agent_name] = result

            yield {"event": "agent_complete", "data": {
                "agent": agent_name,
                "stage": "analysis",
                "result": result.dict()
            }}

        # Stage 4: GeneralAnalysisAgent整合
        yield {"event": "thinking", "data": {"stage": "synthesis"}}

        final_answer = await general_analysis_agent.synthesize(
            user_message=user_message,
            chat_history=chat_history,
            agent_results=agent_results,
            market_context={
                "btc_price": market_data.btc_price.price,
                "price_change_24h": market_data.btc_price.price_change_24h
            }
        )

        yield {"event": "final_answer", "data": final_answer.dict()}
        yield {"event": "done", "data": {"status": "completed"}}

    async def _run_macro_agent(self, market_data):
        """运行MacroAgent"""
        macro_data = {
            "btc_price": market_data.btc_price.price,
            "price_change_24h": market_data.btc_price.price_change_24h,
            "macro": market_data.macro.dict() if market_data.macro else {},
            "fear_greed": market_data.fear_greed.dict() if market_data.fear_greed else {}
        }
        return await macro_agent.analyze(macro_data)

    async def _run_ta_agent(self, market_data):
        """运行TAAgent"""
        ta_data = {
            "btc_price": market_data.btc_price.price,
            "ohlcv": [c.dict() for c in market_data.btc_ohlcv],
            "volume_24h": market_data.btc_price.volume_24h
        }
        return await ta_agent.analyze(ta_data)

    async def _run_onchain_agent(self, market_data):
        """运行OnChainAgent"""
        onchain_data = {
            "btc_price": market_data.btc_price.price,
            "volume_24h": market_data.btc_price.volume_24h,
            "onchain": market_data.onchain.dict() if market_data.onchain else {}
        }
        return await onchain_agent.analyze(onchain_data)
```

---

## 数据流设计

### 完整数据流图

```
用户输入
    ↓
[后端] POST /api/v1/research/sessions/{id}/messages
    ↓
[后端] ResearchWorkflow.process_message()
    ↓
[SSE] event: thinking (SuperAgent)
    ↓
[后端] SuperAgent.classify()
    ├─→ decision: DIRECT_ANSWER
    │   └─→ [SSE] event: final_answer
    │       └─→ [SSE] event: done
    │
    └─→ decision: ROUTE_TO_PLANNING
        ↓
        [SSE] event: super_decision
        ↓
        [SSE] event: thinking (PlanningAgent)
        ↓
        [后端] PlanningAgent.plan()
        ↓
        [SSE] event: planning
        ↓
        [后端] 收集市场数据 (data_manager.collect_all)
        ↓
        [后端] 并行调用业务Agents
            ├─→ MacroAgent.analyze()
            │   ├─→ [SSE] event: agent_start (macro)
            │   ├─→ [SSE] event: agent_progress (数据收集)
            │   └─→ [SSE] event: agent_complete (分析完成)
            │
            └─→ TAAgent.analyze()
                ├─→ [SSE] event: agent_start (ta)
                ├─→ [SSE] event: agent_progress (数据收集)
                └─→ [SSE] event: agent_complete (分析完成)
        ↓
        [SSE] event: thinking (GeneralAnalysisAgent)
        ↓
        [后端] GeneralAnalysisAgent.synthesize()
        ↓
        [SSE] event: final_answer
        ↓
        [SSE] event: done
```

---

## 实现细节

### 1. SuperAgent实现要点

```python
# app/agents/super_agent.py

class SuperAgent:
    """问题分类和路由Agent"""

    SYSTEM_PROMPT = """你是一个智能路由Agent，负责判断用户问题的复杂度。

简单问题（直接回答）：
- 知识性问题：定义、概念解释
- 信息查询：当前价格、指数值
- 基础问答：是什么、怎么算

复杂金融问题（转交Planning）：
- 市场分析：趋势、走势
- 投资决策：买卖建议
- 综合研究：为什么、会怎样
- 预测性问题：未来走势

返回JSON格式：
{
  "decision": "DIRECT_ANSWER" | "ROUTE_TO_PLANNING",
  "reasoning": "判断理由",
  "confidence": 0.95,
  "direct_answer": "直接答案（如果是简单问题）"
}
"""

    async def classify(
        self,
        user_message: str,
        chat_history: list
    ) -> SuperAgentDecision:
        """分类用户问题"""

        # 构建prompt
        prompt = f"""用户问题：{user_message}

最近对话：
{self._format_history(chat_history)}

判断这是简单问题还是复杂金融问题，并给出回答/路由决策。"""

        # 调用LLM
        messages = [Message(role="user", content=prompt)]
        response = await llm_manager.chat_for_agent(
            agent_name="super_agent",
            messages=messages
        )

        # 解析结果
        result = json.loads(response.content)
        return SuperAgentDecision(**result)
```

### 2. PlanningAgent实现要点

```python
# app/agents/planning_agent.py

class PlanningAgent:
    """任务规划Agent"""

    SYSTEM_PROMPT = """你是一个任务规划Agent，负责分解复杂金融问题并规划执行策略。

可用的业务Agents：
1. MacroAgent - 宏观经济分析
   - 分析：美联储利率、M2货币供应、美元指数、市场情绪
   - 适用：宏观环境、货币政策、系统性风险

2. TAAgent - 技术面分析
   - 分析：趋势、支撑阻力、技术指标（EMA、RSI、MACD、布林带）
   - 适用：价格走势、入场时机、止损止盈

3. OnChainAgent - 链上数据分析
   - 分析：持币者行为、交易量、鲸鱼活动
   - 适用：市场结构、持仓分布、资金流向
   - 注意：链上数据暂不可用，将基于价格和交易量替代

规划原则：
- 分析阶段：确定需要哪些Agent（可并行）
- 决策阶段：由GeneralAnalysisAgent整合
- 合理估计时间

返回JSON格式（严格遵守schema）：
{
  "plan": {
    "task_breakdown": {
      "analysis_phase": [...],
      "decision_phase": {...}
    },
    "execution_strategy": {
      "parallel_agents": [...],
      "sequential_after": [...],
      "estimated_time": "20-30秒"
    }
  },
  "reasoning": "规划理由"
}
"""

    async def plan(
        self,
        user_message: str,
        chat_history: list,
        available_agents: list
    ) -> PlanningResult:
        """规划任务执行"""

        # 构建prompt
        prompt = f"""用户问题：{user_message}

可用Agents：{', '.join(available_agents)}

请规划如何分析这个问题。"""

        # 调用LLM
        messages = [Message(role="user", content=prompt)]
        response = await llm_manager.chat_for_agent(
            agent_name="planning_agent",
            messages=messages
        )

        # 解析结果
        result = json.loads(response.content)
        return PlanningResult(**result)
```

### 3. GeneralAnalysisAgent实现要点

```python
# app/agents/general_analysis_agent.py

class GeneralAnalysisAgent:
    """通用分析整合Agent"""

    SYSTEM_PROMPT = """你是一个金融分析总结Agent，负责整合多个专业Agent的分析结果并给出最终建议。

你的任务：
1. 理解用户的真实问题和意图
2. 综合各业务Agent的分析（宏观、技术、链上）
3. 识别共识和分歧
4. 给出明确、可执行的建议

输出要求：
- recommendation: BUY | SELL | WAIT_AND_SEE
- confidence: 0-1之间
- 结构化展示：综合分析、各维度视角、风险因素、行动建议
- 语言清晰、专业、客观

返回JSON格式：
{
  "answer": {
    "recommendation": "WAIT_AND_SEE",
    "confidence": 0.75,
    "summary": "总体概述...",
    "detailed_analysis": {
      "macro_perspective": "...",
      "technical_perspective": "...",
      "risk_factors": [...],
      "opportunity_factors": [...]
    },
    "action_plan": {
      "immediate": "...",
      "entry_conditions": [...],
      "risk_management": "..."
    }
  },
  "consensus": true/false,
  "agent_signals_summary": {...}
}
"""

    async def synthesize(
        self,
        user_message: str,
        chat_history: list,
        agent_results: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> GeneralAnalysisOutput:
        """整合分析结果"""

        # 构建prompt
        prompt = f"""用户问题：{user_message}

当前市场：
- BTC价格：${market_context['btc_price']:,.2f}
- 24h变化：{market_context['price_change_24h']:+.2f}%

业务Agent分析结果：
{self._format_agent_results(agent_results)}

请整合以上分析，给出最终建议。"""

        # 调用LLM
        messages = [Message(role="user", content=prompt)]
        response = await llm_manager.chat_for_agent(
            agent_name="general_analysis_agent",
            messages=messages
        )

        # 解析结果
        result = json.loads(response.content)
        return GeneralAnalysisOutput(**result)
```

### 4. 消息持久化

```python
# app/models/research_message.py

class ResearchMessage(Base):
    """Research聊天消息"""

    __tablename__ = "research_messages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("research_sessions.id"))
    type = Column(String)  # user_message, super_decision, planning, etc.
    content = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    session = relationship("ResearchSession", back_populates="messages")
```

### 5. 前端SSE处理

```typescript
// 前端SSE处理
async function sendMessage(message: string, sessionId: string) {
  const eventSource = new EventSource(
    `/api/v1/research/sessions/${sessionId}/messages?message=${encodeURIComponent(message)}`
  );

  eventSource.addEventListener('thinking', (event) => {
    const data = JSON.parse(event.data);
    // 显示临时等待消息
    addThinkingMessage(data.stage);
  });

  eventSource.addEventListener('super_decision', (event) => {
    const data = JSON.parse(event.data);
    // 移除thinking，显示SuperAgent决策
    removeThinkingMessage();
    addSuperDecision(data);
  });

  eventSource.addEventListener('planning', (event) => {
    const data = JSON.parse(event.data);
    removeThinkingMessage();
    addPlanning(data);
  });

  eventSource.addEventListener('agent_start', (event) => {
    const data = JSON.parse(event.data);
    startAgentProgress(data.agent);
  });

  eventSource.addEventListener('agent_complete', (event) => {
    const data = JSON.parse(event.data);
    completeAgentProgress(data.agent, data.result);
  });

  eventSource.addEventListener('final_answer', (event) => {
    const data = JSON.parse(event.data);
    removeThinkingMessage();
    addFinalAnswer(data);
  });

  eventSource.addEventListener('done', (event) => {
    eventSource.close();
  });

  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    eventSource.close();
    showError('连接断开，请重试');
  };
}
```

---

## 与策略系统的关系

### 策略系统保持不变

```python
# 策略系统直接调用业务Agent
async def generate_trading_signal():
    """生成交易信号（策略系统）"""

    # 收集市场数据
    market_data = await data_manager.collect_all()

    # 并行调用业务Agent
    macro_result = await macro_agent.analyze(...)
    onchain_result = await onchain_agent.analyze(...)
    ta_result = await ta_agent.analyze(...)

    # 决策层Agent整合
    final_signal = await decision_agent.aggregate([
        macro_result,
        onchain_result,
        ta_result
    ])

    # 触发交易/模拟交易
    if final_signal.should_trade:
        await execute_trade(final_signal)

    return final_signal
```

### 两个系统对比

| 特性 | Research Chat | 策略系统 |
|------|--------------|----------|
| 触发方式 | 用户提问 | 定时任务 |
| 路由层 | SuperAgent + PlanningAgent | 无（直接调用） |
| 业务Agent | 根据问题动态选择 | 固定调用全部 |
| 整合层 | GeneralAnalysisAgent | DecisionAgent |
| 输出 | 用户答案 | 交易信号 |
| 执行 | 无交易 | 模拟/真实交易 |

### 业务Agent完全复用

```python
# MacroAgent既可被Research调用，也可被策略调用
# 接口完全一致，无需修改

# Research调用
research_result = await macro_agent.analyze(market_data)
# 返回：MacroAnalysisOutput

# 策略调用
strategy_result = await macro_agent.analyze(market_data)
# 返回：MacroAnalysisOutput（同一个）
```

---

## 总结

### 关键设计原则

1. **业务Agent零修改**
   - MacroAgent、OnChainAgent、TAAgent保持独立
   - 输出格式统一，接口稳定
   - 既服务Research，也服务策略

2. **分层架构**
   - 路由层（SuperAgent）：快速分类
   - 规划层（PlanningAgent）：智能分解
   - 分析层（业务Agents）：专业分析
   - 整合层（GeneralAnalysisAgent）：综合总结

3. **并行执行**
   - 业务Agent可并发调用
   - 提升响应速度
   - 降低整体延迟

4. **精细交互**
   - 每个阶段可见
   - 过程透明
   - 结果可追溯

5. **消息分类**
   - 临时消息（thinking）：不持久化
   - 流程消息（super/planning）：持久化但不传LLM
   - 对话消息（user/final）：持久化且传LLM

### 实施优先级

**Phase 1** (必需):
1. ✅ MacroAgent (已完成)
2. 实现TAAgent
3. 实现SuperAgent
4. 实现PlanningAgent
5. 实现GeneralAnalysisAgent

**Phase 2** (增强):
1. 实现OnChainAgent（链上数据可用后）
2. 优化LLM Prompt
3. 添加更多数据源

**Phase 3** (完善):
1. 会话管理
2. 历史记录
3. 用户反馈
4. A/B测试

---

最后更新: 2025-11-05
