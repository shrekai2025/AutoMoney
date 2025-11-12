# AutoMoney - 重构后的项目架构文档

**最后更新**: 2025-11-12  
**版本**: v2.0 (重构版)  
**工作目录**: /Users/uniteyoo/Documents/AutoMoney

---

## 项目概述

AutoMoney 是一个基于多Agent分析的量化交易策略平台，使用AI代理进行宏观经济、链上数据和技术分析，生成交易信号并执行模拟交易。

### 核心特性

- ✅ **策略模板系统** - 策略定义与实例分离
- ✅ **三级权限管理** - User/Trader/Admin角色
- ✅ **多Agent架构** - 宏观、链上、技术分析Agent
- ✅ **动态决策引擎** - 可配置的决策逻辑
- ✅ **批量执行优化** - 共享Agent分析结果，节省57% LLM成本
- ✅ **模拟交易引擎** - Paper Trading

---

## 核心概念

### 1. 策略模板 (Strategy Definition)

**定义**: 策略的"产品定义"，包含完整的策略逻辑配置。

**包含内容**:
- 需要调用哪些业务Agent（如macro, ta, onchain）
- 使用哪个决策Agent
- 交易渠道和币种
- 执行周期
- 默认参数

### 2. 策略实例 (Portfolio)

**定义**: 用户基于策略模板创建的可运行实例。

**特点**:
- 关联到特定的策略模板
- 有独立的初始资金
- 可以覆盖模板的默认参数
- 拥有独立的交易记录

### 3. 业务Agent

- **Macro Agent** - 宏观经济分析
- **TA Agent** - 技术分析
- **OnChain Agent** - 链上数据分析

### 4. 决策Agent

整合业务Agent输出，生成最终交易信号。当前实现：
- `MultiAgentConvictionDecision` - 基于信念分数的决策

---

## 系统架构

### 工作流程

```
用户选择策略模板
    ↓
配置参数 + 设置初始资金
    ↓
创建策略实例
    ↓
定时调度器触发
    ↓
1. 获取市场数据
    ↓
2. 执行业务Agent分析 (共享给同模板的所有实例)
    ↓
3. 对每个实例：
   - 加载决策Agent
   - 使用实例参数决策
   - 生成交易信号
    ↓
4. 执行交易
    ↓
5. 记录执行历史
```

### 批量执行优化

**传统方式**: 10个实例 = 30次Agent调用 (10×3)  
**优化方式**: 3次业务Agent + 10次决策 = 13次调用  
**节省**: 57%的LLM成本

---

## 数据模型

### 核心表

#### strategy_definitions (策略模板)
- name - 唯一标识
- display_name - 显示名称
- business_agents - 调用的业务Agent列表
- decision_agent_module - 决策Agent模块
- default_params - 默认参数

#### portfolios (策略实例)
- strategy_definition_id - 关联模板
- instance_name - 实例名称
- instance_params - 覆盖的参数
- initial_balance - 初始资金
- total_value - 当前总值
- total_pnl - 总盈亏

#### agent_registries (Agent注册表)
- agent_name - Agent标识
- agent_module - Python模块
- available_tools - 可用工具

#### tool_registries (Tool注册表)
- tool_name - Tool标识
- tool_function - Python函数
- required_apis - 依赖的API

#### api_configs (API配置)
- api_name - API标识
- base_url - API地址
- api_key_encrypted - 加密的密钥

---

## 权限系统

### User (普通用户)
- ✅ 查看活跃策略
- ❌ 不能创建策略

### Trader (交易员)
- ✅ 查看所有策略和模板
- ✅ 创建策略实例
- ✅ 修改自己的实例
- ❌ 不能管理系统配置

### Admin (管理员)
- ✅ 完全权限
- ✅ 管理Agent/Tool/API
- ✅ 修改策略模板

---

## API接口

### 策略实例 (/api/v1/strategies)

```http
GET /strategies - 获取策略实例列表
POST /strategies - 创建策略实例 (Trader/Admin)
PATCH /strategies/{id} - 更新实例 (Trader/Admin)
GET /strategies/{id}/executions - 获取执行历史
GET /strategies/{id}/trades - 获取交易记录
```

### 策略模板 (/api/v1/strategy-definitions)

```http
GET /strategy-definitions - 获取模板列表 (Trader/Admin)
GET /strategy-definitions/{id} - 获取模板详情
PATCH /strategy-definitions/{id} - 更新模板 (Admin)
```

### Admin管理 (/api/v1/admin)

```http
GET /admin/agents - 获取Agent列表 (Admin)
GET /admin/tools - 获取Tool列表 (Admin)
GET /admin/apis - 获取API配置 (Admin)
PATCH /admin/apis/{name} - 更新API配置 (Admin)
```

---

## 部署和维护

### 初始化

```bash
# 1. 数据库迁移
cd AMbackend
venv/bin/alembic upgrade head

# 2. 初始化注册表
venv/bin/python scripts/init_registries.py

# 3. 初始化策略模板
venv/bin/python scripts/init_strategy_definitions.py
```

### 启动服务

```bash
# 后端
cd AMbackend
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd AMfrontend
npm run dev
```

### 故障排查

**检查日志**:
```bash
tail -f AMbackend/server.log
```

**检查数据库迁移**:
```bash
cd AMbackend
venv/bin/alembic current
# 应该显示: 001_add_strategy_system
```

**检查服务状态**:
```bash
ps aux | grep uvicorn
curl http://localhost:8000/api/v1/auth/config
```

---

## 关键目录

```
/Users/uniteyoo/Documents/AutoMoney/
├── AMbackend/
│   ├── app/
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   ├── api/             # API端点
│   │   ├── agents/          # 业务Agent
│   │   └── decision_agents/ # 决策Agent
│   ├── alembic/             # 数据库迁移
│   └── scripts/             # 初始化脚本
├── AMfrontend/              # 前端代码
└── docs/                    # 文档
```

---

## 下一步工作

1. **前端更新** - 调用新的API端点
2. **移除旧路由** - 废弃 /marketplace
3. **添加新策略模板** - ETH, SOL等
4. **监控告警** - 执行失败通知

---

*文档版本: 2.0*  
*最后更新: 2025-11-12*  
*维护者: AI Assistant*
