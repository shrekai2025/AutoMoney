# 策略感知UI设计方案 - Recent Squad Actions

## 🎯 问题描述

当前`StrategyDetails`组件的"Recent Squad Actions"使用**统一格式**展示所有策略执行:
- 显示Agent名称(如"Macro Scout", "Momentum Scout")
- 显示Signal(BUY/SELL/HOLD)
- 显示Conviction Score

但不同策略有不同的特性:
- **旧策略**: 3个Agent(Macro/TA/OnChain) + Conviction Score
- **动量策略**: 2个Agent(Regime Filter/Momentum TA) + Regime Score + 多资产分析

---

## 📋 策略类型与特性对比

### 1. 旧策略 (Multi-Agent BTC Strategy)

**Agents**: 3个
- The Oracle (macro_agent)
- Momentum Scout (ta_agent)
- Data Warden (onchain_agent)

**核心指标**:
- `conviction_score`: 0-100 (整体信念分数)
- `signal`: BUY/SELL/HOLD
- `position_size`: 0-1 (仓位比例)

**UI重点**:
- 三个Agent的信号和置信度
- Conviction Score的变化趋势
- Agent共识度(多少Agent同意)

### 2. 动量策略 (H.I.M.E. Momentum Strategy)

**Agents**: 2个
- Regime Filter (regime_filter)
- Momentum TA (ta_momentum)

**核心指标**:
- `regime_score`: 0-100 (市场制度评分)
- `regime_classification`: DANGEROUS/NEUTRAL/HEALTHY/VERY_HEALTHY
- `best_opportunity`: {asset: BTC/ETH/SOL, signal: LONG/SHORT, strength: 0-1}
- `oco_order`: {stop_loss, take_profit, leverage}

**UI重点**:
- Regime Score的健康状态
- 多资产分析结果(BTC/ETH/SOL)
- 技术动量强度
- OCO订单的止损止盈

---

## 🎨 设计方案

### 方案A: 动态组件切换 (推荐)

根据`strategy_definition.name`或`strategy_definition.decision_agent_class`动态渲染不同组件:

```tsx
// StrategyDetails.tsx

// 判断策略类型
const getStrategyType = (strategy: StrategyDetail) => {
  if (strategy.strategy_definition_name?.includes('momentum')) {
    return 'momentum';
  }
  return 'multi-agent';
};

// Recent Squad Actions部分
<CardContent className="px-3 pb-3 pt-0">
  {getStrategyType(strategy) === 'momentum' ? (
    <MomentumSquadActions activities={strategy.recent_activities} />
  ) : (
    <MultiAgentSquadActions activities={strategy.recent_activities} />
  )}
</CardContent>
```

#### 旧策略展示 (MultiAgentSquadActions)

```tsx
// 当前已有的展示方式
<div className="space-y-1.5">
  {activities.map((activity, index) => (
    <div key={index} className="flex items-center justify-between p-2 rounded border">
      {/* Badge: Multi-Agent Squad */}
      <Badge>Multi-Agent Squad</Badge>
      
      {/* Signal: HOLD/BUY/SELL */}
      <Badge>{activity.signal}</Badge>
      
      {/* Agent Contributions */}
      {activity.agent_contributions.map(agent => (
        <div>
          <span>{agent.display_name}</span>
          <span>{agent.signal}</span> {/* BULLISH/BEARISH/NEUTRAL */}
          <span>{agent.confidence}%</span>
          <span>{agent.score}</span>
        </div>
      ))}
      
      {/* Conviction Score */}
      <div>
        <span>Conviction: {activity.conviction_score}</span>
        <span>Score: {activity.conviction_score > 0 ? '+' : ''}{activity.conviction_score}</span>
      </div>
    </div>
  ))}
</div>
```

#### 动量策略展示 (MomentumSquadActions)

```tsx
<div className="space-y-1.5">
  {activities.map((activity, index) => {
    // 从metadata中提取动量策略专属数据
    const regimeScore = activity.metadata?.regime_score;
    const regimeClassification = activity.metadata?.regime_classification;
    const taDecision = activity.metadata?.ta_decision;
    const ocoOrder = activity.metadata?.oco_order;
    
    return (
      <div key={index} className="flex flex-col p-3 rounded border bg-slate-800/30 border-slate-700/50 hover:border-purple-500/50">
        {/* Header: Badge + Time */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Badge className="bg-purple-500/20 text-purple-400">
              Momentum Strategy
            </Badge>
            <span className="text-xs text-slate-500">
              {new Date(activity.date).toLocaleString()}
            </span>
          </div>
          
          {/* Signal Badge */}
          <Badge className={
            activity.signal === 'LONG' 
              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
              : activity.signal === 'SHORT'
              ? 'bg-red-500/20 text-red-400 border-red-500/50'
              : 'bg-blue-500/20 text-blue-400 border-blue-500/50'
          }>
            {activity.signal}
          </Badge>
        </div>
        
        {/* Regime Score Gauge (简化版) */}
        {regimeScore !== undefined && (
          <div className="mb-2">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">Market Regime</span>
              <span className={`font-medium ${
                regimeScore >= 70 ? 'text-emerald-400' :
                regimeScore >= 50 ? 'text-blue-400' :
                regimeScore >= 30 ? 'text-amber-400' :
                'text-red-400'
              }`}>
                {regimeClassification || 'NEUTRAL'}
              </span>
            </div>
            <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all ${
                  regimeScore >= 70 ? 'bg-emerald-400' :
                  regimeScore >= 50 ? 'bg-blue-400' :
                  regimeScore >= 30 ? 'bg-amber-400' :
                  'bg-red-400'
                }`}
                style={{ width: `${regimeScore}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mt-0.5">
              <span>0</span>
              <span>{regimeScore.toFixed(0)}</span>
              <span>100</span>
            </div>
          </div>
        )}
        
        {/* TA Decision (多资产) */}
        {taDecision?.asset && (
          <div className="bg-slate-900/50 rounded px-2 py-1.5 mb-2">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="text-purple-400 font-medium">Target:</span>
                <span className="text-white font-bold">{taDecision.asset}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Strength:</span>
                <span className="text-emerald-400 font-medium">
                  {(taDecision.signal_strength * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        )}
        
        {/* OCO Order Details */}
        {ocoOrder && (
          <div className="grid grid-cols-3 gap-1.5 text-xs">
            <div className="bg-red-500/10 border border-red-500/30 rounded px-2 py-1">
              <div className="text-red-400 font-medium">SL</div>
              <div className="text-white">${ocoOrder.stop_loss_price?.toFixed(2)}</div>
            </div>
            <div className="bg-slate-700/30 border border-slate-600/30 rounded px-2 py-1">
              <div className="text-slate-400 font-medium">Entry</div>
              <div className="text-white">${ocoOrder.entry_price?.toFixed(2)}</div>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded px-2 py-1">
              <div className="text-emerald-400 font-medium">TP</div>
              <div className="text-white">${ocoOrder.take_profit_price?.toFixed(2)}</div>
            </div>
          </div>
        )}
        
        {/* Agent Contributions */}
        <div className="mt-2 pt-2 border-t border-slate-700/30 space-y-1">
          {activity.agent_contributions?.map((agent, idx) => (
            <div key={idx} className="flex items-center justify-between text-xs">
              <span className={`font-medium ${
                agent.agent_name === 'regime_filter' ? 'text-blue-400' : 'text-purple-400'
              }`}>
                {agent.display_name}
              </span>
              <div className="flex items-center gap-2">
                {agent.agent_name === 'regime_filter' && agent.score !== undefined && (
                  <span className="text-slate-300">
                    Score: <span className="text-white font-medium">{agent.score.toFixed(1)}</span>
                  </span>
                )}
                <span className="text-slate-400">
                  Confidence: <span className="text-white">{agent.confidence}%</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  })}
</div>
```

---

## 🔧 实现步骤

### Step 1: 创建策略特定组件

```tsx
// AMfrontend/src/components/strategy/MultiAgentSquadActions.tsx
export function MultiAgentSquadActions({ activities }: { activities: any[] }) {
  // 当前已有的渲染逻辑
  return (...)
}

// AMfrontend/src/components/strategy/MomentumSquadActions.tsx
export function MomentumSquadActions({ activities }: { activities: any[] }) {
  // 动量策略专属渲染逻辑
  return (...)
}
```

### Step 2: 在StrategyDetails中动态切换

```tsx
// AMfrontend/src/components/StrategyDetails.tsx

import { MultiAgentSquadActions } from './strategy/MultiAgentSquadActions';
import { MomentumSquadActions } from './strategy/MomentumSquadActions';

// 在Recent Squad Actions部分
<CardContent className="px-3 pb-3 pt-0">
  {(() => {
    // 判断策略类型
    const strategyType = strategy.strategy_definition_name?.includes('momentum') 
      ? 'momentum' 
      : 'multi-agent';
    
    switch (strategyType) {
      case 'momentum':
        return <MomentumSquadActions activities={strategy.recent_activities} />;
      case 'multi-agent':
      default:
        return <MultiAgentSquadActions activities={strategy.recent_activities} />;
    }
  })()}
</CardContent>
```

### Step 3: 确保后端metadata完整

后端需要在`recent_activities`的`metadata`中包含策略特定数据:

```python
# AMbackend/app/services/strategy/marketplace_service.py

# 旧策略
activity = {
    "agent": "Multi-Agent Squad",
    "signal": execution.signal,
    "date": execution.execution_time,
    "conviction_score": execution.conviction_score,
    "agent_contributions": [...],  # 3个Agent
    "metadata": {
        # 旧策略没有额外metadata
    }
}

# 动量策略
activity = {
    "agent": "Momentum Strategy",
    "signal": execution.signal,  # LONG/SHORT/HOLD
    "date": execution.execution_time,
    "conviction_score": execution.conviction_score,
    "agent_contributions": [...],  # 2个Agent
    "metadata": {
        "regime_score": 65.0,
        "regime_classification": "HEALTHY",
        "ta_decision": {
            "asset": "BTC",
            "signal_strength": 0.75,
            "trend": "UPTREND"
        },
        "oco_order": {
            "entry_price": 43000.0,
            "stop_loss_price": 42000.0,
            "take_profit_price": 45000.0,
            "leverage": 3.0
        }
    }
}
```

---

## 🎨 UI对比效果

### 旧策略展示
```
┌─────────────────────────────────────────┐
│ [Multi-Agent Squad]         HOLD        │
│ 11/13/2025, 09:31 PM                    │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ The Oracle      NEUTRAL  55%  +15.0│  │
│ │ Momentum Scout  NEUTRAL  62%  +15.0│  │
│ │ Data Warden     NEUTRAL  72%  +15.0│  │
│ └────────────────────────────────────┘  │
│                                          │
│ Conviction: 55%  Score: +15.0           │
└─────────────────────────────────────────┘
```

### 动量策略展示
```
┌─────────────────────────────────────────┐
│ [Momentum Strategy]         LONG        │
│ 11/13/2025, 09:31 PM                    │
│                                          │
│ Market Regime: HEALTHY                  │
│ ████████████████████░░░░░░░ 65          │
│ 0                          50        100 │
│                                          │
│ Target: BTC    Strength: 75%            │
│                                          │
│ ┌──────┐  ┌──────┐  ┌──────┐           │
│ │  SL  │  │Entry │  │  TP  │           │
│ │$42000│  │$43000│  │$45000│           │
│ └──────┘  └──────┘  └──────┘           │
│                                          │
│ ─────────────────────────────────       │
│ Regime Filter    Score: 65.0  Conf: 72%│
│ Momentum TA                   Conf: 80%│
└─────────────────────────────────────────┘
```

---

## ✅ 优势

1. **用户体验优化**
   - 每个策略展示最相关的信息
   - 避免信息过载
   - 视觉上更清晰

2. **可扩展性**
   - 新增策略只需添加新组件
   - 不影响现有策略展示

3. **信息密度**
   - 动量策略展示Regime Score + OCO订单
   - 旧策略展示3个Agent共识

4. **视觉差异化**
   - 不同策略有不同的颜色主题
   - 更容易区分策略类型

---

## 🚀 下一步

是否需要我实现这个方案?我可以:
1. 创建`MomentumSquadActions.tsx`组件
2. 重构现有代码到`MultiAgentSquadActions.tsx`
3. 更新`StrategyDetails.tsx`支持动态切换
4. 确保后端metadata包含必要数据

请告诉我是否继续实现! 🎯

