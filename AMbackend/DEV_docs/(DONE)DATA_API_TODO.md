# 数据API对接TODO

## 对接优先级和步骤

### ✅ 优先级1: Alternative.me Fear & Greed Index

**为什么优先：**
- 免费，无需API key
- 单一端点，最简单
- 不需要注册
- 对Agent决策很重要（情绪指标）

**API信息：**
- 端点: `https://api.alternative.me/fng/`
- 文档: https://alternative.me/crypto/fear-and-greed-index/
- 返回格式:
  ```json
  {
    "name": "Fear and Greed Index",
    "data": [{
      "value": "74",
      "value_classification": "Greed",
      "timestamp": "1609459200"
    }]
  }
  ```

**需要修改的文件：**
- `app/services/data_collectors/alternative_me.py` (第37-67行)

**工作量：** 10分钟

---

### ✅ 优先级2: Binance公开API

**为什么优先：**
- 免费
- 公开数据无需API key
- 文档完善，稳定性好
- 提供核心的价格和K线数据

**需要的API端点：**

1. **24小时价格行情**
   - 端点: `https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT`
   - 文档: https://binance-docs.github.io/apidocs/spot/en/#24hr-ticker-price-change-statistics
   - 返回字段: price, volume, priceChangePercent, high, low

2. **K线数据（蜡烛图）**
   - 端点: `https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=200`
   - 文档: https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data
   - 返回格式: `[timestamp, open, high, low, close, volume, ...]`

**需要修改的文件：**
- `app/services/data_collectors/binance.py` (第33-109行)

**注意事项：**
- 公开API有速率限制：1200请求/分钟
- 无需API key和secret（使用空字符串）
- 可以直接使用httpx调用

**工作量：** 20分钟

---

### ⏳ 优先级3: FRED API（宏观经济数据）

**为什么重要：**
- 权威的美国经济数据源
- MacroAgent必需
- 免费但需要注册

**注册步骤：**
1. 访问: https://fred.stlouisfed.org/
2. 点击 "My Account" → "API Keys"
3. 创建新的API key（免费，即时生效）
4. 复制API key到 `.env` 文件

**需要的数据序列：**

| 数据 | Series ID | 说明 |
|------|-----------|------|
| M2货币供应 | M2SL | 美国M2货币存量 |
| 美元指数 | DTWEXBGS | DXY美元指数 |
| 联邦基金利率 | DFF | Fed利率 |
| 10年期国债收益率 | DGS10 | 长期利率指标 |

**API端点格式：**
```
https://api.stlouisfed.org/fred/series/observations
  ?series_id=M2SL
  &api_key=YOUR_API_KEY
  &file_type=json
  &sort_order=desc
  &limit=1
```

**需要修改的文件：**
- `app/services/data_collectors/fred.py` (第33-95行)
- `.env` 添加 `FRED_API_KEY=你的密钥`

**文档：**
- 官方文档: https://fred.stlouisfed.org/docs/api/fred/
- API限制: 每天120,000请求

**工作量：** 30分钟（含注册）

---

### ✅ 优先级4: 链上数据 (已完成免费方案)

**现状：** ✅ 已使用免费API完全替代Glassnode付费服务

**Glassnode付费方案（已决定不使用）：**
- Starter: $29/月（基础指标）
- Advanced: $149/月（完整指标）
- Professional: $799/月（实时数据）

**✅ 已实现的免费替代方案：**

1. **Blockchain.info API** ✅ 已实现
   - 端点: `https://api.blockchain.info/`
   - 免费，无需注册
   - 文件: `app/services/data_collectors/blockchain_info.py`
   - 提供数据:
     - 网络统计 (hash rate, difficulty, block height)
     - 活跃地址数 (24h)
     - 交易量 (30天平均)
     - 市值数据

2. **Mempool.space API** ✅ 已实现
   - 端点: `https://mempool.space/api`
   - 免费，无需注册
   - 文件: `app/services/data_collectors/mempool_space.py`
   - 提供数据:
     - 推荐交易费用 (sat/vB)
     - Mempool状态 (TX数量、大小)
     - 区块高度
     - 难度调整预测

**OnChainAgent状态：** ✅ 已完成
- 文件: `app/agents/onchain_agent.py`
- 使用免费API提供完整链上分析
- 计算简化NVT比率
- 网络健康度评估 (HEALTHY/MODERATE/CONGESTED)
- 已集成到Research Workflow

**工作量：** ✅ 已完成 (实际用时: 约90分钟，含测试和调试)

---

## 对接时间表

### 第1天（今天）✅ 已完成
- [x] 后端服务启动
- [x] 前端集成文档
- [x] Alternative.me API对接（10分钟）
- [x] Binance公开API对接（20分钟）
- [x] 测试数据采集功能
- [x] 创建市场数据API端点
- [x] 实现HTTP客户端和缓存机制

### 第2天 ✅ 已完成
- [x] 注册FRED API key
- [x] FRED API对接（30分钟）
- [x] 完整测试所有数据源
- [x] 创建/api/v1/market/macro端点

### 第3天 ✅ 已完成
- [x] 删除所有Mock数据降级逻辑
- [x] 确保API错误正确暴露
- [x] 禁用Glassnode（需付费订阅）
- [x] 创建真实数据测试套件

### 第4天 ✅ 已完成 (2025-11-06)
- [x] 实现Blockchain.info API对接（40分钟）
- [x] 实现Mempool.space API对接（30分钟）
- [x] 创建OnChainAgent并集成（60分钟）
- [x] 完整测试链上数据采集和分析
- [x] 修复OnChainAgent代码问题（5个关键bug）
- [x] 集成到Research Workflow

---

## 对接检查清单

### Alternative.me ✅ 已完成
- [x] 修改 `alternative_me.py` 使用真实API
- [x] 测试数据获取
- [x] 验证数据格式
- [x] 确认缓存工作正常

### Binance ✅ 已完成
- [x] 修改 `binance.py` 价格API
- [x] 修改 `binance.py` K线API
- [x] 测试BTC和ETH数据
- [x] 验证OHLCV格式正确
- [x] 确认技术指标计算正常

### FRED ✅ 已完成
- [x] 注册并获取API key
- [x] 更新 `.env` 配置
- [x] 修改 `fred.py` 实现
- [x] 测试M2, DXY, Fed利率数据
- [x] 验证数据采集正常

### OnChain数据 ✅ 已完成
- [x] 创建 `blockchain_info.py` 采集器
- [x] 创建 `mempool_space.py` 采集器
- [x] 测试网络统计、活跃地址、交易量数据
- [x] 测试交易费用、Mempool状态数据
- [x] 创建OnChainAgent并集成LLM分析
- [x] 实现简化NVT比率计算
- [x] 验证网络健康度评估
- [x] 修复5个代码问题（f-string语法等）
- [x] 集成到Research Workflow

### Glassnode ✅ 已完成
- [x] 评估是否需要付费订阅（决定不订阅）
- [x] 删除Mock数据
- [x] 实现NotImplementedError提示
- [x] 标记为可选数据源
- [x] 使用免费API完全替代（Blockchain.info + Mempool.space）

---

## API速率限制总结

| 数据源 | 免费限制 | 是否需要Key |
|--------|----------|-------------|
| Alternative.me | 无明确限制 | ❌ 不需要 |
| Binance | 1200次/分钟 | ❌ 不需要 |
| FRED | 120,000次/天 | ✅ 需要 |
| Blockchain.info | 无明确限制 | ❌ 不需要 |
| Mempool.space | 无明确限制 | ❌ 不需要 |
| Glassnode | N/A（付费，已禁用） | ✅ 需要 |

---

## 测试命令

对接完成后，使用以下命令测试：

```bash
# 测试数据采集
python test_data_collection.py

# 测试技术指标（含真实数据）
python test_ta_integration.py

# 查看采集器状态
curl http://localhost:8000/api/v1/data/status
```

---

## 注意事项

1. **API密钥安全**
   - 不要提交 `.env` 文件到git
   - 使用环境变量管理密钥
   - 定期轮换API密钥

2. **🚫 严禁使用Mock数据（项目核心原则）**
   - ❌ **禁止**在生产代码中使用任何Mock数据
   - ❌ **禁止**API失败时降级到Mock数据
   - ✅ **必须**使用真实API进行开发和测试
   - ✅ **必须**让API错误正确暴露，不被Mock掩盖
   - ✅ **必须**在API不可用时直接返回错误，而不是返回假数据
   - **原因**: Mock数据会掩盖真实问题，导致上线后才发现bug，严重影响系统可靠性

3. **错误处理**
   - 所有API调用都有超时设置
   - 失败时使用缓存数据（如果有且未过期）
   - 缓存也失败时，返回错误给前端，**不使用Mock数据**
   - 记录错误日志便于调试

4. **缓存策略**
   - 价格数据：1分钟缓存
   - 链上数据：5分钟缓存
   - 宏观数据：1小时缓存
   - 恐惧贪婪：10分钟缓存

5. **成本控制**
   - 使用缓存减少API调用
   - 避免过于频繁的请求
   - 监控API使用量

---

## 联系方式

如果对接过程中遇到问题：
1. 查看具体数据源的官方文档
2. 检查 `.env` 配置是否正确
3. 查看后端日志了解错误信息
4. 测试API端点是否可访问

---

## 集成总结

### 已完成的数据源 ✅
1. **Alternative.me Fear & Greed Index** - 加密货币市场情绪指标
2. **Binance Market Data** - BTC/ETH价格、OHLCV蜡烛图数据
3. **FRED Macroeconomic Data** - 联邦基金利率、M2货币供应、DXY美元指数、10年期国债

### 可用的API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/market/snapshot` | GET | 完整市场数据快照 |
| `/api/v1/market/fear-greed` | GET | 恐惧贪婪指数 |
| `/api/v1/market/prices` | GET | BTC和ETH当前价格 |
| `/api/v1/market/ohlcv` | GET | OHLCV蜡烛图数据 |
| `/api/v1/market/macro` | GET | 宏观经济数据 |
| `/api/v1/market/indicators` | GET | 技术指标 |
| `/api/v1/market/status` | GET | 数据采集器状态 |
| `/api/v1/market/cache/clear` | POST | 清除所有缓存 |

### 测试结果（2025-11-05）

```bash
# 所有API测试通过（真实数据）
alternative_me      : ✓ PASSED (Value: 23, Extreme Fear)
binance             : ✓ PASSED (BTC: $101,390, ETH: $3,279)
fred                : ✓ PASSED (Fed Rate: 3.87%, M2: +0.47%, DXY: 121.77)

Total: 3/3 APIs working

# Mock数据移除测试通过
✓ Alternative.me real data
✓ Binance real data
✓ FRED real data
✓ Binance error handling (no mock fallback)
✓ Glassnode disabled (requires subscription)
✓ FRED error handling (no mock fallback)

✅ 所有采集器仅使用真实数据（无Mock降级）
✅ 错误正确暴露（不被Mock数据掩盖）
```

---

## ✅ 数据集成阶段完成总结

### 已完成的工作
1. ✅ Alternative.me Fear & Greed Index API集成
2. ✅ Binance市场数据API集成（价格 + OHLCV）
3. ✅ FRED宏观经济数据API集成
4. ✅ 删除所有Mock数据降级逻辑
5. ✅ 实现完整的错误处理和暴露
6. ✅ 创建8个RESTful API端点
7. ✅ 实现缓存机制（1分钟-1小时）
8. ✅ 完整测试套件

### 数据源状态
- ✅ **Alternative.me**: 实时数据，10分钟缓存
- ✅ **Binance**: 实时数据，1-5分钟缓存
- ✅ **FRED**: 实时数据，1小时缓存
- ⏸️ **Glassnode**: 已禁用（需付费$29-799/月）

---

## 🚀 下一阶段：Agent系统开发

数据采集层已完成，现在可以开始开发核心的AI Agent系统。

### ✅ MacroAgent开发 (已完成 - 2025-11-05)

**成果:**
1. ✅ 创建MacroAgent基类 (`app/agents/macro_agent.py`)
2. ✅ 定义Agent schemas (`app/schemas/agents.py`)
   - SignalType (BULLISH/BEARISH/NEUTRAL)
   - MacroAnalysisOutput
   - ConfidenceLevel评分系统
3. ✅ 集成Tuzi Claude 4.5 Thinking模型
   - 更新Tuzi Provider支持Claude Messages API
   - 配置Claude Sonnet 4.5 Thinking All模型
   - Base URL: https://api.tu-zi.com
4. ✅ 实现宏观经济分析逻辑
   - 分析Federal Funds Rate、M2 Growth、DXY、Fear & Greed
   - 结构化输出macro_indicators
   - 风险评估和关键因素识别
5. ✅ 测试验证 (`test_macro_agent.py`)
   - 成功获取实时市场数据
   - LLM分析返回详细推理
   - 置信度评分和风险评估

**测试结果示例:**
```
Signal: BEARISH
Confidence: 72% (HIGH)
Key Factors:
  - Exceptionally strong US Dollar (DXY at 121.77)
  - Stagnant M2 growth (0.47%)
  - Extreme Fear sentiment (23/100)
```

### 🔄 PlanningAgent & GeneralAnalysisAgent ✅ (已完成 - 2025-11-06)

**成果:**
1. ✅ 创建PlanningAgent (`app/agents/planning_agent.py`)
   - 使用Claude Sonnet 4.5 Thinking进行任务分解
   - 动态选择业务Agent（从agent_registry获取可用Agent）
   - 规划并行/串行执行策略
   - 输出PlanningAgentOutput结构化计划

2. ✅ 创建GeneralAnalysisAgent (`app/agents/general_analysis_agent.py`)
   - 综合所有Agent分析结果
   - 使用Claude Sonnet 4.5 Thinking进行决策综合
   - 生成最终用户可读答案
   - 输出GeneralAnalysisOutput结构化结果

3. ✅ 创建SuperAgent (`app/agents/super_agent.py`)
   - 问题路由：简单问题直接回答，复杂问题路由到PlanningAgent
   - 使用OpenRouter GPT-4o-mini（高效决策）
   - 输出SuperAgentOutput路由决策

4. ✅ 创建Agent Registry (`app/agents/registry.py`)
   - 动态注册和发现Agent
   - 为PlanningAgent提供可用Agent列表
   - 支持Agent可用性检查

5. ✅ 实现Research Workflow (`app/workflows/research_workflow.py`)
   - 完整的多Agent协作流程
   - Server-Sent Events (SSE) 实时流式输出
   - 5步骤工作流：SuperAgent路由 → PlanningAgent规划 → 数据收集 → 并行Agent分析 → GeneralAnalysisAgent综合

6. ✅ 创建Research Chat API (`app/api/v1/endpoints/research.py`)
   - `POST /api/v1/research/chat` - SSE流式研究问答
   - `GET /api/v1/research/available-agents` - 获取可用Agent列表
   - 支持chat_history上下文

7. ✅ Bug修复：
   - 修复PlanningAgent prompt中的KeyError（转义大括号）
   - 修复GeneralAnalysisAgent JSON解析问题（字符串中的换行符转义）
   - 重写`json_parser.py`的`fix_common_json_issues`函数

**工作流程:**
```
用户提问
→ SuperAgent（路由决策）
  ├─ DIRECT_ANSWER：直接回答
  └─ ROUTE_TO_PLANNING：复杂分析
      → PlanningAgent（任务规划）
      → DataManager（收集市场数据）
      → 并行执行 Business Agents (MacroAgent等)
      → GeneralAnalysisAgent（综合分析）
      → 最终答案
```

**测试结果:**
```bash
python -c "
from app.workflows.research_workflow import research_workflow
async for event in research_workflow.process_question('现在适合买BTC吗？'):
    print(event['type'])
"
# ✅ status (任务识别)
# ✅ status (规划分析)
# ✅ planning_result (计划生成)
# ✅ status (收集数据)
# ✅ data_collected (数据收集完成)
# ✅ status (执行分析)
# ✅ agent_result (MacroAgent分析完成)
# ✅ status (整合结果)
# ✅ final_answer (最终答案)
```

### ✅ OnChainAgent代码检查与修复 (2025-11-06 晚)

**执行内容:**
全面代码检查，发现并修复5个关键问题

**修复清单:**
1. ✅ **严重语法错误** - f-string第85行三元运算符格式错误
   ```python
   # ❌ 错误
   {active_addresses:,} if active_addresses else "N/A"
   # ✅ 修复
   {f"{active_addresses:,}" if active_addresses else "N/A"}
   ```

2. ✅ **导入错误** - 移除不存在的`Agent`基类继承
   - 其他Agent都没有继承基类，保持一致性

3. ✅ **LLM集成错误** - 修正LLM调用方式
   - 从`app.core.llm.get_llm_client()` 改为 `llm_manager.chat_for_agent()`

4. ✅ **Schema不完整** - 添加confidence_level自动计算
   - 确保LLM返回的confidence自动转换为confidence_level enum

5. ✅ **Workflow集成** - 修复user_query传递
   - `_execute_business_agents`和`_run_agent`增加user_message参数
   - OnChainAgent可获知用户真实问题，提供更有针对性的分析

**测试验证:**
```bash
$ python test_onchain_fixes.py

[1] ✅ Agent instantiated successfully (no syntax errors)
[2] ✅ Data collection successful + Data structure correct
[3] ✅ Prompt contains user query + Active addresses formatted correctly
[4] ✅ Workflow integration correct (user_message parameter passing)

🎉 All tests passed! OnChainAgent is ready.
```

**新增文件:**
- `ONCHAIN_AGENT_FIXES.md` - 完整修复记录文档
- `test_onchain_fixes.py` - 代码检查验证测试套件

**结论:**
✅ OnChainAgent代码质量达到生产标准，可正式投入使用

---

### 🔄 下一步: TAAgent优化

继续完善TAAgent以完善多Agent系统。

**优先级:**
1. **TAAgent (Technical Analysis Agent)** - P0
   - 技术分析：RSI, MACD, EMA, Bollinger Bands
   - 依赖已完成的技术指标计算器
   - 类似MacroAgent的实现模式
   - **建议**: 进行类似的代码检查，确保代码质量

**已完成的Business Agent:**
- ✅ MacroAgent - 宏观经济分析
- ✅ TAAgent - 技术分析
- ✅ OnChainAgent - 链上数据分析（已验证代码质量）

---

最后更新: 2025-11-06 晚
