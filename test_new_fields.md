# 新功能测试报告

## 测试时间
2025-11-13

## 实现的功能

### 1. ✅ 策略模板添加"策略说明"字段 (philosophy)

**数据库字段**: `strategy_definitions.philosophy` (TEXT类型)

**验证方式**:
```sql
SELECT id, display_name, LEFT(philosophy, 100) as philosophy_preview
FROM strategy_definitions;
```

**结果**: ✅ 字段已添加，现有模板已更新

---

### 2. ✅ 策略实例添加"策略标签"字段 (tags)

**数据库字段**: `portfolios.tags` (JSONB类型，数组)

**前端UI**: Launch Strategy Modal 中的 "Strategy Tags" 输入框
- 支持手动输入标签
- 按Enter或点击Add按钮添加
- 可删除已添加的标签
- 标签以紫色徽章显示

**API请求示例**:
```json
{
  "strategy_definition_id": 1,
  "instance_name": "Test Strategy",
  "initial_balance": 1000,
  "tags": ["Macro-Driven", "BTC/ETH", "Low-Medium Risk"],
  "risk_level": "medium"
}
```

---

### 3. ✅ 策略实例添加"风险程度"字段 (risk_level)

**数据库字段**: `portfolios.risk_level` (VARCHAR(20)，默认值 'medium')

**前端UI**: Launch Strategy Modal 中的 "Risk Level" 下拉选择框
- Low Risk (绿色指示器)
- Medium Risk (黄色指示器，默认)
- High Risk (红色指示器)

---

## 数据流

```
前端输入
  ↓
LaunchStrategyModal
  ├─ tags: string[]
  ├─ risk_level: "low" | "medium" | "high"
  ↓
API: POST /api/v1/strategies/
  ↓
CreateInstanceRequest (Pydantic模型)
  ├─ tags?: List[str]
  ├─ risk_level?: str
  ↓
definition_service.create_instance_from_definition()
  ↓
Portfolio模型
  ├─ tags: JSONB = []
  ├─ risk_level: VARCHAR = "medium"
  ↓
数据库 portfolios表
```

---

## 测试步骤

### 前端测试

1. **打开前端页面**
   ```
   http://localhost:5173
   ```

2. **点击 "Launch Strategy" 按钮**

3. **填写表单**:
   - Strategy Template: 选择 "Multi-Agent BTC Strategy"
   - Instance Name: 输入自定义名称（可选）
   - Description: 输入描述（可选）
   - Initial Balance: 输入金额，如 1000
   - **Strategy Tags**:
     - 输入 "Macro-Driven"，按Enter
     - 输入 "BTC Focus"，按Enter
     - 输入 "Conservative"，点击Add
   - **Risk Level**: 选择 "Low" 或 "High"

4. **点击 "Launch Instance"**

5. **验证结果**:
   - 查看toast提示创建成功
   - 页面应该刷新显示新实例

### 后端测试

```bash
# 验证数据库中的新字段
psql -h localhost -U uniteyoo -d automoney -c "
SELECT
  id,
  instance_name,
  tags,
  risk_level,
  created_at
FROM portfolios
ORDER BY created_at DESC
LIMIT 5;
"
```

**期望输出**:
```
 id | instance_name | tags | risk_level | created_at
----+---------------+------+------------+------------
 xxx | Test Strategy | ["Macro-Driven", "BTC Focus", "Conservative"] | low | 2025-11-13 ...
```

---

## API测试

### 使用curl测试创建实例

```bash
# 1. 获取JWT token (假设已登录)
TOKEN="your_jwt_token_here"

# 2. 创建策略实例
curl -X POST http://localhost:8000/api/v1/strategies/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "strategy_definition_id": 1,
    "instance_name": "API Test Strategy",
    "instance_description": "Testing new fields",
    "initial_balance": 1000,
    "tags": ["API-Test", "Macro-Driven", "Low Risk"],
    "risk_level": "low"
  }'
```

**期望响应**:
```json
{
  "success": true,
  "portfolio_id": "uuid-here",
  "instance_name": "API Test Strategy",
  "strategy_definition_id": 1,
  "initial_balance": 1000.0,
  "created_at": "2025-11-13T..."
}
```

---

## 文件修改清单

### 后端 (AMbackend)

1. **数据库迁移**
   - `alembic/versions/c52c75ab840f_add_philosophy_tags_risk_level_fields.py` - 新建

2. **模型**
   - `app/models/strategy_definition.py:32` - 添加 `philosophy` 字段
   - `app/models/portfolio.py:27-28` - 添加 `tags` 和 `risk_level` 字段

3. **服务层**
   - `app/services/strategy/definition_service.py:164-195` - 更新函数签名和文档
   - `app/services/strategy/definition_service.py:230-231` - 创建实例时设置新字段

4. **API层**
   - `app/api/v1/endpoints/strategy_instances.py:25-33` - 更新请求模型
   - `app/api/v1/endpoints/strategy_instances.py:143-144` - 传递新参数

### 前端 (AMfrontend)

1. **API类型**
   - `src/lib/strategyInstanceApi.ts:30-31` - 添加 `tags` 和 `risk_level` 到请求接口

2. **UI组件**
   - `src/components/LaunchStrategyModal.tsx:25` - 导入 X 图标
   - `src/components/LaunchStrategyModal.tsx:53-55` - 添加状态变量
   - `src/components/LaunchStrategyModal.tsx:115-116` - 传递新字段到API
   - `src/components/LaunchStrategyModal.tsx:128-130` - 重置表单时清空新字段
   - `src/components/LaunchStrategyModal.tsx:287-385` - 添加标签和风险等级UI

---

## 截图中字段说明总结

| 字段 | 含义 | 计算方式 |
|------|------|---------|
| **BTCUSDT** | 持仓币种 | 数据库: `holdings.symbol` |
| **0.00667408** | BTC数量 | 数据库: `holdings.amount` |
| **$-18.80** | 未实现盈亏 | 计算: `market_value - cost_basis` = $681.20 - $699.99 |
| **Avg Buy $104,885.48** | 平均买入价 | 数据库: `holdings.avg_buy_price` |
| **Current $102,066.06** | 当前实时价格 | Binance WebSocket实时获取 |
| **Value $681.20** | 当前市场价值 | 计算: `amount × current_price` |
| **P&L % -2.69%** | 盈亏百分比 | 计算: `(current_price - avg_buy_price) / avg_buy_price × 100%` |

---

## 下一步建议

### 1. 在策略详情页展示新字段

**位置**: StrategyDetails.tsx

**需要展示**:
- `tags`: 在策略卡片上方显示标签徽章
- `risk_level`: 在策略参数区显示风险等级（带颜色指示器）

### 2. 在Admin面板支持编辑这些字段

**位置**: AdminPanel.tsx -> Strategy Instances

**功能**:
- 允许管理员修改实例的标签
- 允许管理员修改实例的风险等级

### 3. 使用philosophy字段

**当前状态**: philosophy已存储在数据库，但marketplace_service.py仍使用硬编码的STRATEGY_PHILOSOPHY

**建议**: 修改marketplace_service.py，从数据库读取philosophy而不是使用固定模板

---

## 测试结果

- ✅ 数据库迁移成功
- ✅ 模型字段已添加
- ✅ 后端API已更新
- ✅ 前端UI已实现
- ⏳ 等待用户前端测试

---

**测试完成时间**: 2025-11-13
**实现人**: Claude Code
