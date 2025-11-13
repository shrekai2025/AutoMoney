# 业务Agent解耦数据持久化改造计划

> **版本**: 1.2 (Phase 1-2 完成)
> **创建日期**: 2025-11-06
> **最后更新**: 2025-11-06 (Phase 1-2 完成)
> **优先级**: P0 (架构基础改造，必须先于策略系统实施)
> **预计工期**: 5-7天
> **状态**: 🎉 Phase 1-2 完成 (100%)

## ⚠️ 重要说明

**本计划已与 `STRATEGY_TRADING_TODO.md` 完成协调整合**

### 关键变更
1. **新增 `strategy_execution_id` 字段** - 支持策略系统的强关联需求
2. **新增索引 `idx_agent_executions_strategy`** - 优化策略系统的查询性能
3. **新增relationship** - `AgentExecution.strategy_execution` 关联到 `StrategyExecution`

### 与策略系统的关系
- ✅ **策略系统删除了 `agent_conversations` 表** - 改用本计划的 `agent_executions` 表
- ✅ **策略系统删除了 `agent_outputs` 字段** - 通过 `strategy_execution_id` 外键查询Agent结果
- ✅ **统一数据源** - Research Chat和Strategy System都使用 `agent_executions` 表

### 实施顺序
**本计划必须先实施，策略系统依赖 `agent_executions` 表！**

---

## 📋 目录

1. [背景和目标](#背景和目标)
2. [当前架构问题](#当前架构问题)
3. [解决方案设计](#解决方案设计)
4. [数据库Schema设计](#数据库schema设计)
5. [实施阶段](#实施阶段)
6. [API设计](#api设计)
7. [前端集成](#前端集成)
8. [测试计划](#测试计划)
9. [迁移策略](#迁移策略)

---

## 背景和目标

### 业务背景

AutoMoney v2.0目前有两个调用业务Agent的场景：

1. **Research Chat** - 用户主动对话，SuperAgent路由到业务Agent
2. **Strategy System** - 定时执行策略，直接调用业务Agent

**核心问题**: 业务Agent（MacroAgent, TAAgent, OnChainAgent）的工作成果与调用方耦合，导致：
- Mind Hub页面无法统一展示最新Agent工作成果
- 无法按策略或对话追溯Agent分析历史
- 数据存储分散，难以维护

### 改造目标

实现业务Agent的**工作成果存储与调用方解耦**，满足以下需求：

✅ **需求1**: Mind Hub可以展示所有业务Agent的最新工作成果
✅ **需求2**: 可以按特定Research Chat对话查询相关Agent分析
✅ **需求3**: 可以按特定Strategy执行查询相关Agent分析
✅ **需求4**: Agent工作成果独立存储，不依赖调用方
✅ **需求5**: 保留调用方关联，支持追溯和审计

### 适用范围

**涉及的业务Agent**:
- MacroAgent (宏观分析)
- TAAgent (技术分析)
- OnChainAgent (链上分析)

**不涉及的Agent**:
- SuperAgent (系统层，不直接分析)
- PlanningAgent (系统层，不直接分析)
- GeneralAnalysisAgent (综合层，依赖业务Agent结果)

---

## 当前架构问题

### 问题1: 数据存储耦合

**Research Chat场景**:
```
用户提问 → SuperAgent → PlanningAgent →
  → MacroAgent (结果存入conversations表)
  → TAAgent (结果存入conversations表)
  → OnChainAgent (结果存入conversations表)
```

**Strategy System场景**:
```
定时触发 →
  → MacroAgent (结果存入strategy_executions表)
  → TAAgent (结果存入strategy_executions表)
  → OnChainAgent (结果存入strategy_executions表)
```

**问题**: 同一个Agent的工作成果散落在不同表中，无法统一查询。

### 问题2: Mind Hub无法获取最新结果

Mind Hub需要显示"Squad Decision Core"（三个业务Agent的最新工作），但：
- 如果最近一次是Research Chat调用的 → 需要查conversations表
- 如果最近一次是Strategy调用的 → 需要查strategy_executions表
- **无法确定去哪个表查询最新结果**

### 问题3: 追溯困难

无法回答以下问题：
- "某次策略执行时，MacroAgent给出了什么结论？"
- "某次对话中，OnChainAgent的分析是什么？"
- "MacroAgent过去7天的分析趋势如何？"

---

## 解决方案设计

### 核心设计理念

**解耦但可关联** - Agent工作成果独立存储，但保留调用方引用

```
┌─────────────────────────────────────────┐
│   调用方 (Research Chat / Strategy)     │
└───────────────┬─────────────────────────┘
                │ 调用
                ↓
┌─────────────────────────────────────────┐
│   业务Agent (Macro/TA/OnChain)          │
│   - 执行分析                            │
│   - 生成结果                            │
└───────────────┬─────────────────────────┘
                │ 记录到
                ↓
┌─────────────────────────────────────────┐
│   agent_executions 表 (统一存储)        │
│   - agent_name: 'macro_agent'           │
│   - signal, confidence, reasoning       │
│   - caller_type: 'research_chat'        │  ← 可选关联
│   - caller_id: 'conv_123'               │  ← 可选关联
└─────────────────────────────────────────┘
```

### 关键特性

1. **Agent结果独立存储** - 所有业务Agent的工作成果存在同一个表
2. **可选调用方关联** - `caller_type` 和 `caller_id` 字段可为NULL
3. **统一查询接口** - 通过 `AgentExecutionRecorder` 服务统一访问
4. **灵活查询模式** - 支持"最新结果"、"按调用方"、"按时间范围"等查询

---

## 数据库Schema设计

### 新表: agent_executions

**表名**: `agent_executions`
**用途**: 统一存储所有业务Agent的工作成果

```sql
CREATE TABLE agent_executions (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Agent标识
    agent_name VARCHAR(50) NOT NULL,          -- 'macro_agent', 'ta_agent', 'onchain_agent'
    agent_display_name VARCHAR(100),          -- 'The Oracle', 'Data Warden', 'Momentum Scout'

    -- 执行信息
    executed_at TIMESTAMP NOT NULL,
    execution_duration_ms INTEGER,            -- 执行耗时（毫秒）
    status VARCHAR(20) DEFAULT 'success',     -- 'success', 'failed', 'timeout'

    -- 标准化输出（所有Agent统一格式）
    signal VARCHAR(20) NOT NULL,              -- 'BULLISH', 'BEARISH', 'NEUTRAL'
    confidence NUMERIC(3, 2) NOT NULL,        -- 0.00 ~ 1.00
    score NUMERIC(3, 2),                      -- -1.00 ~ +1.00 (可选)
    reasoning TEXT NOT NULL,                  -- LLM推理过程

    -- Agent专属数据（JSONB灵活存储）
    agent_specific_data JSONB NOT NULL,       -- MacroAgent: {etf_flow, fed_rate, ...}
                                              -- TAAgent: {ema_21, rsi_14, ...}
                                              -- OnChainAgent: {mvrv, nvt, ...}

    -- 市场数据快照（用于复现分析）
    market_data_snapshot JSONB,               -- 执行时的完整市场数据

    -- LLM调用追踪
    llm_provider VARCHAR(50),                 -- 'tuzi', 'openrouter'
    llm_model VARCHAR(100),                   -- 'claude-sonnet-4-5-thinking-all'
    llm_prompt TEXT,                          -- 发送给LLM的完整prompt
    llm_response TEXT,                        -- LLM原始响应
    tokens_used INTEGER,                      -- Token消耗
    llm_cost NUMERIC(10, 6),                  -- LLM调用成本（USD）

    -- 调用方关联（可选，实现解耦）
    caller_type VARCHAR(50),                  -- 'research_chat', 'strategy_system', 'manual', NULL
    caller_id UUID,                           -- conversation_id (可为NULL)
    
    -- 💡 策略系统专用关联（强类型外键）
    strategy_execution_id UUID REFERENCES strategy_executions(id),  -- 策略执行ID (可为NULL)
    
    user_id UUID REFERENCES users(id),        -- 触发用户（可为NULL，如定时任务）

    -- 审计字段
    created_at TIMESTAMP DEFAULT NOW(),

    -- 约束
    CONSTRAINT chk_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT chk_score CHECK (score IS NULL OR (score >= -1 AND score <= 1)),
    CONSTRAINT chk_signal CHECK (signal IN ('BULLISH', 'BEARISH', 'NEUTRAL')),
    CONSTRAINT chk_status CHECK (status IN ('success', 'failed', 'timeout'))
);

-- 索引设计
-- 1. Mind Hub查询最新结果（最高频）
CREATE INDEX idx_agent_executions_latest
    ON agent_executions(agent_name, executed_at DESC)
    WHERE status = 'success';

-- 2. 按调用方查询
CREATE INDEX idx_agent_executions_caller
    ON agent_executions(caller_type, caller_id, executed_at DESC);

-- 2.5 按策略执行查询 (策略系统专用)
CREATE INDEX idx_agent_executions_strategy
    ON agent_executions(strategy_execution_id, executed_at);

-- 3. 按用户查询
CREATE INDEX idx_agent_executions_user
    ON agent_executions(user_id, executed_at DESC);

-- 4. 按时间范围查询
CREATE INDEX idx_agent_executions_time
    ON agent_executions(executed_at DESC);

-- 5. LLM成本分析
CREATE INDEX idx_agent_executions_llm
    ON agent_executions(llm_provider, llm_model, executed_at DESC);
```

### agent_specific_data 字段示例

**MacroAgent**:
```json
{
  "etf_flow": 250000000,
  "futures_position": 65.5,
  "fed_rate_prob": 80,
  "m2_growth": 5.5,
  "dxy_index": 102.3,
  "signals": {
    "etf": "bullish",
    "futures": "neutral",
    "fed": "bullish",
    "liquidity": "bullish"
  }
}
```

**TAAgent**:
```json
{
  "ema_21": 46910.60,
  "ema_55": 45200.30,
  "rsi_14": 72.86,
  "macd": 26.11,
  "bb_width": 2.5,
  "signals": {
    "trend": "uptrend",
    "momentum": "overbought",
    "volatility": "normal"
  }
}
```

**OnChainAgent**:
```json
{
  "mvrv_z_score": 2.5,
  "nvt_ratio": 60.0,
  "exchange_flow": -12000,
  "lth_change": 2.3,
  "active_addresses": 547000,
  "hash_rate": 1100,
  "signals": {
    "valuation": "fair",
    "accumulation": "whales_buying",
    "activity": "increasing"
  }
}
```

---

## ✅ 实施进度总结

### Phase 1: 数据库基础 ✅ 完成 (100%)
- ✅ Task 1.1: 创建数据库迁移 - 完成
- ✅ Task 1.2: 创建SQLAlchemy模型 - 完成
- ✅ 修复: user_id类型从UUID改为Integer - 完成
- ✅ 修复: 临时移除strategy_execution_id外键 - 完成

### Phase 2: 服务层实现 ✅ 完成 (100%)
- ✅ Task 2.1: 创建AgentExecutionRecorder服务 - 完成
- ✅ Task 2.2: 集成到ResearchWorkflow - 完成
- ✅ 修复: 添加_serialize_for_json()方法 - 完成
- ✅ 测试: 完整集成测试通过 - 完成

### 🎯 重要实现规则

#### 1. user_id类型为Integer (不是UUID)
**原因**: 现有users表的id字段为Integer类型，必须保持一致。

**实现**:
```python
# app/models/agent_execution.py
user_id = Column(Integer, ForeignKey("user.id"))  # Integer, not UUID
```

**迁移**: 创建了migration 59d6bfb0a721 使用`ALTER TABLE ... USING NULL`进行类型转换。

#### 2. strategy_execution_id外键暂时注释
**原因**: StrategyExecution表尚未创建（属于STRATEGY_TRADING_TODO.md的Phase 1）。

**实现**:
```python
# app/models/agent_execution.py
strategy_execution_id = Column(
    UUID(as_uuid=True),
    # ForeignKey("strategy_executions.id"),  # 暂时注释，等待表创建
    comment="策略执行ID (可为NULL)"
)
# strategy_execution = relationship("StrategyExecution", ...)  # 暂时注释
```

**后续**: 当strategy_executions表创建后，取消注释即可。

#### 3. JSONB序列化处理
**问题**: datetime和Decimal对象无法直接存储到PostgreSQL JSONB。

**解决方案**: 实现递归序列化函数:
```python
@staticmethod
def _serialize_for_json(obj: Any) -> Any:
    """递归序列化对象以便存储到 JSONB"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, 'dict'):  # Pydantic model
        return AgentExecutionRecorder._serialize_for_json(obj.dict())
    elif isinstance(obj, dict):
        return {k: AgentExecutionRecorder._serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [AgentExecutionRecorder._serialize_for_json(item) for item in obj]
    else:
        return obj
```

#### 4. 错误容错机制
**原则**: Agent执行记录失败不应影响workflow主流程。

**实现**:
```python
# app/workflows/research_workflow.py
if db and output:
    try:
        await agent_execution_recorder.record_macro_agent(...)
        print(f"✅ Recorded {agent_name} execution to database")
    except Exception as record_error:
        # 不阻断workflow
        print(f"⚠️  Failed to record {agent_name} execution: {record_error}")
```

---

## 实施阶段（原计划，已完成）

### Phase 1: 数据库基础 (1-2天) ✅ 完成

#### Task 1.1: 创建数据库迁移 ✅

**文件**: `alembic/versions/003_create_agent_executions_table.py` + `alembic/versions/59d6bfb0a721_fix_agent_executions_user_id_type.py`

```python
"""Create agent_executions table

Revision ID: 003
Revises: 002
Create Date: 2025-11-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '003'
down_revision = '002'

def upgrade():
    op.create_table(
        'agent_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_name', sa.String(50), nullable=False),
        sa.Column('agent_display_name', sa.String(100)),
        sa.Column('executed_at', sa.TIMESTAMP, nullable=False),
        sa.Column('execution_duration_ms', sa.Integer),
        sa.Column('status', sa.String(20), server_default='success'),

        sa.Column('signal', sa.String(20), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('score', sa.Numeric(3, 2)),
        sa.Column('reasoning', sa.Text, nullable=False),

        sa.Column('agent_specific_data', JSONB, nullable=False),
        sa.Column('market_data_snapshot', JSONB),

        sa.Column('llm_provider', sa.String(50)),
        sa.Column('llm_model', sa.String(100)),
        sa.Column('llm_prompt', sa.Text),
        sa.Column('llm_response', sa.Text),
        sa.Column('tokens_used', sa.Integer),
        sa.Column('llm_cost', sa.Numeric(10, 6)),

        sa.Column('caller_type', sa.String(50)),
        sa.Column('caller_id', UUID(as_uuid=True)),
        sa.Column('strategy_execution_id', UUID(as_uuid=True), sa.ForeignKey('strategy_executions.id')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')),

        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),

        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='chk_confidence'),
        sa.CheckConstraint('score IS NULL OR (score >= -1 AND score <= 1)', name='chk_score'),
        sa.CheckConstraint("signal IN ('BULLISH', 'BEARISH', 'NEUTRAL')", name='chk_signal'),
        sa.CheckConstraint("status IN ('success', 'failed', 'timeout')", name='chk_status'),
    )

    # 创建索引
    op.create_index('idx_agent_executions_latest', 'agent_executions',
                   ['agent_name', sa.text('executed_at DESC')],
                   postgresql_where=sa.text("status = 'success'"))
    op.create_index('idx_agent_executions_caller', 'agent_executions',
                   ['caller_type', 'caller_id', sa.text('executed_at DESC')])
    op.create_index('idx_agent_executions_strategy', 'agent_executions',
                   ['strategy_execution_id', sa.text('executed_at')])
    op.create_index('idx_agent_executions_user', 'agent_executions',
                   ['user_id', sa.text('executed_at DESC')])
    op.create_index('idx_agent_executions_time', 'agent_executions',
                   [sa.text('executed_at DESC')])
    op.create_index('idx_agent_executions_llm', 'agent_executions',
                   ['llm_provider', 'llm_model', sa.text('executed_at DESC')])

def downgrade():
    op.drop_index('idx_agent_executions_llm')
    op.drop_index('idx_agent_executions_time')
    op.drop_index('idx_agent_executions_user')
    op.drop_index('idx_agent_executions_strategy')
    op.drop_index('idx_agent_executions_caller')
    op.drop_index('idx_agent_executions_latest')
    op.drop_table('agent_executions')
```

### Phase 1 验收标准 ✅ 全部通过

- [x] ✅ agent_executions表创建成功
- [x] ✅ 所有索引创建成功（7个索引）
- [x] ✅ 约束生效（4个check constraints）
- [x] ✅ user_id类型修复为Integer
- [x] ✅ 迁移可以正常执行和回滚

**数据库验证**:
```bash
alembic upgrade head
# ✅ agent_executions表创建成功
# ✅ 所有索引创建成功
# ✅ 约束生效
# ✅ user_id类型为Integer
```

---

### Phase 2: 服务层实现 (2-3天) ✅ 完成

#### Task 2.1: 创建AgentExecutionRecorder服务 ✅

**文件**: `app/services/agents/execution_recorder.py`

**实现内容**:
- ✅ 创建AgentExecutionRecorder类
- ✅ 实现record_macro_agent()方法
- ✅ 实现record_ta_agent()方法
- ✅ 实现record_onchain_agent()方法
- ✅ 实现get_latest_executions()方法
- ✅ 实现get_executions_by_caller()方法
- ✅ 实现get_executions_by_time_range()方法
- ✅ 添加_serialize_for_json()静态方法（关键修复）

**关键代码**:
```python
class AgentExecutionRecorder:
    """统一记录和查询业务Agent执行结果"""

    DISPLAY_NAMES = {
        'macro_agent': 'The Oracle',
        'ta_agent': 'Momentum Scout',
        'onchain_agent': 'Data Warden',
    }

    @staticmethod
    def _serialize_for_json(obj: Any) -> Any:
        """递归序列化对象以便存储到 JSONB"""
        # 处理 datetime, Decimal, Pydantic models, dict, list
        ...

    async def record_macro_agent(
        self, db: AsyncSession, output: MacroAnalysisOutput,
        market_data: Dict[str, Any], llm_info: Dict[str, Any],
        caller_type: Optional[str] = None, caller_id: Optional[str] = None,
        strategy_execution_id: Optional[str] = None, user_id: Optional[str] = None,
        execution_duration_ms: Optional[int] = None,
    ) -> AgentExecution:
        # Serialize market_data for JSONB storage
        serialized_market_data = self._serialize_for_json(market_data)

        execution = AgentExecution(
            agent_name='macro_agent',
            agent_display_name=self.DISPLAY_NAMES['macro_agent'],
            signal=output.signal.value,
            confidence=output.confidence,
            reasoning=output.reasoning,
            agent_specific_data={
                'macro_indicators': output.macro_indicators,
                'risk_assessment': output.risk_assessment,
            },
            market_data_snapshot=serialized_market_data,
            # ... other fields
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        return execution
```

#### Task 2.2: 集成到ResearchWorkflow ✅

**文件**: `app/workflows/research_workflow.py`

**修改内容**:
- ✅ 添加import: AsyncSession, agent_execution_recorder, time
- ✅ 修改process_question()签名，添加db, user_id, conversation_id参数
- ✅ 修改_execute_business_agents()，传递db session
- ✅ 修改_run_agent()，在Agent执行后记录到数据库
- ✅ 添加错误容错机制（记录失败不阻断workflow）

**关键代码**:
```python
async def _run_agent(
    self, agent: Any, agent_name: str, market_data: Dict[str, Any],
    user_message: str = "", db: Optional[AsyncSession] = None,
    user_id: Optional[int] = None, conversation_id: Optional[str] = None,
) -> Any:
    start_time = time.time()

    # Execute agent
    output = await agent.analyze(agent_data)
    execution_duration_ms = int((time.time() - start_time) * 1000)

    # Record to database (if db provided)
    if db and output:
        try:
            llm_info = {
                "provider": getattr(agent, "last_llm_provider", "tuzi"),
                "model": getattr(agent, "last_llm_model", "claude-sonnet-4-5"),
                # ... other LLM info
            }

            if agent_name == "macro_agent":
                await agent_execution_recorder.record_macro_agent(
                    db=db, output=output, market_data=market_data,
                    llm_info=llm_info, caller_type="research_chat",
                    caller_id=conversation_id, user_id=user_id,
                    execution_duration_ms=execution_duration_ms,
                )
            # ... similar for ta_agent and onchain_agent
            print(f"✅ Recorded {agent_name} execution to database")
        except Exception as record_error:
            # Don't fail workflow if recording fails
            print(f"⚠️  Failed to record {agent_name} execution: {record_error}")

    return output
```

#### Task 2.3: API端点集成 ✅

**文件**: `app/api/v1/endpoints/research.py`

**修改内容**:
- ✅ 添加import: uuid, AsyncSession, get_db, get_current_user, User
- ✅ 修改research_chat()，添加db和current_user依赖注入
- ✅ 生成conversation_id (UUID)
- ✅ 提取user_id (如果已认证)
- ✅ 传递所有参数到workflow.process_question()

**关键代码**:
```python
@router.post("/chat")
async def research_chat(
    request: ResearchChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = None,  # Optional authentication
):
    # Generate conversation ID for tracking
    conversation_id = str(uuid.uuid4())

    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    async def event_generator():
        async for event in research_workflow.process_question(
            user_message=request.message,
            chat_history=chat_history,
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        ):
            event_data = json.dumps(event, ensure_ascii=False)
            yield f"data: {event_data}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

#### Task 2.4: 集成测试 ✅

**文件**: `test_research_workflow_with_recorder.py`

**测试内容**:
- ✅ 完整workflow执行测试
- ✅ 数据库记录验证
- ✅ Agent执行记录验证
- ✅ 字段完整性验证
- ✅ 关联关系验证

**测试结果**: ✅ ALL TESTS PASSED
```
🎉 所有测试通过！
📋 测试总结:
  - 测试问题: BTC现在的市场情况如何？应该买入还是观望？
  - 对话ID: <UUID>
  - Workflow事件数: 10
  - Agent结果数: 3
  - 数据库新增记录: 3
  - 记录的Agent: macro_agent, onchain_agent, ta_agent
✅ ResearchWorkflow + AgentExecutionRecorder 集成成功！
```

### Phase 2 验收标准 ✅ 全部通过

- [x] ✅ AgentExecutionRecorder可以记录MacroAgent
- [x] ✅ AgentExecutionRecorder可以记录TAAgent
- [x] ✅ AgentExecutionRecorder可以记录OnChainAgent
- [x] ✅ get_latest_executions返回正确结果
- [x] ✅ get_executions_by_caller返回正确结果
- [x] ✅ _serialize_for_json()正确处理datetime/Decimal
- [x] ✅ workflow集成无错误
- [x] ✅ 错误容错机制正常工作
- [x] ✅ 完整集成测试通过

---

### Phase 3-5: API端点和前端集成 ⏳ 待开发

#### Phase 3: 创建API端点 (1-2天)

**待实现内容**:

from sqlalchemy import Column, String, Integer, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, NUMERIC
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.models.base import Base


class AgentExecution(Base):
    """业务Agent执行记录（解耦存储）"""
    __tablename__ = "agent_executions"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Agent标识
    agent_name = Column(String(50), nullable=False, index=True)
    agent_display_name = Column(String(100))

    # 执行信息
    executed_at = Column(TIMESTAMP, nullable=False, index=True)
    execution_duration_ms = Column(Integer)
    status = Column(String(20), default='success')

    # 标准化输出
    signal = Column(String(20), nullable=False)
    confidence = Column(NUMERIC(3, 2), nullable=False)
    score = Column(NUMERIC(3, 2))
    reasoning = Column(Text, nullable=False)

    # Agent专属数据
    agent_specific_data = Column(JSONB, nullable=False)
    market_data_snapshot = Column(JSONB)

    # LLM追踪
    llm_provider = Column(String(50))
    llm_model = Column(String(100))
    llm_prompt = Column(Text)
    llm_response = Column(Text)
    tokens_used = Column(Integer)
    llm_cost = Column(NUMERIC(10, 6))

    # 调用方关联（可选）
    caller_type = Column(String(50), index=True)
    caller_id = Column(UUID(as_uuid=True), index=True)
    
    # 策略系统专用关联（强类型外键）
    strategy_execution_id = Column(UUID(as_uuid=True), ForeignKey("strategy_executions.id"))
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # 审计
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="agent_executions")
    strategy_execution = relationship("StrategyExecution", back_populates="agent_executions")

    # 约束
    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='chk_confidence'),
        CheckConstraint('score IS NULL OR (score >= -1 AND score <= 1)', name='chk_score'),
        CheckConstraint("signal IN ('BULLISH', 'BEARISH', 'NEUTRAL')", name='chk_signal'),
        CheckConstraint("status IN ('success', 'failed', 'timeout')", name='chk_status'),
        Index('idx_agent_executions_latest', 'agent_name', 'executed_at',
              postgresql_where="status = 'success'"),
        Index('idx_agent_executions_caller', 'caller_type', 'caller_id', 'executed_at'),
        Index('idx_agent_executions_strategy', 'strategy_execution_id', 'executed_at'),
    )

    def __repr__(self):
        return f"<AgentExecution(agent={self.agent_name}, signal={self.signal}, executed_at={self.executed_at})>"
```

**文件**: `app/models/__init__.py` (更新)

```python
from app.models.agent_execution import AgentExecution

__all__ = [
    # ... 其他模型
    "AgentExecution",
]
```

---

### Phase 2: 服务层实现 (2-3天)

#### Task 2.1: 创建AgentExecutionRecorder服务

**文件**: `app/services/agents/execution_recorder.py`

```python
"""Agent Execution Recorder - 业务Agent工作成果记录服务"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.agent_execution import AgentExecution
from app.schemas.agents import (
    MacroAnalysisOutput,
    TAAnalysisOutput,
    OnChainAnalysisOutput
)


class AgentExecutionRecorder:
    """统一记录和查询业务Agent执行结果"""

    # Agent显示名称映射
    DISPLAY_NAMES = {
        'macro_agent': 'The Oracle',
        'ta_agent': 'Momentum Scout',
        'onchain_agent': 'Data Warden',
    }

    async def record_macro_agent(
        self,
        db: AsyncSession,
        output: MacroAnalysisOutput,
        market_data: Dict[str, Any],
        llm_info: Dict[str, Any],
        caller_type: Optional[str] = None,
        caller_id: Optional[str] = None,
        strategy_execution_id: Optional[str] = None,  # 💡 新增: 策略系统专用
        user_id: Optional[str] = None,
        execution_duration_ms: Optional[int] = None,
    ) -> AgentExecution:
        """记录MacroAgent执行结果"""

        execution = AgentExecution(
            agent_name='macro_agent',
            agent_display_name=self.DISPLAY_NAMES['macro_agent'],
            executed_at=datetime.utcnow(),
            execution_duration_ms=execution_duration_ms,
            status='success',

            # 标准化输出
            signal=output.signal.value,
            confidence=output.confidence,
            score=None,  # MacroAgent不输出score
            reasoning=output.reasoning,

            # Agent专属数据
            agent_specific_data={
                'macro_indicators': output.macro_indicators,
                'risk_assessment': output.risk_assessment,
            },
            market_data_snapshot=market_data,

            # LLM信息
            llm_provider=llm_info.get('provider'),
            llm_model=llm_info.get('model'),
            llm_prompt=llm_info.get('prompt'),
            llm_response=llm_info.get('response'),
            tokens_used=llm_info.get('tokens_used'),
            llm_cost=llm_info.get('cost'),

            # 调用方关联
            caller_type=caller_type,
            caller_id=caller_id,
            strategy_execution_id=strategy_execution_id,  # 💡 新增
            user_id=user_id,
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        return execution

    async def record_ta_agent(
        self,
        db: AsyncSession,
        output: TAAnalysisOutput,
        market_data: Dict[str, Any],
        llm_info: Dict[str, Any],
        caller_type: Optional[str] = None,
        caller_id: Optional[str] = None,
        strategy_execution_id: Optional[str] = None,  # 💡 新增
        user_id: Optional[str] = None,
        execution_duration_ms: Optional[int] = None,
    ) -> AgentExecution:
        """记录TAAgent执行结果"""

        execution = AgentExecution(
            agent_name='ta_agent',
            agent_display_name=self.DISPLAY_NAMES['ta_agent'],
            executed_at=datetime.utcnow(),
            execution_duration_ms=execution_duration_ms,
            status='success',

            # 标准化输出
            signal=output.signal.value,
            confidence=output.confidence,
            score=None,
            reasoning=output.reasoning,

            # Agent专属数据
            agent_specific_data={
                'technical_indicators': output.technical_indicators,
                'support_resistance': output.support_resistance,
                'trend_analysis': output.trend_analysis,
            },
            market_data_snapshot=market_data,

            # LLM信息
            llm_provider=llm_info.get('provider'),
            llm_model=llm_info.get('model'),
            llm_prompt=llm_info.get('prompt'),
            llm_response=llm_info.get('response'),
            tokens_used=llm_info.get('tokens_used'),
            llm_cost=llm_info.get('cost'),

            # 调用方关联
            caller_type=caller_type,
            caller_id=caller_id,
            strategy_execution_id=strategy_execution_id,  # 💡 新增
            user_id=user_id,
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        return execution

    async def record_onchain_agent(
        self,
        db: AsyncSession,
        output: OnChainAnalysisOutput,
        market_data: Dict[str, Any],
        llm_info: Dict[str, Any],
        caller_type: Optional[str] = None,
        caller_id: Optional[str] = None,
        strategy_execution_id: Optional[str] = None,  # 💡 新增
        user_id: Optional[str] = None,
        execution_duration_ms: Optional[int] = None,
    ) -> AgentExecution:
        """记录OnChainAgent执行结果"""

        execution = AgentExecution(
            agent_name='onchain_agent',
            agent_display_name=self.DISPLAY_NAMES['onchain_agent'],
            executed_at=datetime.utcnow(),
            execution_duration_ms=execution_duration_ms,
            status='success',

            # 标准化输出
            signal=output.signal.value,
            confidence=output.confidence,
            score=None,
            reasoning=output.reasoning,

            # Agent专属数据
            agent_specific_data={
                'onchain_metrics': output.onchain_metrics,
                'network_health': output.network_health,
                'key_observations': output.key_observations,
            },
            market_data_snapshot=market_data,

            # LLM信息
            llm_provider=llm_info.get('provider'),
            llm_model=llm_info.get('model'),
            llm_prompt=llm_info.get('prompt'),
            llm_response=llm_info.get('response'),
            tokens_used=llm_info.get('tokens_used'),
            llm_cost=llm_info.get('cost'),

            # 调用方关联
            caller_type=caller_type,
            caller_id=caller_id,
            strategy_execution_id=strategy_execution_id,  # 💡 新增
            user_id=user_id,
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        return execution

    async def get_latest_executions(
        self,
        db: AsyncSession,
        agent_names: Optional[List[str]] = None,
    ) -> Dict[str, AgentExecution]:
        """
        获取最新的Agent执行结果（用于Mind Hub显示）

        Args:
            agent_names: Agent名称列表，默认查询所有业务Agent

        Returns:
            {
                'macro_agent': AgentExecution(...),
                'ta_agent': AgentExecution(...),
                'onchain_agent': AgentExecution(...)
            }
        """
        if agent_names is None:
            agent_names = ['macro_agent', 'ta_agent', 'onchain_agent']

        results = {}

        for agent_name in agent_names:
            result = await db.execute(
                select(AgentExecution)
                .where(
                    and_(
                        AgentExecution.agent_name == agent_name,
                        AgentExecution.status == 'success'
                    )
                )
                .order_by(desc(AgentExecution.executed_at))
                .limit(1)
            )

            execution = result.scalar_one_or_none()
            if execution:
                results[agent_name] = execution

        return results

    async def get_executions_by_caller(
        self,
        db: AsyncSession,
        caller_type: str,
        caller_id: str,
    ) -> List[AgentExecution]:
        """
        按调用方查询Agent执行结果（用于追溯分析）

        Args:
            caller_type: 'research_chat' 或 'strategy_system'
            caller_id: conversation_id 或 strategy_execution_id

        Returns:
            AgentExecution列表
        """
        result = await db.execute(
            select(AgentExecution)
            .where(
                and_(
                    AgentExecution.caller_type == caller_type,
                    AgentExecution.caller_id == caller_id
                )
            )
            .order_by(AgentExecution.executed_at)
        )

        return result.scalars().all()

    async def get_executions_by_time_range(
        self,
        db: AsyncSession,
        agent_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[AgentExecution]:
        """
        按时间范围查询Agent执行历史（用于趋势分析）
        """
        result = await db.execute(
            select(AgentExecution)
            .where(
                and_(
                    AgentExecution.agent_name == agent_name,
                    AgentExecution.executed_at >= start_time,
                    AgentExecution.executed_at <= end_time,
                    AgentExecution.status == 'success'
                )
            )
            .order_by(AgentExecution.executed_at)
        )

        return result.scalars().all()


# 全局实例
agent_execution_recorder = AgentExecutionRecorder()
```

#### Task 2.2: 集成到现有Agent

**修改文件**: `app/agents/macro_agent.py` (示例)

```python
from app.services.agents.execution_recorder import agent_execution_recorder

class MacroAgent:
    async def analyze(
        self,
        data: dict,
        caller_type: Optional[str] = None,
        caller_id: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> MacroAgentOutput:
        """执行宏观分析"""

        start_time = datetime.utcnow()

        # 1. 规则引擎预处理
        preliminary_score = self._calculate_preliminary_score(data)

        # 2. 调用LLM
        llm_response = await self.llm.chat(...)

        # 3. 解析输出
        result = MacroAgentOutput.parse_raw(llm_response.content)

        execution_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # 4. 记录到agent_executions表（新增）
        if db:
            await agent_execution_recorder.record_macro_agent(
                db=db,
                output=result,
                market_data=data,
                llm_info={
                    'provider': 'tuzi',
                    'model': 'claude-sonnet-4-5-thinking-all',
                    'prompt': self.prompt_template.format(**data),
                    'response': llm_response.content,
                    'tokens_used': llm_response.usage.total_tokens,
                    'cost': llm_response.usage.total_tokens * 0.000003,  # 示例价格
                },
                caller_type=caller_type,
                caller_id=caller_id,
                user_id=user_id,
                execution_duration_ms=execution_duration_ms,
            )

        return result
```

**类似修改**:
- `app/agents/ta_agent.py`
- `app/agents/onchain_agent.py`

---

### Phase 3: API端点开发 (1-2天)

#### Task 3.1: Mind Hub API

**文件**: `app/api/v1/endpoints/mind_hub.py`

```python
"""Mind Hub API - Squad Decision Core"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.deps import get_db, get_current_user
from app.models import User
from app.services.agents.execution_recorder import agent_execution_recorder
from app.schemas.mind_hub import SquadDecisionCoreResponse

router = APIRouter()


@router.get("/squad-decision-core", response_model=SquadDecisionCoreResponse)
async def get_squad_decision_core(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取Squad Decision Core数据（Mind Hub页面）

    返回三个业务Agent的最新工作成果
    """

    latest_executions = await agent_execution_recorder.get_latest_executions(db)

    squad = []

    for agent_name in ['macro_agent', 'ta_agent', 'onchain_agent']:
        execution = latest_executions.get(agent_name)

        if execution:
            squad.append({
                'agent_name': execution.agent_name,
                'display_name': execution.agent_display_name,
                'signal': execution.signal,
                'confidence': float(execution.confidence),
                'reasoning': execution.reasoning[:200],  # 摘要
                'executed_at': execution.executed_at.isoformat(),
                'metrics': execution.agent_specific_data.get('metrics', {}),
            })
        else:
            # Agent还未执行过
            squad.append({
                'agent_name': agent_name,
                'display_name': agent_execution_recorder.DISPLAY_NAMES[agent_name],
                'signal': None,
                'confidence': None,
                'reasoning': '暂无数据',
                'executed_at': None,
                'metrics': {},
            })

    return {
        'squad': squad,
        'last_updated': max([e.executed_at for e in latest_executions.values()]) if latest_executions else None
    }


@router.get("/agent-history/{agent_name}")
async def get_agent_history(
    agent_name: str,
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取某个Agent的历史执行记录（用于趋势图）"""

    from datetime import timedelta

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    executions = await agent_execution_recorder.get_executions_by_time_range(
        db=db,
        agent_name=agent_name,
        start_time=start_time,
        end_time=end_time,
    )

    return {
        'agent_name': agent_name,
        'history': [
            {
                'executed_at': e.executed_at.isoformat(),
                'signal': e.signal,
                'confidence': float(e.confidence),
            }
            for e in executions
        ]
    }
```

#### Task 3.2: 调用方追溯API

**文件**: `app/api/v1/endpoints/agent_executions.py`

```python
"""Agent Executions API - 查询和追溯"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models import User
from app.services.agents.execution_recorder import agent_execution_recorder

router = APIRouter()


@router.get("/by-conversation/{conversation_id}")
async def get_executions_by_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    查询某次Research Chat对话中所有Agent的分析结果

    用途: 回溯某次对话，查看当时各Agent给出的结论
    """

    executions = await agent_execution_recorder.get_executions_by_caller(
        db=db,
        caller_type='research_chat',
        caller_id=conversation_id,
    )

    if not executions:
        raise HTTPException(status_code=404, detail="No agent executions found for this conversation")

    return {
        'conversation_id': conversation_id,
        'agents': [
            {
                'agent_name': e.agent_name,
                'signal': e.signal,
                'confidence': float(e.confidence),
                'reasoning': e.reasoning,
                'executed_at': e.executed_at.isoformat(),
                'agent_specific_data': e.agent_specific_data,
            }
            for e in executions
        ]
    }


@router.get("/by-strategy/{strategy_execution_id}")
async def get_executions_by_strategy(
    strategy_execution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    查询某次策略执行中所有Agent的分析结果

    用途: 回溯某次策略执行，查看当时各Agent给出的结论
    """

    executions = await agent_execution_recorder.get_executions_by_caller(
        db=db,
        caller_type='strategy_system',
        caller_id=strategy_execution_id,
    )

    if not executions:
        raise HTTPException(status_code=404, detail="No agent executions found for this strategy execution")

    return {
        'strategy_execution_id': strategy_execution_id,
        'agents': [
            {
                'agent_name': e.agent_name,
                'signal': e.signal,
                'confidence': float(e.confidence),
                'reasoning': e.reasoning,
                'executed_at': e.executed_at.isoformat(),
                'agent_specific_data': e.agent_specific_data,
            }
            for e in executions
        ]
    }
```

---

### Phase 4: 前端集成 (1-2天)

#### Task 4.1: Mind Hub Squad Decision Core组件

**文件**: `AMfrontend/src/components/SquadDecisionCore.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface AgentData {
  agent_name: string;
  display_name: string;
  signal: string | null;
  confidence: number | null;
  reasoning: string;
  executed_at: string | null;
  metrics: Record<string, any>;
}

export default function SquadDecisionCore() {
  const [squad, setSquad] = useState<AgentData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSquadData();

    // 每30秒刷新一次
    const interval = setInterval(loadSquadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadSquadData = async () => {
    try {
      const response = await axios.get('/api/v1/mind-hub/squad-decision-core', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      setSquad(response.data.squad);
    } catch (error) {
      console.error('Failed to load squad data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading Squad Decision Core...</div>;

  return (
    <div className="grid grid-cols-3 gap-4">
      {squad.map((agent) => (
        <div key={agent.agent_name} className="border rounded-lg p-4">
          <h3 className="font-bold text-lg">{agent.display_name}</h3>

          {agent.signal ? (
            <>
              <div className={`mt-2 text-2xl font-bold ${
                agent.signal === 'BULLISH' ? 'text-green-600' :
                agent.signal === 'BEARISH' ? 'text-red-600' :
                'text-gray-600'
              }`}>
                {agent.signal}
              </div>

              <div className="mt-1 text-sm text-gray-500">
                Confidence: {(agent.confidence! * 100).toFixed(0)}%
              </div>

              <p className="mt-2 text-sm">{agent.reasoning}</p>

              <div className="mt-2 text-xs text-gray-400">
                Updated: {new Date(agent.executed_at!).toLocaleString()}
              </div>
            </>
          ) : (
            <div className="mt-2 text-gray-400">暂无数据</div>
          )}
        </div>
      ))}
    </div>
  );
}
```

---

## 测试计划

### 单元测试

**文件**: `tests/unit/test_agent_execution_recorder.py`

```python
import pytest
from app.services.agents.execution_recorder import agent_execution_recorder

@pytest.mark.asyncio
async def test_record_macro_agent(db_session, test_user):
    """测试记录MacroAgent执行"""

    output = MacroAnalysisOutput(
        signal='BULLISH',
        confidence=0.75,
        reasoning='测试推理',
        macro_indicators={},
        risk_assessment='LOW',
    )

    execution = await agent_execution_recorder.record_macro_agent(
        db=db_session,
        output=output,
        market_data={'btc_price': 45000},
        llm_info={'provider': 'tuzi', 'model': 'claude'},
        caller_type='research_chat',
        caller_id='test_conv_123',
        user_id=test_user.id,
    )

    assert execution.agent_name == 'macro_agent'
    assert execution.signal == 'BULLISH'
    assert execution.caller_type == 'research_chat'


@pytest.mark.asyncio
async def test_get_latest_executions(db_session):
    """测试获取最新执行结果"""

    latest = await agent_execution_recorder.get_latest_executions(db_session)

    assert 'macro_agent' in latest
    assert latest['macro_agent'].status == 'success'
```

---

## 迁移策略

### 兼容性处理

1. **保留现有存储** - 现有的conversations表和strategy_executions表保持不变
2. **新旧并存** - 新系统同时记录到agent_executions表和原表
3. **逐步切换** - Mind Hub等新功能只读agent_executions表

### 数据回填（可选）

如果需要将历史数据回填到agent_executions表：

```python
# 脚本: scripts/backfill_agent_executions.py

async def backfill_from_conversations():
    """从conversations表回填数据"""
    # 读取历史conversation记录
    # 解析Agent输出
    # 写入agent_executions表
    pass
```

---

## 验收标准

### Phase 1 验收
- [ ] agent_executions表创建成功
- [ ] 所有索引正常工作
- [ ] AgentExecution模型可以正常CRUD

### Phase 2 验收
- [ ] AgentExecutionRecorder可以记录MacroAgent
- [ ] AgentExecutionRecorder可以记录TAAgent
- [ ] AgentExecutionRecorder可以记录OnChainAgent
- [ ] get_latest_executions返回正确结果
- [ ] get_executions_by_caller返回正确结果

### Phase 3 验收
- [ ] Mind Hub API返回正确的Squad数据
- [ ] 按conversation查询API正常工作
- [ ] 按strategy查询API正常工作

### Phase 4 验收
- [ ] Mind Hub前端显示最新Agent结果
- [ ] 数据每30秒自动刷新
- [ ] 信号颜色正确显示

---

## 总结

这个改造方案实现了业务Agent工作成果与调用方的**解耦但可关联**：

✅ **解耦**: Agent结果独立存储，不依赖调用方
✅ **可关联**: 通过caller_type和caller_id支持追溯
✅ **统一查询**: 通过AgentExecutionRecorder统一访问
✅ **灵活扩展**: JSONB字段支持Agent自定义数据
✅ **完整追踪**: LLM调用、成本、耗时全部记录

**下一步**: 等待确认后开始Phase 1实施。

---

最后更新: 2025-11-06
