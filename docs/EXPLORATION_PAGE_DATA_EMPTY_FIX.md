# Exploration页面数据为空问题修复

## 问题描述

用户反馈：策略每16分钟执行一次，但Exploration Hub页面数据仍然有很多为空（N/A），不正常。

## 问题分析

### 根本原因

**Agent执行记录查询没有按user_id过滤**

1. `get_latest_executions()` 方法没有 `user_id` 参数
2. 查询时没有过滤用户，导致：
   - 可能查询到其他用户的记录
   - 或者查询不到任何记录（如果数据库中有多个用户的记录，但最新的是其他用户的）

### 数据流程

```
策略执行（每16分钟）
  ↓
执行Agent（macro_agent, ta_agent, onchain_agent）
  ↓
记录Agent执行结果（AgentExecution表，包含user_id）
  ↓
查询Agent执行记录（get_latest_executions）
  ❌ 问题：没有按user_id过滤
  ↓
Exploration API返回数据
  ↓
前端显示（显示N/A或空数据）
```

## 修复方案

### 1. 修改 `get_latest_executions` 方法

**文件**: `AMbackend/app/services/agents/execution_recorder.py`

**修改内容**:
- 添加 `user_id` 参数
- 添加用户过滤条件

```python
async def get_latest_executions(
    self,
    db: AsyncSession,
    agent_names: Optional[List[str]] = None,
    user_id: Optional[int] = None,  # 新增参数
) -> Dict[str, AgentExecution]:
    # ...
    if user_id is not None:
        query = query.where(AgentExecution.user_id == user_id)
    # ...
```

### 2. 修改API调用处

**文件**: `AMbackend/app/api/v1/endpoints/exploration.py`

**修改位置**:
1. `get_squad_decision_core()` - 查询Agent执行记录
2. `get_data_stream()` - 查询Agent执行记录用于数据流

**修改内容**:
```python
# 修改前
latest_executions = await agent_execution_recorder.get_latest_executions(db)

# 修改后
latest_executions = await agent_execution_recorder.get_latest_executions(db, user_id=current_user.id)
```

### 3. 添加必要的导入

**文件**: `AMbackend/app/services/agents/execution_recorder.py`

```python
from sqlalchemy import select, and_, or_, desc  # 添加 or_（虽然最终没用到，但保留以防需要）
```

## 验证检查清单

### Agent执行记录
- [x] `get_latest_executions` 支持 `user_id` 参数
- [x] 查询时正确过滤用户
- [x] API调用时传入 `current_user.id`

### 策略执行记录
- [x] `get_commander_analysis` 使用 `StrategyExecution.user_id == current_user.id` ✓
- [x] `get_active_directive` 使用 `StrategyExecution.user_id == current_user.id` ✓

### 数据关联
- [x] Agent执行时正确设置 `user_id`（从portfolio.user_id获取）✓
- [x] 策略执行时正确设置 `user_id`（从portfolio.user_id获取）✓

## 预期效果

修复后，Exploration页面应该能够：

1. **正确显示Agent数据**
   - MacroAgent: ETF Net Flow, Fed Rate（如果有数据）
   - OnChainAgent: MVRV Z-Score, Exchange Flow（如果有数据）
   - TAAgent: RSI, Trend Status（如果有数据）

2. **正确显示AI Commander数据**
   - Market Analysis Summary（从StrategyExecution.llm_summary获取）
   - Conviction Score（从StrategyExecution.conviction_score获取）

3. **正确显示Active Directive数据**
   - 策略名称、倒计时、操作指令等

4. **正确显示Data Stream数据**
   - Macro、OnChain、TA数据流

## 注意事项

1. **数据可用性**
   - 某些数据（如ETF Net Flow）可能因为数据源不可用而显示N/A，这是正常的
   - 只要Agent执行成功，核心数据（如MVRV、RSI、Fed Rate等）应该能显示

2. **数据更新频率**
   - Agent数据更新频率 = 策略执行频率（16分钟）
   - 前端30秒轮询，但数据只在策略执行时更新

3. **用户隔离**
   - 每个用户只能看到自己的数据
   - Agent执行记录通过user_id隔离

## 后续优化建议

1. **添加数据可用性指示**
   - 区分"未执行"和"数据源不可用"
   - 显示数据最后更新时间

2. **优化查询性能**
   - 考虑添加索引：`(user_id, agent_name, executed_at)`
   - 考虑缓存最新执行记录

3. **添加调试信息**
   - 在API响应中添加调试字段（如查询到的记录数量）
   - 记录查询日志

## 修改的文件

1. `AMbackend/app/services/agents/execution_recorder.py`
   - 修改 `get_latest_executions` 方法

2. `AMbackend/app/api/v1/endpoints/exploration.py`
   - 修改 `get_squad_decision_core` 调用
   - 修改 `get_data_stream` 调用

