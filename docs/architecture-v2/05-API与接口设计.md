# API与接口设计

> 版本: 2.0  
> 更新日期: 2025-11-05  
> 目标: 定义前后端通信规范

---

## 一、API设计原则

### 1.1 核心原则

1. **RESTful风格**: 资源导向，语义化URL
2. **统一响应格式**: 成功/失败统一结构
3. **版本控制**: `/api/v1/...` 支持未来升级
4. **限流保护**: 防止滥用
5. **错误友好**: 清晰的错误码和提示

### 1.2 通用响应格式

**成功响应**:
```json
{
  "success": true,
  "data": {...},
  "timestamp": "2025-11-05T12:00:00Z"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "账户余额不足",
    "details": {
      "required": 1000,
      "available": 500
    }
  },
  "timestamp": "2025-11-05T12:00:00Z"
}
```

---

## 二、认证与授权

### 2.1 Google OAuth登录

**流程**:
```
前端 → Google OAuth → 获取code
  ↓
POST /api/v1/auth/google
  Body: { code: "..." }
  ↓
后端验证code → 创建/更新用户 → 生成JWT
  ↓
返回: { token, user }
```

**接口定义**:
```
POST /api/v1/auth/google
Content-Type: application/json

Request:
{
  "code": "4/0AfJoh...",
  "redirect_uri": "http://localhost:5173/auth/callback"
}

Response:
{
  "success": true,
  "data": {
    "token": "eyJhbGci...",
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "name": "John Doe",
      "avatar": "https://..."
    }
  }
}
```

### 2.2 JWT认证

**Token格式**:
```json
{
  "sub": "user_123",
  "email": "user@example.com",
  "exp": 1699200000,
  "iat": 1699113600
}
```

**使用方式**:
```
GET /api/v1/portfolio
Authorization: Bearer eyJhbGci...
```

**过期策略**:
- Access Token: 7天
- 无Refresh Token（简化实现）
- 过期后重新Google登录

---

## 三、核心API接口

### 3.1 投资组合管理

#### GET /api/v1/portfolio

**描述**: 获取用户投资组合

**请求**:
```
GET /api/v1/portfolio
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_value": 45000.50,
    "initial_capital": 10000.00,
    "realized_pnl": 2000.30,
    "unrealized_pnl": 33000.20,
    "total_return_pct": 350.05,
    "holdings": [
      {
        "asset": "BTC",
        "quantity": 0.5,
        "avg_cost": 40000.00,
        "current_price": 45000.00,
        "value": 22500.00,
        "unrealized_pnl": 2500.00,
        "pnl_pct": 12.5
      }
    ],
    "last_updated": "2025-11-05T12:00:00Z"
  }
}
```

---

### 3.2 策略管理

#### GET /api/v1/strategies

**描述**: 获取所有可用策略

**请求**:
```
GET /api/v1/strategies
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "hodl-wave",
      "name": "HODL Wave 宏观波段",
      "description": "基于宏观、链上、技术分析的中长期策略",
      "timeframe": "4小时",
      "risk_level": "中",
      "min_capital": 1000,
      "historical_performance": {
        "sharpe_ratio": 1.8,
        "max_drawdown": -18.5,
        "win_rate": 65.2,
        "total_return_pct": 156.3
      },
      "agent_weights": {
        "macro": 0.4,
        "onchain": 0.4,
        "ta": 0.2
      },
      "is_subscribed": true
    }
  ]
}
```

#### POST /api/v1/strategies/{strategy_id}/subscribe

**描述**: 订阅策略

**请求**:
```
POST /api/v1/strategies/hodl-wave/subscribe
Authorization: Bearer <token>

{
  "initial_capital": 5000
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "subscription_id": "sub_123",
    "strategy_id": "hodl-wave",
    "status": "active",
    "created_at": "2025-11-05T12:00:00Z"
  }
}
```

---

### 3.3 Agent分析查询

#### GET /api/v1/agents/scores

**描述**: 获取最新Agent分析结果

**请求**:
```
GET /api/v1/agents/scores?strategy_id=hodl-wave
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "strategy_id": "hodl-wave",
    "execution_id": "exec_abc123",
    "timestamp": "2025-11-05T12:00:00Z",
    "agents": {
      "macro": {
        "score": 0.75,
        "confidence": 0.85,
        "reasoning": "ETF净流入强劲，降息预期提升...",
        "signals": {
          "etf_flow": "positive",
          "fed_rate": "dovish"
        }
      },
      "onchain": {
        "score": 0.60,
        "confidence": 0.90,
        "reasoning": "MVRV处于健康区间，交易所流出增加...",
        "signals": {
          "mvrv": "healthy",
          "exchange_flow": "outflow"
        }
      },
      "ta": {
        "score": 0.45,
        "confidence": 0.75,
        "reasoning": "EMA金叉确认，但RSI显示超买...",
        "signals": {
          "ema": "bullish",
          "rsi": "overbought"
        }
      }
    },
    "decision": {
      "conviction_score": 72,
      "signal": "BUY",
      "reasoning": "宏观和链上强支撑，技术面短期超买可接受",
      "recommended_position": 0.005
    }
  }
}
```

---

### 3.4 SuperAgent对话

#### POST /api/v1/agents/chat

**描述**: 与SuperAgent对话

**请求**:
```
POST /api/v1/agents/chat
Authorization: Bearer <token>

{
  "message": "分析一下BTC当前行情",
  "context": {
    "strategy_id": "hodl-wave"
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "message_id": "msg_abc",
    "reply": "根据最新分析，BTC当前处于健康上升趋势...",
    "intent": {
      "type": "ANALYZE_MARKET",
      "confidence": 0.95
    },
    "actions_taken": [
      "触发MacroAgent分析",
      "触发OnChainAgent分析"
    ],
    "timestamp": "2025-11-05T12:00:00Z"
  }
}
```

---

### 3.5 交易历史

#### GET /api/v1/trades

**描述**: 获取交易记录

**请求**:
```
GET /api/v1/trades?strategy_id=hodl-wave&limit=20&offset=0
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "trades": [
      {
        "id": "trade_123",
        "strategy_id": "hodl-wave",
        "asset": "BTC",
        "action": "BUY",
        "quantity": 0.1,
        "price": 44500.00,
        "total_value": 4450.00,
        "conviction_score": 75,
        "timestamp": "2025-11-04T08:00:00Z",
        "status": "executed"
      }
    ],
    "pagination": {
      "total": 100,
      "limit": 20,
      "offset": 0
    }
  }
}
```

---

## 四、WebSocket事件

### 4.1 连接与认证

**连接URL**: `wss://api.automoney.app/ws`

**认证**:
```javascript
const socket = io('wss://api.automoney.app', {
  auth: {
    token: 'Bearer eyJhbGci...'
  }
})
```

### 4.2 事件列表

#### agent:scores

**触发**: Agent分析完成

**Payload**:
```json
{
  "strategy_id": "hodl-wave",
  "scores": {
    "macro": 0.75,
    "onchain": 0.60,
    "ta": 0.45
  },
  "conviction_score": 72,
  "timestamp": "2025-11-05T12:00:00Z"
}
```

#### decision:made

**触发**: 生成交易信号

**Payload**:
```json
{
  "strategy_id": "hodl-wave",
  "signal": "BUY",
  "conviction_score": 75,
  "reasoning": "强烈看多信号",
  "timestamp": "2025-11-05T12:00:00Z"
}
```

#### trade:executed

**触发**: 交易执行完成

**Payload**:
```json
{
  "trade_id": "trade_123",
  "asset": "BTC",
  "action": "BUY",
  "quantity": 0.1,
  "price": 44500.00,
  "timestamp": "2025-11-05T12:00:00Z"
}
```

#### portfolio:update

**触发**: 投资组合变化

**Payload**:
```json
{
  "total_value": 45000.50,
  "unrealized_pnl": 33000.20,
  "change_pct": 2.5,
  "timestamp": "2025-11-05T12:00:00Z"
}
```

---

## 五、错误码定义

| 错误码 | HTTP状态 | 描述 | 处理建议 |
|-------|---------|------|---------|
| `UNAUTHORIZED` | 401 | 未授权 | 重新登录 |
| `FORBIDDEN` | 403 | 无权限 | 升级订阅 |
| `NOT_FOUND` | 404 | 资源不存在 | 检查ID |
| `VALIDATION_ERROR` | 400 | 参数错误 | 检查请求参数 |
| `INSUFFICIENT_BALANCE` | 400 | 余额不足 | 充值 |
| `STRATEGY_NOT_FOUND` | 404 | 策略不存在 | 检查策略ID |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求过多 | 等待后重试 |
| `INTERNAL_ERROR` | 500 | 服务器错误 | 稍后重试 |
| `LLM_SERVICE_UNAVAILABLE` | 503 | LLM服务不可用 | 稍后重试 |

---

## 六、限流策略

### 6.1 限流规则

| 用户层级 | 限流规则 | 说明 |
|---------|---------|------|
| **免费用户** | 60次/小时 | 基础查询 |
| **付费用户** | 600次/小时 | 10倍提升 |
| **API用户** | 3000次/小时 | 专业版 |

### 6.2 限流响应

**触发限流**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试",
    "details": {
      "limit": 60,
      "remaining": 0,
      "reset_at": "2025-11-05T13:00:00Z"
    }
  }
}
```

**响应头**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699200000
```

---

## 七、API版本管理

### 7.1 版本策略

**当前**: `/api/v1/...`

**未来兼容**:
- v1继续维护12个月
- 新功能优先在v2实现
- 提前3个月通知废弃

### 7.2 废弃流程

1. **提前通知**: 3个月前在响应头添加`X-API-Deprecated: true`
2. **迁移指南**: 提供v1→v2迁移文档
3. **下线日期**: 明确下线时间

---

## 八、开发工具

### 8.1 API文档

**工具**: FastAPI自动生成Swagger文档

**访问**: `https://api.automoney.app/docs`

**特性**:
- 交互式测试
- 自动类型验证
- 示例请求/响应

### 8.2 SDK（未来）

**计划提供**:
- Python SDK
- TypeScript SDK
- 示例代码

---

**📌 关键Takeaway**: 
- RESTful API统一设计
- WebSocket实现实时推送
- JWT认证简单可靠
- 限流保护防止滥用

**下一步**: 阅读 `07-开发规范与最佳实践.md` 了解代码规范


