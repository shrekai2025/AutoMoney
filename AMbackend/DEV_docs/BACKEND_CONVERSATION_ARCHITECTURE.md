# 后端对话架构设计

## 概述

本文档提出基于后端的对话管理架构，以满足用户需求：

1. **防止前端断开连接导致对话中断**
2. **将对话历史存储到数据库**
3. **提供更好的错误处理和恢复机制**

## 当前架构（存在的问题）

```
前端 → SSE流 → 工作流 → Agent → LLM
   ↓                              ↑
   ↓         (直接连接)            ↑
   └──────────────────────────────┘
```

**存在的问题**:
- 前端断开连接会终止整个对话
- 没有对话持久化
- SSE超时会杀死长时间运行的工作流
- 错误事件没有正确显示
- 没有对话恢复机制

## 提议的架构

```
前端 → REST API ← 会话管理器 ← 数据库
              ↓                   ↑
         后台任务队列              ↑
              ↓                   ↑
         工作流执行器 → Agent → LLM
              ↓                   ↑
         事件发布器 ────────────────┘
              ↓
         SSE广播器 → 前端（可重连）
```

## 数据库Schema

### 1. 对话表 (Conversations)
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'active',  -- active, completed, error
    metadata JSONB  -- 用户偏好、设置等
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
```

### 2. 消息表 (Messages)
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB,  -- agent信息、置信度等

    -- 消息排序
    sequence_number INTEGER NOT NULL,

    -- 富内容支持
    message_type VARCHAR(50) DEFAULT 'text',  -- text, analysis, chart_data

    CONSTRAINT unique_conversation_sequence UNIQUE (conversation_id, sequence_number)
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id, sequence_number);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
```

### 3. 工作流执行表 (Workflow Executions)
```sql
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,

    -- 工作流状态
    status VARCHAR(50) NOT NULL,  -- pending, running, completed, error, cancelled
    stage VARCHAR(100),  -- routing, planning, data_collection, analysis, synthesis

    -- 执行详情
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    error_traceback TEXT,

    -- 工作流数据
    planning_result JSONB,  -- PlanningAgent的任务分解
    agent_results JSONB[],  -- Agent分析结果数组
    final_answer TEXT,

    -- 执行元数据
    execution_time_ms INTEGER,
    agents_executed VARCHAR(100)[],
    metadata JSONB
);

CREATE INDEX idx_workflow_executions_conversation_id ON workflow_executions(conversation_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_message_id ON workflow_executions(message_id);
```

### 4. SSE连接表（内存缓存）
```sql
-- 使用Redis追踪SSE连接
-- Key模式: sse_connection:{conversation_id}:{client_id}
{
    "client_id": "uuid",
    "conversation_id": "uuid",
    "connected_at": "timestamp",
    "last_heartbeat": "timestamp",
    "user_agent": "string"
}
```

## API接口

### 1. 开始对话
```python
POST /api/v1/conversations

请求:
{
    "initial_message": "结合链上数据，说说现在能不能买BTC",
    "metadata": {
        "source": "web_ui",
        "preferences": {}
    }
}

响应:
{
    "conversation_id": "uuid",
    "message_id": "uuid",
    "workflow_execution_id": "uuid",
    "sse_endpoint": "/api/v1/conversations/{conversation_id}/stream"
}
```

### 2. 继续对话
```python
POST /api/v1/conversations/{conversation_id}/messages

请求:
{
    "message": "那现在买还是等等？",
    "context": {}  # 可选的上下文覆盖
}

响应:
{
    "message_id": "uuid",
    "workflow_execution_id": "uuid"
}
```

### 3. 获取对话历史
```python
GET /api/v1/conversations/{conversation_id}

响应:
{
    "conversation_id": "uuid",
    "title": "BTC投资分析",
    "created_at": "2025-11-06T03:30:00Z",
    "updated_at": "2025-11-06T03:35:00Z",
    "status": "active",
    "messages": [
        {
            "id": "uuid",
            "role": "user",
            "content": "结合链上数据，说说现在能不能买BTC",
            "created_at": "2025-11-06T03:30:00Z",
            "sequence_number": 1
        },
        {
            "id": "uuid",
            "role": "assistant",
            "content": "基于当前多维度分析...",
            "created_at": "2025-11-06T03:30:45Z",
            "sequence_number": 2,
            "metadata": {
                "workflow_execution_id": "uuid",
                "agents_used": ["onchain_agent", "macro_agent", "ta_agent"],
                "confidence": 0.65
            }
        }
    ]
}
```

### 4. SSE流（可重连）
```python
GET /api/v1/conversations/{conversation_id}/stream

Headers:
  Last-Event-ID: {last_received_event_id}  # 用于重连

响应 (SSE):
  event: status
  id: 1
  data: {"stage": "planning", "message": "规划分析任务..."}

  event: planning_result
  id: 2
  data: {"task_breakdown": {...}, "execution_strategy": {...}}

  event: agent_result
  id: 3
  data: {"agent_name": "onchain_agent", "signal": "NEUTRAL", ...}

  event: final_answer
  id: 4
  data: {"answer": "基于当前多维度分析...", "conversation_id": "uuid"}

  event: error
  id: 5
  data: {"error": "...", "recoverable": true}

  event: heartbeat
  id: 6
  data: {"timestamp": "2025-11-06T03:30:00Z"}
```

### 5. 列出对话
```python
GET /api/v1/conversations?limit=20&offset=0

响应:
{
    "total": 100,
    "conversations": [
        {
            "conversation_id": "uuid",
            "title": "BTC投资分析",
            "created_at": "2025-11-06T03:30:00Z",
            "last_message_at": "2025-11-06T03:35:00Z",
            "message_count": 6,
            "preview": "基于当前多维度分析..."
        }
    ]
}
```

### 6. 取消工作流
```python
POST /api/v1/conversations/{conversation_id}/cancel

响应:
{
    "cancelled": true,
    "workflow_execution_id": "uuid"
}
```

## 实现组件

### 1. 会话管理器
```python
# app/services/conversation/session_manager.py

class SessionManager:
    """管理对话会话和持久化"""

    async def create_conversation(
        self,
        user_id: str,
        initial_message: str,
        metadata: dict = None
    ) -> Conversation:
        """创建新对话并启动工作流执行"""

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict = None
    ) -> Message:
        """向对话历史添加消息"""

    async def get_conversation(
        self,
        conversation_id: str
    ) -> Conversation:
        """获取包含完整消息历史的对话"""

    async def update_workflow_status(
        self,
        workflow_execution_id: str,
        status: str,
        stage: str = None,
        **kwargs
    ) -> None:
        """更新工作流执行状态"""
```

### 2. 后台任务队列
```python
# app/services/conversation/job_queue.py

from celery import Celery

celery_app = Celery('automoney', broker='redis://localhost:6379/0')

@celery_app.task(bind=True)
async def execute_workflow_task(
    self,
    conversation_id: str,
    message_id: str,
    user_question: str
):
    """在后台执行研究工作流"""

    workflow_execution_id = await create_workflow_execution(
        conversation_id=conversation_id,
        message_id=message_id,
        status='running'
    )

    try:
        async for event in research_workflow.process_question(user_question):
            # 发布事件到SSE广播器
            await event_publisher.publish(conversation_id, event)

            # 保存事件到数据库
            await save_workflow_event(workflow_execution_id, event)

            # 更新工作流状态
            if event['type'] == 'status':
                await update_workflow_status(
                    workflow_execution_id,
                    stage=event['data']['stage']
                )
            elif event['type'] == 'final_answer':
                await update_workflow_status(
                    workflow_execution_id,
                    status='completed',
                    final_answer=event['data']['answer']
                )

                # 向对话添加助手消息
                await session_manager.add_message(
                    conversation_id=conversation_id,
                    role='assistant',
                    content=event['data']['answer'],
                    metadata={'workflow_execution_id': workflow_execution_id}
                )

    except Exception as e:
        logger.error(f"工作流执行错误: {e}")
        await update_workflow_status(
            workflow_execution_id,
            status='error',
            error_message=str(e),
            error_traceback=traceback.format_exc()
        )

        # 发布错误事件
        await event_publisher.publish(conversation_id, {
            'type': 'error',
            'data': {
                'error': str(e),
                'recoverable': True,
                'workflow_execution_id': workflow_execution_id
            }
        })
```

### 3. 事件发布器（Redis Pub/Sub）
```python
# app/services/conversation/event_publisher.py

import redis.asyncio as redis
import json

class EventPublisher:
    """将工作流事件发布到Redis用于SSE广播"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

    async def publish(
        self,
        conversation_id: str,
        event: dict
    ) -> None:
        """发布事件到对话频道"""
        channel = f"conversation:{conversation_id}"
        await self.redis_client.publish(
            channel,
            json.dumps(event)
        )

    async def subscribe(
        self,
        conversation_id: str
    ):
        """订阅对话事件"""
        pubsub = self.redis_client.pubsub()
        channel = f"conversation:{conversation_id}"
        await pubsub.subscribe(channel)

        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    yield json.loads(message['data'])
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

event_publisher = EventPublisher()
```

### 4. SSE广播器
```python
# app/api/v1/endpoints/conversations.py

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

@router.get("/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: str,
    request: Request,
    last_event_id: str = Header(None, alias="Last-Event-ID")
):
    """支持重连的SSE端点"""

    async def event_generator():
        # 如果重连，发送错过的事件
        if last_event_id:
            missed_events = await get_events_after(
                conversation_id,
                int(last_event_id)
            )
            for event_id, event in missed_events:
                yield {
                    "id": str(event_id),
                    "event": event['type'],
                    "data": json.dumps(event['data'])
                }

        # 订阅实时事件
        async for event in event_publisher.subscribe(conversation_id):
            if await request.is_disconnected():
                break

            event_id = await increment_event_counter(conversation_id)

            yield {
                "id": str(event_id),
                "event": event['type'],
                "data": json.dumps(event['data'])
            }

            # 每15秒发送心跳
            await asyncio.sleep(15)
            yield {
                "id": str(event_id + 1),
                "event": "heartbeat",
                "data": json.dumps({"timestamp": datetime.utcnow().isoformat()})
            }

    return EventSourceResponse(event_generator())
```

### 5. 前端集成
```typescript
// AMfrontend/src/services/conversationService.ts

class ConversationService {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private lastEventId: string | null = null;

  async startConversation(message: string): Promise<string> {
    const response = await fetch('/api/v1/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initial_message: message })
    });

    const { conversation_id, sse_endpoint } = await response.json();
    this.connectSSE(conversation_id);

    return conversation_id;
  }

  connectSSE(conversationId: string) {
    const url = `/api/v1/conversations/${conversationId}/stream`;

    // EventSource自动使用Last-Event-ID重连
    this.eventSource = new EventSource(url);

    this.eventSource.addEventListener('status', (e) => {
      this.lastEventId = e.lastEventId;
      const data = JSON.parse(e.data);
      this.handleStatusEvent(data);
    });

    this.eventSource.addEventListener('agent_result', (e) => {
      this.lastEventId = e.lastEventId;
      const data = JSON.parse(e.data);
      this.handleAgentResult(data);
    });

    this.eventSource.addEventListener('final_answer', (e) => {
      this.lastEventId = e.lastEventId;
      const data = JSON.parse(e.data);
      this.handleFinalAnswer(data);
      this.reconnectAttempts = 0; // 成功完成后重置
    });

    this.eventSource.addEventListener('error', (e) => {
      if (e.target.readyState === EventSource.CLOSED) {
        this.handleDisconnection();
      }
    });

    this.eventSource.onerror = (error) => {
      console.error('SSE错误:', error);
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnect(conversationId);
      }
    };
  }

  handleDisconnection() {
    console.log('SSE连接已关闭');
    // 对话在后端继续执行！
    // 用户可以刷新页面并恢复
  }

  reconnect(conversationId: string) {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

    console.log(`将在${delay}ms后重连（第${this.reconnectAttempts}次尝试）`);

    setTimeout(() => {
      this.eventSource?.close();
      this.connectSSE(conversationId);
    }, delay);
  }

  async continueConversation(conversationId: string, message: string) {
    const response = await fetch(`/api/v1/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    return await response.json();
  }

  async getConversationHistory(conversationId: string) {
    const response = await fetch(`/api/v1/conversations/${conversationId}`);
    return await response.json();
  }
}
```

## 优势

### 1. 前端断线恢复能力
- ✅ 即使前端断开，工作流仍继续执行
- ✅ 使用`Last-Event-ID`自动重连并重放事件
- ✅ 用户可以刷新页面并恢复对话
- ✅ 心跳事件检测过期连接

### 2. 对话持久化
- ✅ 完整对话历史存储在数据库
- ✅ 可以查看过去的对话
- ✅ 可以分析用户模式和偏好
- ✅ 支持对话导出/导入

### 3. 更好的错误处理
- ✅ 错误与完整堆栈跟踪一起存储，便于调试
- ✅ 工作流状态追踪（pending、running、completed、error）
- ✅ 可以重试失败的工作流
- ✅ 优雅降级

### 4. 可扩展性
- ✅ 后台任务队列分散负载
- ✅ Redis pub/sub处理多个SSE客户端
- ✅ 数据库持久化状态以便崩溃恢复
- ✅ 无状态API服务器

### 5. 用户体验
- ✅ 跨会话的对话历史
- ✅ 可以恢复中断的对话
- ✅ 更好的错误消息
- ✅ 加载状态和进度追踪

## 迁移计划

### 阶段1: 数据库设置
1. 创建数据库表
2. 使用Alembic添加迁移脚本
3. 创建SQLAlchemy模型

### 阶段2: 会话管理器
1. 实现`SessionManager`类
2. 添加对话CRUD操作
3. 添加工作流执行追踪

### 阶段3: 后台任务
1. 设置Redis和Celery
2. 实现`execute_workflow_task`
3. 添加事件发布

### 阶段4: API接口
1. 实现新的对话接口
2. 更新现有的`/api/v1/research/ask`使用新架构
3. 添加SSE重连支持

### 阶段5: 前端迁移
1. 更新`ResearchChat.tsx`使用新API
2. 实现对话历史UI
3. 添加重连处理

### 阶段6: 测试和部署
1. 测试重连场景
2. 多对话负载测试
3. 监控错误率和性能
4. 逐步推出

## 技术栈

- **数据库**: PostgreSQL（存储对话、消息、工作流执行）
- **缓存**: Redis（SSE连接追踪、事件pub/sub）
- **任务队列**: Celery + Redis broker
- **SSE**: sse-starlette（FastAPI SSE支持）
- **前端**: EventSource API + 重连机制

## 下一步

1. 审查并批准架构设计
2. 估算实施时间线
3. 创建详细的实施任务
4. 搭建带有Redis和Celery的开发环境
5. 开始阶段1: 数据库设置
