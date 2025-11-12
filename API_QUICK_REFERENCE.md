# API快速参考 - 策略系统重构版

## 🔐 权限说明

| 角色 | 代码 | 权限 |
|------|------|------|
| 普通用户 | `user` | 查看活跃策略实例 |
| 交易员 | `trader` | 创建实例、调整参数 |
| 管理员 | `admin` | 管理模板、系统配置 |

---

## 📡 API端点总览

### 策略模板管理（Admin Only）

```
GET    /api/v1/strategy-definitions          # 获取所有策略模板
GET    /api/v1/strategy-definitions/{id}     # 获取模板详情
PATCH  /api/v1/strategy-definitions/{id}     # 更新模板配置
```

---

### 策略实例管理（按角色）

```
GET    /api/v1/strategies                     # 获取实例列表
POST   /api/v1/strategies                     # 创建实例 (Trader/Admin)
GET    /api/v1/strategies/{id}                # 获取实例详情
PATCH  /api/v1/strategies/{id}                # 更新实例 (Trader/Admin)
DELETE /api/v1/strategies/{id}                # 删除实例 (Trader/Admin)

GET    /api/v1/strategies/{id}/executions     # 获取执行历史
GET    /api/v1/strategies/{id}/trades         # 获取交易记录
```

---

### 配置管理（Admin Only）

```
GET    /api/v1/admin/agents                   # Agent注册表
GET    /api/v1/admin/tools                    # Tool注册表
GET    /api/v1/admin/apis                     # API配置列表
PATCH  /api/v1/admin/apis/{api_name}          # 更新API配置
```

---

## 📋 数据模型

### StrategyDefinition（策略模板）

```json
{
  "id": 1,
  "name": "multi_agent_btc_v1",
  "display_name": "Multi-Agent BTC Strategy",
  "description": "使用宏观、链上、技术分析三个Agent的BTC现货策略",
  "decision_agent_module": "app.decision_agents.multi_agent_conviction",
  "decision_agent_class": "MultiAgentConvictionDecision",
  "business_agents": ["macro", "ta", "onchain"],
  "trade_channel": "binance_spot",
  "trade_symbol": "BTC",
  "rebalance_period_minutes": 10,
  "default_params": {
    "agent_weights": {"macro": 0.4, "onchain": 0.4, "ta": 0.2},
    "buy_threshold": 50,
    "partial_sell_threshold": 50,
    "full_sell_threshold": 45,
    "consecutive_signal_threshold": 30,
    "acceleration_multiplier_min": 1.1,
    "acceleration_multiplier_max": 2.0,
    "fg_circuit_breaker_threshold": 20,
    "fg_position_adjust_threshold": 30
  },
  "is_active": true
}
```

---

### Portfolio（策略实例）

```json
{
  "id": "uuid-here",
  "strategy_definition_id": 1,
  "user_id": 123,
  "instance_name": "Multi-Agent BTC Strategy - 张三 - #1",
  "instance_description": "测试用，高风险配置",
  "instance_params": {
    "agent_weights": {"macro": 0.5, "onchain": 0.3, "ta": 0.2},
    "buy_threshold": 60,
    "full_sell_threshold": 40
  },
  "initial_balance": 10000,
  "current_balance": 9500,
  "total_value": 10500,
  "total_pnl": 500,
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## 🔧 API使用示例

### 1. 获取策略模板列表（Admin）

**Request:**
```bash
GET /api/v1/strategy-definitions
Authorization: Bearer <ADMIN_TOKEN>
```

**Response:**
```json
{
  "definitions": [
    {
      "id": 1,
      "name": "multi_agent_btc_v1",
      "display_name": "Multi-Agent BTC Strategy",
      "business_agents": ["macro", "ta", "onchain"],
      "default_params": {...}
    }
  ],
  "total": 1
}
```

---

### 2. 创建策略实例（Trader）

**Request:**
```bash
POST /api/v1/strategies
Authorization: Bearer <TRADER_TOKEN>
Content-Type: application/json

{
  "strategy_definition_id": 1,
  "instance_name": "我的测试策略",
  "instance_description": "用于测试新架构",
  "initial_balance": 10000,
  "instance_params": {
    "buy_threshold": 55,
    "full_sell_threshold": 42
  }
}
```

**Response:**
```json
{
  "success": true,
  "portfolio_id": "uuid-here",
  "instance_name": "我的测试策略",
  "strategy_definition_id": 1,
  "initial_balance": 10000,
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

### 3. 获取实例列表（按角色）

**普通用户:**
```bash
GET /api/v1/strategies
Authorization: Bearer <USER_TOKEN>
```
返回：仅is_active=true的实例

**交易员/Admin:**
```bash
GET /api/v1/strategies?active_only=false
Authorization: Bearer <TRADER_TOKEN>
```
返回：所有实例

---

### 4. 更新实例参数（Trader）

**Request:**
```bash
PATCH /api/v1/strategies/{portfolio_id}
Authorization: Bearer <TRADER_TOKEN>
Content-Type: application/json

{
  "instance_name": "更新后的名称",
  "instance_params": {
    "buy_threshold": 65,
    "agent_weights": {"macro": 0.6, "onchain": 0.2, "ta": 0.2}
  }
}
```

**Response:**
```json
{
  "success": true,
  "portfolio_id": "uuid-here",
  "instance_name": "更新后的名称",
  "message": "Instance updated successfully"
}
```

---

### 5. 获取Agent注册表（Admin）

**Request:**
```bash
GET /api/v1/admin/agents
Authorization: Bearer <ADMIN_TOKEN>
```

**Response:**
```json
[
  {
    "id": 1,
    "agent_name": "macro",
    "display_name": "The Oracle - 宏观分析Agent",
    "agent_module": "app.agents.macro_agent",
    "agent_class": "MacroAgent",
    "available_tools": ["fetch_macro_data", "fetch_fear_greed"],
    "is_active": true
  },
  ...
]
```

---

### 6. 更新API配置（Admin）

**Request:**
```bash
PATCH /api/v1/admin/apis/binance_api
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json

{
  "api_key_encrypted": "new-api-key-here",
  "rate_limit": 1500
}
```

**Response:**
```json
{
  "id": 1,
  "api_name": "binance_api",
  "display_name": "Binance API",
  "api_key_masked": "abc1...xyz9",
  "rate_limit": 1500,
  "is_active": true
}
```

---

## 🔄 数据库查询示例

### 查看所有策略模板
```sql
SELECT 
    id, 
    name, 
    display_name,
    business_agents,
    rebalance_period_minutes,
    is_active
FROM strategy_definitions
ORDER BY created_at DESC;
```

---

### 查看所有策略实例
```sql
SELECT 
    p.id,
    p.instance_name,
    sd.display_name as template_name,
    u.email as user_email,
    p.is_active,
    p.initial_balance,
    p.total_value,
    p.total_pnl,
    p.created_at
FROM portfolios p
LEFT JOIN strategy_definitions sd ON p.strategy_definition_id = sd.id
LEFT JOIN "user" u ON p.user_id = u.id
ORDER BY p.created_at DESC;
```

---

### 查看实例参数
```sql
SELECT 
    instance_name,
    jsonb_pretty(instance_params) as params
FROM portfolios
WHERE id = 'uuid-here';
```

---

### 查看按模板分组的实例数
```sql
SELECT 
    sd.display_name,
    COUNT(p.id) as instance_count,
    COUNT(CASE WHEN p.is_active THEN 1 END) as active_count
FROM strategy_definitions sd
LEFT JOIN portfolios p ON sd.id = p.strategy_definition_id
GROUP BY sd.id, sd.display_name
ORDER BY instance_count DESC;
```

---

## 🎯 关键配置参数说明

### agent_weights（Agent权重）
```json
{
  "macro": 0.4,    // 宏观分析权重 40%
  "onchain": 0.4,  // 链上分析权重 40%
  "ta": 0.2        // 技术分析权重 20%
}
```
- 总和必须为1.0
- 影响最终conviction_score计算

---

### 交易阈值
```json
{
  "buy_threshold": 50,            // >= 50 买入
  "partial_sell_threshold": 50,   // 45-50 部分减仓
  "full_sell_threshold": 45       // < 45 全部清仓
}
```

---

### 连续信号机制
```json
{
  "consecutive_signal_threshold": 30,      // 连续30次触发加速
  "acceleration_multiplier_min": 1.1,      // 最小乘数1.1x
  "acceleration_multiplier_max": 2.0       // 最大乘数2.0x
}
```

---

### 熔断机制
```json
{
  "fg_circuit_breaker_threshold": 20,      // Fear & Greed < 20 暂停交易
  "fg_position_adjust_threshold": 30       // Fear & Greed < 30 减少仓位
}
```

---

## 📞 技术支持

### 查看日志
```bash
# 实时查看
tail -f AMbackend/server.log

# 搜索特定关键词
grep "策略执行" AMbackend/server.log | tail -20
grep "决策完成" AMbackend/server.log | tail -20
grep "批量执行" AMbackend/server.log | tail -20
```

---

### 常见问题

**Q: 如何修改现有模板的默认参数？**
```bash
PATCH /api/v1/strategy-definitions/1
{
  "default_params": {
    "buy_threshold": 60  # 只更新这个参数
  }
}
```
注意：只影响新创建的实例，现有实例不受影响

---

**Q: 如何调整已创建实例的参数？**
```bash
PATCH /api/v1/strategies/{portfolio_id}
{
  "instance_params": {
    "buy_threshold": 65
  }
}
```
注意：下次执行时立即生效

---

**Q: 如何停用某个实例？**
```bash
PATCH /api/v1/strategies/{portfolio_id}
{
  "is_active": false
}
```

---

**Q: 如何查看系统正在使用哪些Agent？**
```bash
GET /api/v1/admin/agents
```

---

**Q: 如何验证批量执行是否按模板分组？**
查看日志：
```bash
grep "按模板分组" AMbackend/server.log
grep "节省LLM调用" AMbackend/server.log
```

---

**最后更新:** 2024-01-15  
**版本:** v2.0.0





