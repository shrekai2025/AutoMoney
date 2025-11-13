# 动量策略UI设计分析

## 共通部分 (可复用的组件)

### 1. 策略列表卡片 (StrategyMarketplace)
**共通元素**:
- ✅ 策略卡片布局
- ✅ 性能指标展示 (收益率、最大回撤、夏普比率)
- ✅ 风险等级标签
- ✅ 筛选和排序功能
- ✅ 角色权限控制(trader/admin)
- ✅ Launch按钮

**个性化需求**:
- 🔧 显示Regime Score范围
- 🔧 显示多币种支持标签(BTC/ETH/SOL)
- 🔧 15分钟执行频率标签
- 🔧 动量策略特有图标

### 2. 策略详情页 (StrategyDetails)
**共通元素**:
- ✅ 总体性能指标卡片
- ✅ 持仓展示
- ✅ 净值曲线图
- ✅ Agent Squad显示
- ✅ 策略参数展示
- ✅ 交易历史
- ✅ 执行历史

**个性化需求**:
- 🔧 Regime Score实时显示和历史曲线
- 🔧 多币种持仓分组展示
- 🔧 OCO订单状态展示(止损/止盈价格)
- 🔧 技术指标概览(EMA/RSI/MACD)
- 🔧 动量强度可视化

### 3. 执行详情模态框 (ExecutionDetailsModal)
**共通元素**:
- ✅ Agent分析结果展示
- ✅ 决策reasoning
- ✅ 执行时间线

**个性化需求**:
- 🔧 Regime Filter Agent结果(Regime Score详情)
- 🔧 TA Momentum Agent结果(技术指标分数)
- 🔧 OCO订单详情
- 🔧 多币种分析对比

---

## 个性化组件需求

### 1. RegimeScoreGauge (Regime分数仪表盘)
**位置**: StrategyDetails顶部  
**功能**:
- 半圆形仪表盘显示当前Regime Score (0-100)
- 颜色分区:
  - 0-20: 红色 (极度危险)
  - 20-40: 橙色 (危险)
  - 40-60: 黄色 (中性)
  - 60-80: 浅绿 (健康)
  - 80-100: 深绿 (极度健康)
- 显示推荐乘数 (0.3x-1.6x)

### 2. MultiAssetHoldings (多币种持仓展示)
**位置**: StrategyDetails持仓区  
**功能**:
- Tab切换: BTC | ETH | SOL | All
- 每个币种独立显示:
  - 持仓量
  - 入场价
  - 当前价
  - 未实现盈亏
  - OCO订单状态
    - 止损价 (红色标记)
    - 止盈价 (绿色标记)
  - 距离触发百分比

### 3. OCOOrderStatus (OCO订单状态卡片)
**位置**: 持仓详情内  
**布局**:
```
[止损价]  ←  [当前价]  →  [止盈价]
42950.00      43950.00      46100.00
   -2.3%         0%          +4.9%
   🔴          💎           🟢
```

### 4. TechnicalIndicatorsSummary (技术指标概览)
**位置**: StrategyDetails中部  
**功能**:
- 网格布局显示关键指标:
  - EMA排列 (多头/空头)
  - RSI值 (14周期)
  - MACD状态 (金叉/死叉)
  - ATR (波动率)
- 每个指标显示15m和60m两个时间框架

### 5. MomentumStrengthChart (动量强度图表)
**位置**: StrategyDetails性能图表下方  
**功能**:
- 折线图显示历史动量强度
- 双轴: 
  - 左轴: 动量强度 (0-1)
  - 右轴: Regime Score (0-100)
- 高亮交易时刻

### 6. MomentumAgentDetails (动量Agent详情)
**位置**: ExecutionDetailsModal  
**功能**:
- Regime Filter Agent输出:
  - Component Scores雷达图
  - Key Factors列表
  - Risk Assessment
- TA Momentum Agent输出:
  - 三个币种分析对比表
  - 技术评分条形图
  - Best Opportunity高亮

---

## UI组件树结构

```
StrategyMarketplace (共通,需小改)
├── StrategyCard (共通)
│   ├── 策略名称和描述
│   ├── 性能指标
│   ├── 风险标签
│   └── [新增] 多币种标签
│   └── [新增] Regime Score范围显示

StrategyDetails (共通,需扩展)
├── [新增] RegimeScoreGauge (顶部)
├── PerformanceMetrics (共通)
├── [新增] TechnicalIndicatorsSummary
├── NetValueChart (共通)
├── [新增] MomentumStrengthChart
├── [改造] MultiAssetHoldings
│   ├── AssetTab切换
│   └── [新增] OCOOrderStatus
├── AgentSquad (共通,需适配)
│   ├── [新增] RegimeFilterAgent徽章
│   └── [新增] TAMomentumAgent徽章
├── RecentActivity (共通)
├── StrategyParameters (共通)
└── TradeHistory (共通,需显示OCO信息)

ExecutionDetailsModal (共通,需扩展)
├── ExecutionHeader (共通)
├── [新增] MomentumAgentDetails
│   ├── RegimeAnalysisSection
│   └── TechnicalAnalysisSection
├── DecisionSummary (共通,需适配)
└── Timeline (共通)
```

---

## 数据结构扩展

### Strategy Card (Marketplace)
```typescript
interface MomentumStrategyCard extends StrategyCard {
  // 新增字段
  regime_score_range: {
    min: number;
    max: number;
    current: number;
  };
  supported_assets: string[];  // ["BTC", "ETH", "SOL"]
  momentum_strength: number;   // 0-1
}
```

### Strategy Detail
```typescript
interface MomentumStrategyDetail extends StrategyDetail {
  // 新增字段
  current_regime: {
    score: number;
    classification: string;
    recommended_multiplier: number;
    component_scores: Record<string, number>;
    key_factors: string[];
  };
  
  technical_indicators: {
    [asset: string]: {
      "15m": TechnicalIndicators;
      "60m": TechnicalIndicators;
    }
  };
  
  momentum_metrics: {
    overall_strength: number;
    market_trend: string;
    best_opportunity: {
      asset: string;
      signal: string;
      signal_strength: number;
    } | null;
  };
}
```

### Holding with OCO
```typescript
interface MomentumHolding extends Holding {
  // 新增OCO字段
  oco_order: {
    stop_loss_price: number;
    take_profit_price: number;
    entry_price: number;
    side: "LONG" | "SHORT";
    created_at: string;
  } | null;
  
  // OCO触发状态
  distance_to_stop_loss_pct: number;
  distance_to_take_profit_pct: number;
}
```

---

## 开发优先级

### P0 (核心功能,必须有)
1. ✅ 策略卡片显示多币种标签
2. ✅ RegimeScoreGauge组件
3. ✅ MultiAssetHoldings多币种持仓
4. ✅ OCOOrderStatus订单状态

### P1 (重要功能,提升体验)
5. ⚠️ TechnicalIndicatorsSummary技术指标
6. ⚠️ MomentumStrengthChart动量图表
7. ⚠️ MomentumAgentDetails详情

### P2 (优化功能,锦上添花)
8. ⚠️ 实时Regime Score更新动画
9. ⚠️ OCO触发预警提示
10. ⚠️ 技术指标趋势预测

---

## 设计规范

### 颜色方案
- **Regime Score**:
  - Dangerous (0-40): `#ef4444` (red)
  - Neutral (40-60): `#f59e0b` (amber)
  - Healthy (60-80): `#10b981` (emerald)
  - Very Healthy (80-100): `#22c55e` (green)

- **多币种标签**:
  - BTC: `#f7931a` (Bitcoin橙)
  - ETH: `#627eea` (Ethereum蓝)
  - SOL: `#14f195` (Solana绿)

- **OCO状态**:
  - 止损: `#ef4444` (红色)
  - 当前: `#8b5cf6` (紫色)
  - 止盈: `#22c55e` (绿色)

### 图标选择
- Regime Score: `<Activity />` (活动图标)
- 多币种: `<Coins />` (硬币图标)
- OCO订单: `<Shield />` (盾牌图标)
- 技术指标: `<BarChart3 />` (柱状图图标)
- 动量: `<TrendingUp />` / `<TrendingDown />`

---

## API端点需求

### 获取Regime实时数据
```
GET /api/v1/strategies/{strategy_id}/regime-current
Response: {
  regime_score: number,
  classification: string,
  recommended_multiplier: number,
  timestamp: string
}
```

### 获取技术指标
```
GET /api/v1/strategies/{strategy_id}/technical-indicators
Response: {
  assets: {
    BTC: { "15m": {...}, "60m": {...} },
    ETH: {...},
    SOL: {...}
  }
}
```

### 获取动量历史
```
GET /api/v1/strategies/{strategy_id}/momentum-history
Response: {
  data: [
    {timestamp, momentum_strength, regime_score},
    ...
  ]
}
```

---

## 实现步骤

### Step 1: 创建基础组件 (P0)
- [ ] `RegimeScoreGauge.tsx`
- [ ] `MultiAssetHoldings.tsx`
- [ ] `OCOOrderStatus.tsx`

### Step 2: 修改现有组件
- [ ] 扩展`StrategyCard` 添加多币种标签
- [ ] 扩展`StrategyDetails` 集成新组件
- [ ] 扩展`TradeHistoryModal` 显示OCO信息

### Step 3: 创建高级组件 (P1)
- [ ] `TechnicalIndicatorsSummary.tsx`
- [ ] `MomentumStrengthChart.tsx`
- [ ] `MomentumAgentDetails.tsx`

### Step 4: API集成
- [ ] 添加新的API调用函数
- [ ] 实现实时数据更新
- [ ] 错误处理和加载状态

### Step 5: 测试和优化
- [ ] 组件单元测试
- [ ] 响应式布局测试
- [ ] 性能优化

---

**文档版本**: v1.0  
**创建时间**: 2025-11-13  
**状态**: 设计完成,待实现

