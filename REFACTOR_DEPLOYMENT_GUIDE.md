# 策略系统重构 - 部署和测试指南

## 📋 概览

重构完成度：**14/15 (93%)**

核心架构已完成，可以开始部署和测试。

---

## 🚀 部署步骤

### 前置条件

1. **备份数据库**（重要！此次重构会删除所有Portfolio数据）
```bash
cd AMbackend
pg_dump automoney > backup_$(date +%Y%m%d_%H%M%S).sql
```

2. **确认Python环境**
```bash
# 激活虚拟环境（根据实际情况）
source venv/bin/activate
# 或
python3 -m venv venv && source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

### 步骤1：执行数据库迁移

```bash
cd AMbackend

# 检查当前迁移状态
alembic current

# 执行迁移（添加新表）
alembic upgrade head

# 验证表是否创建成功
psql automoney -c "\dt strategy_definitions"
psql automoney -c "\dt agent_registry"
psql automoney -c "\dt tool_registry"
psql automoney -c "\dt api_config"
```

**预期结果:**
- ✅ 4个新表创建成功
- ✅ portfolios表添加了新字段（strategy_definition_id, instance_name等）
- ✅ portfolios表删除了旧字段（strategy_name, agent_weights等）

---

### 步骤2：清理旧数据

```bash
cd AMbackend

# 删除所有旧的Portfolio数据
python scripts/cleanup_old_portfolios.py

# 输入 yes 确认
```

**预期结果:**
- ✅ 删除所有Portfolio、Trade、StrategyExecution等
- ✅ 保留User数据

---

### 步骤3：初始化策略模板

```bash
# 创建初始策略模板
python scripts/init_strategy_definitions.py

# 验证
psql automoney -c "SELECT id, name, display_name FROM strategy_definitions;"
```

**预期结果:**
- ✅ 创建 "Multi-Agent BTC Strategy" 模板
- ✅ 模板包含完整的default_params配置

---

### 步骤4：初始化注册表

```bash
# 初始化Agent/Tool/API注册表
python scripts/init_registries.py

# 验证
psql automoney -c "SELECT agent_name, display_name FROM agent_registry;"
psql automoney -c "SELECT tool_name, display_name FROM tool_registry;"
psql automoney -c "SELECT api_name, display_name FROM api_config;"
```

**预期结果:**
- ✅ 注册3个业务Agent（macro, ta, onchain）
- ✅ 注册4个Tools
- ✅ 注册6个API配置

---

### 步骤5：重启后端服务

```bash
cd AMbackend

# 停止旧服务
./stop.sh

# 启动新服务
./start.sh

# 监控日志
tail -f server.log
```

**检查日志应该看到:**
- ✅ "策略调度器已启动"
- ✅ 没有import错误
- ✅ 没有模型加载错误

---

## 🧪 测试清单

### 测试1：策略模板API（Admin）

```bash
# 获取所有策略模板
curl -X GET "http://localhost:8000/api/v1/strategy-definitions" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# 获取模板详情
curl -X GET "http://localhost:8000/api/v1/strategy-definitions/1" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# 更新模板配置
curl -X PATCH "http://localhost:8000/api/v1/strategy-definitions/1" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "更新后的描述",
    "rebalance_period_minutes": 15
  }'
```

**预期结果:**
- ✅ 返回策略模板列表
- ✅ 包含完整的default_params配置
- ✅ 更新成功

---

### 测试2：创建策略实例（交易员/Admin）

```bash
# 创建策略实例
curl -X POST "http://localhost:8000/api/v1/strategies" \
  -H "Authorization: Bearer <TRADER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_definition_id": 1,
    "instance_name": "我的测试策略",
    "instance_description": "用于测试重构功能",
    "initial_balance": 10000,
    "instance_params": {
      "agent_weights": {"macro": 0.5, "onchain": 0.3, "ta": 0.2},
      "buy_threshold": 55,
      "partial_sell_threshold": 48,
      "full_sell_threshold": 42
    }
  }'
```

**预期结果:**
- ✅ 创建成功，返回portfolio_id
- ✅ instance_name正确
- ✅ instance_params包含完整配置
- ✅ 实例自动激活（is_active=true）

---

### 测试3：自动命名生成

```bash
# 创建实例时不提供instance_name
curl -X POST "http://localhost:8000/api/v1/strategies" \
  -H "Authorization: Bearer <TRADER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_definition_id": 1,
    "initial_balance": 5000
  }'
```

**预期结果:**
- ✅ instance_name自动生成
- ✅ 格式：`Multi-Agent BTC Strategy - {用户名} - #1`

---

### 测试4：策略实例列表（按角色）

**普通用户:**
```bash
curl -X GET "http://localhost:8000/api/v1/strategies" \
  -H "Authorization: Bearer <USER_TOKEN>"
```
**预期:** 只返回is_active=true的实例

**交易员:**
```bash
curl -X GET "http://localhost:8000/api/v1/strategies" \
  -H "Authorization: Bearer <TRADER_TOKEN>"
```
**预期:** 返回所有实例（包括is_active=false）

---

### 测试5：更新策略实例

```bash
# 更新实例名称和参数
curl -X PATCH "http://localhost:8000/api/v1/strategies/{portfolio_id}" \
  -H "Authorization: Bearer <TRADER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "更新后的名称",
    "instance_params": {
      "buy_threshold": 60
    }
  }'
```

**预期结果:**
- ✅ 更新成功
- ✅ instance_params正确更新

---

### 测试6：批量执行优化

**设置：**
1. 创建2个基于同一模板的实例（同一definition_id）
2. 创建1个基于其他模板的实例（不同definition_id）

**等待调度器执行：**
- 等待10分钟（默认执行周期）
- 查看日志 `tail -f server.log`

**预期日志输出:**
```
开始批量执行策略（按模板分组）
找到 3 个活跃Portfolio，分为 2 个策略模板组
执行策略模板组: ID=1, 实例数=2
执行Agent分析（组内 2 个实例共享）
✅ Agent分析完成（第1次调用）
执行实例: 实例1
✅ 实例执行完成
执行实例: 实例2
✅ 实例执行完成
执行策略模板组: ID=2, 实例数=1
...
批量执行完成汇总:
  - 策略模板数: 2
  - 实例总数: 3
  - Agent调用次数: 2
  - 节省LLM调用: 1 次
```

**关键验证:**
- ✅ 相同模板的实例只调用1次Agent
- ✅ 不同模板的实例分别调用Agent
- ✅ LLM调用次数 = 模板数量（不是实例数量）

---

### 测试7：决策Agent动态加载

**验证方法:**
1. 查看orchestrator日志，应该看到：
```
已加载决策Agent: MultiAgentConvictionDecision
决策完成: signal=BUY, conviction=65.32, position_size=0.0035, should_execute=True
```

2. 检查StrategyExecution记录：
```sql
SELECT 
    id, 
    conviction_score, 
    signal, 
    position_size,
    risk_level
FROM strategy_executions
ORDER BY execution_time DESC
LIMIT 5;
```

**预期结果:**
- ✅ 决策Agent成功动态加载
- ✅ conviction_score正确计算
- ✅ signal/position_size/risk_level正确

---

### 测试8：Admin配置管理

```bash
# 获取Agent注册表
curl -X GET "http://localhost:8000/api/v1/admin/agents" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# 获取Tool注册表
curl -X GET "http://localhost:8000/api/v1/admin/tools" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# 获取API配置
curl -X GET "http://localhost:8000/api/v1/admin/apis" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# 更新API配置
curl -X PATCH "http://localhost:8000/api/v1/admin/apis/binance_api" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "更新的描述",
    "rate_limit": 1500
  }'
```

**预期结果:**
- ✅ 返回注册表数据
- ✅ API密钥被掩码显示
- ✅ 更新成功

---

### 测试9：权限控制

**场景1：普通用户尝试创建实例**
```bash
curl -X POST "http://localhost:8000/api/v1/strategies" \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -d '{"strategy_definition_id": 1, "initial_balance": 1000}'
```
**预期:** ❌ 403 Forbidden - "Trader or Admin access required"

**场景2：交易员尝试管理策略模板**
```bash
curl -X PATCH "http://localhost:8000/api/v1/strategy-definitions/1" \
  -H "Authorization: Bearer <TRADER_TOKEN>" \
  -d '{"description": "test"}'
```
**预期:** ❌ 403 Forbidden - "Admin access required"

**场景3：交易员创建实例**
```bash
curl -X POST "http://localhost:8000/api/v1/strategies" \
  -H "Authorization: Bearer <TRADER_TOKEN>" \
  -d '{"strategy_definition_id": 1, "initial_balance": 1000}'
```
**预期:** ✅ 200 OK - 创建成功

---

## 🐛 故障排查

### 问题1：迁移失败

**症状:** `alembic upgrade head` 报错

**解决:**
1. 检查down_revision是否正确指向最后一个迁移
2. 手动检查数据库表是否存在冲突
3. 如果必要，手动删除旧的迁移记录：
```sql
DELETE FROM alembic_version;
INSERT INTO alembic_version VALUES ('001_add_strategy_system');
```

---

### 问题2：Portfolio字段缺失

**症状:** 查询Portfolio时报错字段不存在

**原因:** 数据库迁移未执行或执行不完整

**解决:**
```bash
# 检查表结构
psql automoney -c "\d portfolios"

# 确认是否有新字段：
# - strategy_definition_id
# - instance_name
# - instance_description
# - instance_params

# 如果缺失，重新执行迁移
alembic downgrade -1
alembic upgrade head
```

---

### 问题3：决策Agent加载失败

**症状:** 日志显示 "加载决策Agent失败"

**原因:** 模块路径或类名错误

**解决:**
```sql
-- 检查strategy_definitions表的配置
SELECT 
    id, 
    name, 
    decision_agent_module, 
    decision_agent_class 
FROM strategy_definitions;

-- 应该是：
-- decision_agent_module = 'app.decision_agents.multi_agent_conviction'
-- decision_agent_class = 'MultiAgentConvictionDecision'
```

---

### 问题4：Portfolio无法关联definition

**症状:** `Portfolio {id} 未关联策略模板，跳过`

**原因:** Portfolio的strategy_definition_id为NULL

**解决:**
```sql
-- 检查哪些Portfolio未关联
SELECT id, instance_name, strategy_definition_id 
FROM portfolios 
WHERE strategy_definition_id IS NULL;

-- 如果有旧数据，删除它们
DELETE FROM portfolios WHERE strategy_definition_id IS NULL;
```

---

## 📊 数据验证

### 验证1：模板数据

```sql
SELECT 
    id,
    name,
    display_name,
    business_agents,
    trade_channel,
    rebalance_period_minutes,
    is_active
FROM strategy_definitions;
```

**预期:**
- 至少1条记录（Multi-Agent BTC Strategy）
- business_agents = ["macro", "ta", "onchain"]
- trade_channel = "binance_spot"

---

### 验证2：注册表数据

```sql
-- Agent注册表
SELECT agent_name, display_name FROM agent_registry;

-- Tool注册表
SELECT tool_name, display_name FROM tool_registry;

-- API配置
SELECT api_name, display_name, is_active FROM api_config;
```

**预期:**
- 3个Agent
- 4个Tool
- 6个API

---

### 验证3：实例创建

创建测试实例后：

```sql
SELECT 
    p.id,
    p.instance_name,
    p.strategy_definition_id,
    sd.display_name as strategy_name,
    p.initial_balance,
    p.is_active,
    jsonb_pretty(p.instance_params) as params
FROM portfolios p
LEFT JOIN strategy_definitions sd ON p.strategy_definition_id = sd.id
ORDER BY p.created_at DESC
LIMIT 5;
```

**验证要点:**
- ✅ instance_name正确
- ✅ strategy_definition_id关联正确
- ✅ instance_params包含完整配置

---

## 🎯 功能测试

### 测试场景1：交易员创建策略实例

**步骤:**
1. 使用交易员账号登录前端
2. 进入策略页面（/strategies）
3. 点击"创建新策略"按钮
4. 选择"Multi-Agent BTC Strategy"模板
5. 填写：
   - 实例名称：测试策略A
   - 初始资金：10000
   - 参数：修改buy_threshold为60
6. 提交创建

**验证:**
- ✅ 实例创建成功
- ✅ instance_name = "测试策略A"
- ✅ instance_params.buy_threshold = 60
- ✅ 其他参数使用模板默认值
- ✅ is_active = true

---

### 测试场景2：批量执行优化

**设置:**
1. 创建3个基于同一模板的实例
2. 每个实例配置不同的buy_threshold

**等待执行:**
- 等待10分钟自动执行
- 观察日志

**验证:**
```
# 日志应该显示：
执行策略模板组: ID=1, 实例数=3
执行Agent分析（组内 3 个实例共享）
✅ Agent分析完成（第1次调用）
执行实例: 测试策略A
✅ 实例执行完成 - signal: BUY
执行实例: 测试策略B
✅ 实例执行完成 - signal: HOLD
执行实例: 测试策略C
✅ 实例执行完成 - signal: BUY
Agent调用次数: 1
节省LLM调用: 2 次
```

**关键验证:**
- ✅ Agent只调用1次
- ✅ 3个实例产生不同的交易信号（因为参数不同）
- ✅ 节省了2次LLM调用成本

---

### 测试场景3：Admin配置管理

**步骤:**
1. Admin登录前端
2. 进入Admin页面
3. 切换到"基础模块配置"tab
4. 查看：
   - 业务Agent列表（应该显示3个）
   - Tool列表（应该显示4个）
   - API配置（应该显示6个，密钥被掩码）
   - 策略模板列表（应该显示1个）

**验证:**
- ✅ 所有注册表数据正确显示
- ✅ API密钥显示为 `abc1...xyz9`（掩码格式）
- ✅ 可以编辑API配置

---

## 📈 性能验证

### 验证1：LLM调用成本

**场景:** 10个实例，2个模板

**旧架构:**
- Agent调用次数 = 10次
- LLM成本 = 10x

**新架构:**
- Agent调用次数 = 2次（按模板分组）
- LLM成本 = 2x
- **节省80%成本！**

---

### 验证2：执行时间

**测量:**
```python
# 在scheduler日志中查看
批量执行完成汇总:
  - 策略模板数: 2
  - 实例总数: 10
  - Agent调用次数: 2
  - 执行总时间: XX秒
```

**预期:**
- 总时间应该 < (Agent执行时间 × 模板数 + 决策时间 × 实例数)
- 相比旧架构应该有显著提升

---

## ✅ 检查清单

部署后逐项检查：

- [ ] 数据库迁移成功
- [ ] 4个新表创建成功
- [ ] 策略模板初始化成功
- [ ] 注册表数据完整
- [ ] 后端服务启动正常
- [ ] 策略模板API可访问
- [ ] 策略实例API可访问
- [ ] Admin配置API可访问
- [ ] 创建实例功能正常
- [ ] 自动命名生成正常
- [ ] 权限控制正确
- [ ] 批量执行按模板分组
- [ ] Agent结果共享生效
- [ ] 决策Agent动态加载成功
- [ ] 从instance_params读参数正常

---

## 🎓 架构理解

### 数据流程

```
策略模板 (StrategyDefinition)
    ↓
    ↓ 创建实例（复制default_params）
    ↓
策略实例 (Portfolio)
    ↓
    ↓ 定时触发
    ↓
按模板分组 (Scheduler)
    ↓
    ↓ 组内共享
    ↓
业务Agent分析 (Macro/TA/OnChain)
    ↓
    ↓ 结果分发
    ↓
决策Agent决策 (每个实例独立)
    ↓
    ↓ 使用instance_params
    ↓
交易执行 (Paper Trading)
```

### 关键设计

1. **策略模板 = 产品定义**
   - 定义业务逻辑
   - 定义决策引擎
   - 提供默认参数
   
2. **策略实例 = 运行实体**
   - 独立资金
   - 独立参数
   - 独立执行状态

3. **批量优化 = 按模板分组**
   - 相同模板的实例共享业务Agent分析
   - 各实例使用自己的参数独立决策
   - 大幅降低LLM成本

---

## 🔜 后续工作

### 立即需要
1. [ ] 前端适配新API
2. [ ] 创建策略UI流程
3. [ ] Admin配置页面

### 近期计划
1. [ ] 添加第二个策略模板
2. [ ] 实现合约交易支持
3. [ ] 优化参数配置UI

---

**最后更新:** 2024-01-15
**状态:** 93%完成，核心重构全部完成，可开始部署测试





