<!-- 1e1b2841-a063-4839-81df-f8209263ca05 a98be041-0aa7-4931-9d0c-24fed3ec5a94 -->
# 策略系统重构计划

## 一、架构概览

### 核心概念

- **策略模板 (StrategyDefinition)**: 定义策略的业务逻辑、Agent组合、决策引擎、交易类型
- **策略实例 (Portfolio)**: 用户/交易员基于模板创建的可运行策略，包含独立参数和资金
- **业务Agent**: 公共分析组件（Macro/OnChain/TA等）
- **决策Agent**: 每个策略模板独享的决策逻辑（目前是ConvictionCalculator+SignalGenerator）
- **交易模块**: 公共执行组件，支持多种交易渠道

### 执行流程

```
定时触发 → 按模板分组 → 执行业务Agent（每组1次）→ 
分发给各实例 → 各自决策 → 各自交易
```

---

## 二、数据库模型重构

### 2.1 新增表：strategy_definitions（策略模板）

关键字段：

- `id`: 主键
- `name`: 唯一标识 (如 "multi_agent_btc_v1")
- `display_name`: 显示名称
- `description`: 描述
- `decision_agent_module/class`: 决策引擎代码引用
- `business_agents`: 业务Agent列表 (JSONB数组)
- `trade_channel`: 交易渠道 (binance_spot/hyperliquid_perp)
- `trade_symbol`: 交易币种 (BTC/ETH)
- `rebalance_period_minutes`: 执行周期
- `default_params`: 默认参数配置 (JSONB)
- `is_active`: 模板开关

### 2.2 修改表：portfolios（策略实例）

**新增字段：**

- `strategy_definition_id`: 关联到策略模板 (ForeignKey)
- `instance_name`: 实例名称，用户自定义 (String(200), required)
- `instance_description`: 实例描述，用户可选 (Text, optional)
- `instance_params`: 实例独立参数 (JSONB, required)

**移除字段：**

- `strategy_name`: 从关联的模板获取
- `rebalance_period_minutes`: 从模板获取
- `agent_weights`: 移入instance_params

**保留字段：**

- 资金相关：initial_balance, current_balance, total_value
- 统计相关：total_pnl, total_trades, win_rate等
- 状态：is_active (实例开关)
- 时间：created_at, last_execution_time

**命名规则：**

- 创建时生成默认：`{模板名称} - {用户名} - #{序号}`
- 用户可在创建或后续修改
- 允许同一用户基于同一模板创建多个实例

### 2.3 修改表：user（用户角色）

修改字段：

- `role`: 扩展为 "user" / "trader" / "admin"

### 2.4 新增表：agent_registry（业务Agent注册表）

用于文档展示，记录所有业务Agent：

- `agent_name`: 唯一标识 (如 "macro_agent")
- `display_name`: 显示名称 (如 "The Oracle")
- `description`: 功能描述
- `agent_module/class`: 代码路径
- `available_tools`: 可用工具列表 (JSONB)
- `is_active`: 状态

### 2.5 新增表：tool_registry（工具注册表）

用于文档展示，记录所有Tool：

- `tool_name`: 唯一标识
- `display_name/description`: 展示信息
- `tool_module/function`: 代码路径
- `required_apis`: 依赖的API列表 (JSONB)
- `is_active`: 状态

### 2.6 新增表：api_config（API配置表）

系统级API配置：

- `api_name`: 唯一标识 (如 "binance_api")
- `display_name/description`: 展示信息
- `base_url`: API地址
- `api_key_encrypted`: 加密存储的密钥
- `is_active`: 状态
- `rate_limit`: 速率限制

---

## 三、代码结构重构

### 3.1 决策Agent目录

新建：`AMbackend/app/decision_agents/`

```
decision_agents/
├── __init__.py
├── base.py  # 预留：未来的抽象基类
└── multi_agent_conviction.py
    └── MultiAgentConvictionDecision (整合Conviction+Signal)
```

### 3.2 策略模板管理服务

新建：[`app/services/strategy/definition_service.py`](app/services/strategy/definition_service.py)

- `get_all_definitions()`: 获取所有模板
- `get_definition_by_id()`: 获取模板详情
- `create_instance_from_definition()`: 从模板创建实例（含命名生成）
- `update_definition_params()`: 更新模板默认参数
- `generate_default_instance_name()`: 生成默认实例名称

### 3.3 重命名服务文件

- `marketplace_service.py` → `instance_service.py`

修改：[`app/services/strategy/instance_service.py`](app/services/strategy/instance_service.py)

- 所有方法改为操作策略实例
- 增加实例命名、描述管理

### 3.4 注册机制服务

新建：[`app/services/agents/agent_manager.py`](app/services/agents/agent_manager.py)

新建：[`app/services/tools/tool_manager.py`](app/services/tools/tool_manager.py)

新建：[`app/services/apis/api_manager.py`](app/services/apis/api_manager.py)

用途：管理注册表数据，供Admin页面查询展示

### 3.5 Scheduler改造

修改：[`app/services/strategy/scheduler.py`](app/services/strategy/scheduler.py)

核心变更：

```python
async def batch_execute_by_definitions():
    # 按 strategy_definition_id 分组
    grouped = await get_instances_grouped_by_definition()
    
    for definition_id, instances in grouped.items():
        definition = await get_definition(definition_id)
        
        # 执行一次业务Agent（该模板的所有实例共享）
        agent_outputs = await execute_business_agents(
            definition.business_agents
        )
        
        # 各实例独立决策和交易
        for instance in instances:
            decision_agent = load_decision_agent(
                definition.decision_agent_module,
                definition.decision_agent_class
            )
            
            signal = decision_agent.decide(
                agent_outputs, 
                instance.instance_params
            )
            
            await execute_trade(instance, signal, definition.trade_channel)
```

---

## 四、API端点重构

### 4.1 路由统一：marketplace → strategies

**文件重命名：**

- `endpoints/marketplace.py` → `endpoints/strategy_instances.py`

**路由前缀修改：**

```python
# api/v1/api.py
api_router.include_router(
    strategy_instances.router,
    prefix="/strategies",  # 原 /marketplace
    tags=["strategies"],
)
```

### 4.2 权限依赖函数

修改：[`app/core/deps.py`](app/core/deps.py)

新增：

```python
async def get_current_trader_or_admin():
    """要求交易员或管理员权限"""
    if current_user.role not in ["trader", "admin"]:
        raise HTTPException(403, "Trader or Admin access required")
    return current_user
```

### 4.3 策略模板API（仅Admin）

新建：[`app/api/v1/endpoints/strategy_definitions.py`](app/api/v1/endpoints/strategy_definitions.py)

```
GET    /api/v1/strategy-definitions       # 获取所有模板
GET    /api/v1/strategy-definitions/{id}  # 获取模板详情
PATCH  /api/v1/strategy-definitions/{id}  # 更新模板配置
```

### 4.4 策略实例API

修改：[`app/api/v1/endpoints/strategy_instances.py`](app/api/v1/endpoints/strategy_instances.py)

```
GET    /api/v1/strategies                 # 获取实例列表（按角色过滤）
POST   /api/v1/strategies                 # 创建实例（交易员/Admin）
GET    /api/v1/strategies/{id}            # 获取实例详情
PATCH  /api/v1/strategies/{id}            # 更新实例名称/描述/参数
DELETE /api/v1/strategies/{id}            # 停止/删除实例

GET    /api/v1/strategies/{id}/executions # 执行历史
GET    /api/v1/strategies/{id}/trades     # 交易记录
```

**权限逻辑：**

- GET列表：普通用户只看is_active=true，交易员/Admin看全部
- POST/PATCH/DELETE：仅交易员/Admin

**创建实例请求体：**

```json
{
  "strategy_definition_id": 1,
  "instance_name": "张三的激进BTC策略",  // 可选，不填则自动生成
  "instance_description": "测试用，高风险参数",  // 可选
  "initial_balance": 10000,
  "instance_params": {
    "agent_weights": {"macro": 0.5, "onchain": 0.3, "ta": 0.2},
    "buy_threshold": 55,
    // ... 所有参数
  }
}
```

### 4.5 Admin配置API

扩展：[`app/api/v1/endpoints/admin.py`](app/api/v1/endpoints/admin.py)

新增"基础模块配置"相关：

```
GET    /api/v1/admin/agents        # Agent注册表
GET    /api/v1/admin/tools         # Tool注册表
GET    /api/v1/admin/apis          # API配置列表
PATCH  /api/v1/admin/apis/{name}   # 更新API密钥等
```

---

## 五、前端改动指引

### 5.1 路由修改

```typescript
// 旧路由
/marketplace → /strategies

// API调用
/api/v1/marketplace/* → /api/v1/strategies/*
```

### 5.2 策略页面（/strategies）

**卡片展示格式：**

```
┌─────────────────────────────────────┐
│ 张三的激进BTC策略                    │ ← instance_name
│ Multi-Agent BTC Strategy           │ ← 来自definition
│ 测试用，高风险参数                   │ ← instance_description
│                                     │
│ 年化收益: +45.2%  初始: $10,000    │
│ 状态: 运行中  创建: 2024-01-15     │
│                                     │
│ [详情] [调参] [停止]  (交易员可见)  │
└─────────────────────────────────────┘
```

**筛选和排序：**

- 按模板筛选
- 按用户筛选（Admin）
- 按状态筛选
- 按收益、时间排序

**创建流程（交易员/Admin）：**

1. 点击"创建新策略"按钮
2. 弹窗：选择策略模板（展示模板列表）
3. 选择后：进入参数配置表单

   - 实例名称（预填生成的默认值，可修改）
   - 实例描述（可选）
   - 初始资金
   - 参数配置（展示模板默认值，可修改）

4. 提交创建，自动激活并开始运行

### 5.3 Admin页面

新增tab："基础模块配置"

4个section：

1. **业务Agent** - 表格展示agent_registry
2. **Tools** - 表格展示tool_registry
3. **APIs** - 表格展示api_config，可编辑密钥
4. **策略模板** - 表格展示strategy_definitions，可编辑基本信息和默认参数

---

## 六、数据迁移

### 6.1 Alembic迁移脚本

创建迁移：`alembic revision -m "add_strategy_system_tables"`

包含：

- 新增4个表（strategy_definitions等）
- 修改user.role枚举
- 修改portfolios表结构

### 6.2 初始化脚本

**scripts/init_strategy_definitions.py** - 创建初始模板

```python
definition = StrategyDefinition(
    name="multi_agent_btc_v1",
    display_name="Multi-Agent BTC Strategy",
    description="使用宏观、链上、技术分析三个Agent的BTC现货策略",
    decision_agent_module="app.decision_agents.multi_agent_conviction",
    decision_agent_class="MultiAgentConvictionDecision",
    business_agents=["macro", "ta", "onchain"],
    trade_channel="binance_spot",
    trade_symbol="BTC",
    rebalance_period_minutes=10,
    default_params={...所有参数...}
)
```

**scripts/init_registries.py** - 填充注册表

- 注册macro/ta/onchain agents
- 注册tools（后续逐步完善）
- 注册APIs（binance, glassnode等）

**scripts/cleanup_old_portfolios.py** - 清理旧数据

- 删除所有Portfolio及关联数据
- 保留User

### 6.3 执行顺序

```bash
# 1. 数据库迁移
alembic upgrade head

# 2. 清理旧数据
python scripts/cleanup_old_portfolios.py

# 3. 初始化新数据
python scripts/init_strategy_definitions.py
python scripts/init_registries.py
```

---

## 七、实施步骤

### 阶段1：数据库层（2-3小时）

1. 创建模型类（4个新表）
2. 创建Alembic迁移脚本
3. 编写初始化脚本
4. 测试迁移执行

### 阶段2：核心服务层（4-5小时）

1. 创建decision_agents目录和MultiAgentConvictionDecision
2. 实现definition_service（模板管理）
3. 重构instance_service（原marketplace_service）
4. 实现注册表管理服务（agent/tool/api_manager）
5. 改造scheduler按模板分组执行
6. 改造orchestrator动态加载决策agent

### 阶段3：API层（2-3小时）

1. 修改deps.py添加交易员权限检查
2. 创建strategy_definitions端点
3. 重构strategy_instances端点（原marketplace）
4. 扩展admin端点添加配置管理
5. 更新api.py路由配置

### 阶段4：测试验证（2小时）

1. 测试模板创建和查询
2. 测试实例创建流程（含命名生成）
3. 测试批量执行优化
4. 测试权限控制
5. 测试实例命名和描述更新

### 阶段5：前端对接（由前端团队）

1. 更新路由和API调用路径
2. 实现策略创建流程UI
3. 实现Admin配置页面
4. 适配新的数据结构

---

## 八、关键设计细节

### 8.1 实例命名生成逻辑

```python
async def generate_default_instance_name(
    definition: StrategyDefinition,
    user: User,
    db: AsyncSession
) -> str:
    # 查询该用户基于该模板已创建的实例数
    count = await get_instance_count_by_user_and_definition(
        user.id, definition.id, db
    )
    
    return f"{definition.display_name} - {user.full_name} - #{count + 1}"
```

### 8.2 参数继承逻辑

创建实例时：

```python
# 从模板复制默认参数
instance_params = definition.default_params.copy()

# 用户提供的参数覆盖默认值
if user_provided_params:
    instance_params.update(user_provided_params)

portfolio = Portfolio(
    instance_params=instance_params,
    # ...
)
```

### 8.3 决策Agent动态加载

```python
def load_decision_agent(module_path: str, class_name: str):
    """动态加载决策Agent类"""
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)
    return agent_class()
```

---

## 九、注意事项

1. **API密钥安全**：使用cryptography.fernet加密存储
2. **批量执行性能**：注意数据库N+1查询，使用joinedload
3. **错误隔离**：单个实例失败不影响其他实例
4. **日志详细**：记录模板ID、实例ID、决策过程
5. **实例命名唯一性**：不强制唯一，允许重名（靠ID区分）

---

## 十、未来扩展预留

1. **决策Agent抽象**：base.py预留BaseDecisionAgent接口
2. **版本管理**：strategy_definitions.version字段
3. **实盘模式**：portfolios.trading_mode (paper/live)
4. **合约支持**：trade_channel扩展值
5. **Tool配置化**：tool_registry.config (JSONB)

### To-dos

- [ ] 创建新模型类：StrategyDefinition、AgentRegistry、ToolRegistry、APIConfig；修改User和Portfolio模型
- [ ] 创建Alembic迁移脚本，添加4个新表，修改user和portfolios表结构
- [ ] 编写初始化脚本：init_strategy_definitions.py、init_registries.py、cleanup_old_portfolios.py
- [ ] 创建decision_agents目录，实现MultiAgentConvictionDecision类（整合Conviction+Signal）
- [ ] 实现definition_service.py：模板CRUD、实例创建、命名生成逻辑
- [ ] 重构marketplace_service为instance_service，更新所有实例管理逻辑
- [ ] 实现agent_manager、tool_manager、api_manager（注册表管理）
- [ ] 改造scheduler：按definition_id分组、Agent结果共享、动态加载决策Agent
- [ ] 改造orchestrator：支持从definition获取配置、从instance_params读参数
- [ ] 修改deps.py：添加get_current_trader_or_admin权限函数
- [ ] 创建strategy_definitions.py端点（Admin管理模板）
- [ ] 重构marketplace.py为strategy_instances.py，更新路由为/strategies
- [ ] 扩展admin.py：添加Agent/Tool/API配置管理端点
- [ ] 更新api.py路由配置，统一为/strategies前缀
- [ ] 测试：模板创建、实例创建、命名生成、批量执行、权限控制