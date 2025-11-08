# Agent重试机制 - 快速参考指南

## 🚀 配置参数

### 重试配置
```python
# app/services/strategy/real_agent_executor.py
MAX_RETRIES = 3        # 最多重试3次
AGENT_TIMEOUT = 300    # 5分钟超时（秒）
```

### 重试策略
- **指数退避**: 1秒 → 2秒 → 4秒
- **并行执行**: 3个Agent同时执行，各自独立重试
- **失败即停**: 任何Agent失败后，整个策略执行标记为失败

## 📦 数据结构

### StrategyExecution.error_details
```json
{
  "error_type": "agent_execution_failed",
  "failed_agent": "macro | ta | onchain | multiple",
  "error_message": "具体错误信息",
  "retry_count": 0-3
}
```

## 🔍 检查命令

### 1. 查看最近的执行状态
```sql
SELECT
    id,
    execution_time,
    status,
    conviction_score,
    signal,
    error_message,
    error_details
FROM strategy_executions
WHERE user_id = 1
ORDER BY execution_time DESC
LIMIT 10;
```

### 2. 查看失败的执行
```sql
SELECT
    execution_time,
    error_message,
    error_details->>'failed_agent' as failed_agent,
    error_details->>'retry_count' as retry_count
FROM strategy_executions
WHERE status = 'failed'
ORDER BY execution_time DESC;
```

### 3. 统计成功率
```sql
SELECT
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM strategy_executions
WHERE user_id = 1
GROUP BY status;
```

## 🧪 测试脚本

### 运行完整测试
```bash
# 全面debug
python debug_agent_retry.py

# 测试失败场景
python test_failure_scenario.py

# 测试重试机制
python test_agent_failure.py
```

### 手动触发策略执行
```bash
python manual_trigger_strategy.py
```

## 📊 API端点

### 获取策略详情（包含错误信息）
```
GET /api/v1/marketplace/strategies/{portfolio_id}
```

**响应示例（失败）**:
```json
{
  "recent_activities": [
    {
      "date": "2025-11-08T02:55:02Z",
      "status": "failed",
      "signal": "HOLD",
      "error_details": {
        "error_type": "agent_execution_failed",
        "failed_agent": "multiple",
        "error_message": "以下 Agent 执行失败: macro, ta, onchain",
        "retry_count": 0
      },
      "agent_contributions": null
    }
  ]
}
```

## 🛠️ 常见问题

### Q1: Agent一直失败怎么办？
**A**: 检查日志中的错误信息：
```bash
# 查看最近的失败执行
python -c "
import asyncio
from sqlalchemy import create_engine, select
from app.models.strategy_execution import StrategyExecution

# ... 查询失败记录
"
```

### Q2: 如何调整重试次数？
**A**: 修改 `app/services/strategy/real_agent_executor.py`:
```python
MAX_RETRIES = 5  # 改为5次
```

### Q3: 如何调整超时时间？
**A**: 修改 `app/services/strategy/real_agent_executor.py`:
```python
AGENT_TIMEOUT = 600  # 改为10分钟
```

### Q4: Conviction Summary显示的是失败执行的分数？
**A**: 不会。API已经过滤，只从成功的执行中获取：
```python
# app/services/strategy/marketplace_service.py:372
.where(StrategyExecution.status == "completed")
```

## 📝 监控检查清单

### 每日检查
- [ ] 查看失败执行数量
- [ ] 检查失败原因
- [ ] 确认重试是否生效

### 每周检查
- [ ] 统计成功率
- [ ] 分析失败模式
- [ ] 评估是否需要调整参数

## 🔧 调试技巧

### 1. 查看实时日志
```bash
tail -f logs/strategy_execution.log | grep "Agent.*执行失败"
```

### 2. 模拟Agent失败
```python
# 传入空market_data
await strategy_orchestrator.execute_strategy(
    db=db,
    user_id=1,
    portfolio_id="xxx",
    market_data={},  # 会导致所有Agent失败
)
```

### 3. 验证数据库迁移
```bash
cd AMbackend
venv/bin/alembic current
venv/bin/alembic history
```

## 📍 关键文件位置

### Backend
```
AMbackend/
├── app/
│   ├── models/
│   │   └── strategy_execution.py          # error_details字段
│   ├── services/
│   │   └── strategy/
│   │       ├── real_agent_executor.py     # 重试逻辑
│   │       ├── strategy_orchestrator.py   # 错误处理
│   │       └── marketplace_service.py     # API过滤
│   └── schemas/
│       └── strategy.py                    # RecentActivity schema
└── alembic/
    └── versions/
        └── 27d5a57729ac_*.py             # 迁移文件
```

### Frontend
```
AMfrontend/
└── src/
    ├── types/
    │   └── strategy.ts                    # ErrorDetails接口
    └── components/
        └── StrategyDetails.tsx            # 错误UI展示
```

## ⚡ 快速命令

```bash
# 查看最近失败
psql -d automoney -c "SELECT execution_time, error_details FROM strategy_executions WHERE status='failed' ORDER BY execution_time DESC LIMIT 5;"

# 运行测试
python debug_agent_retry.py

# 手动执行
python manual_trigger_strategy.py

# 查看迁移状态
cd AMbackend && venv/bin/alembic current
```

## 🎯 成功指标

- ✅ 重试成功率 > 80%
- ✅ 失败执行 < 5%
- ✅ 所有失败都有error_details
- ✅ Conviction Summary始终来自成功执行

---

**最后更新**: 2025-11-08
**版本**: 1.0
