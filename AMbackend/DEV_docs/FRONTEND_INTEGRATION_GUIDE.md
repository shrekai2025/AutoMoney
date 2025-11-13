# 前端集成指南 - Strategy Marketplace API

> **更新时间**: 2025-11-06 18:30
> **状态**: 准备就绪
> **后端API**: 全部测试通过

## 🎯 集成概述

本指南提供详细的前端代码示例，帮助你快速将Strategy Marketplace和Strategy Details页面接入真实后端API。

---

## 📡 API端点

### Base URL
```
http://localhost:8000/api/v1
```

### 可用端点
1. `GET /marketplace` - 获取策略列表
2. `GET /marketplace/{id}` - 获取策略详情
3. `POST /marketplace/{id}/deploy` - 部署资金 (占位)
4. `POST /marketplace/{id}/withdraw` - 提现资金 (占位)

---

## 🔧 1. StrategyMarketplace.tsx 集成

### Step 1: 更新TypeScript接口

```typescript
// src/types/strategy.ts
export interface StrategyCard {
  id: string;                    // ⚠️ 改为 string (UUID)
  name: string;
  subtitle: string;
  description: string;
  tags: string[];
  annualized_return: number;     // ⚠️ 使用 snake_case
  max_drawdown: number;
  sharpe_ratio: number;
  pool_size: number;             // ⚠️ 改为 pool_size (不是tvl)
  squad_size: number;
  risk_level: string;
  history: Array<{               // ⚠️ 包含 date 字段
    date: string;
    value: number;
  }>;
}

export interface MarketplaceResponse {
  strategies: StrategyCard[];
}
```

### Step 2: 创建API调用函数

```typescript
// src/services/marketplaceApi.ts
import { MarketplaceResponse } from '../types/strategy';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

export async function fetchMarketplaceStrategies(
  sortBy: string = 'return',
  riskLevel?: string
): Promise<MarketplaceResponse> {
  const params = new URLSearchParams({
    sort_by: sortBy,
  });

  if (riskLevel) {
    params.append('risk_level', riskLevel);
  }

  const response = await fetch(`${API_BASE_URL}/marketplace?${params}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch strategies: ${response.statusText}`);
  }

  return response.json();
}
```

### Step 3: 替换Mock数据

```typescript
// src/components/StrategyMarketplace.tsx
import { useState, useEffect } from "react";
import { fetchMarketplaceStrategies } from "../services/marketplaceApi";
import type { StrategyCard } from "../types/strategy";

export function StrategyMarketplace({ onSelectStrategy }: StrategyMarketplaceProps) {
  const [strategies, setStrategies] = useState<StrategyCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState("return");
  const [riskFilter, setRiskFilter] = useState<string | undefined>();

  useEffect(() => {
    loadStrategies();
  }, [sortBy, riskFilter]);

  async function loadStrategies() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchMarketplaceStrategies(sortBy, riskFilter);
      setStrategies(data.strategies);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategies');
      console.error('Failed to load strategies:', err);
    } finally {
      setLoading(false);
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-white">Loading strategies...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* 过滤器 */}
      <div className="flex gap-2">
        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="return">Sort by Return</SelectItem>
            <SelectItem value="risk">Sort by Risk</SelectItem>
            <SelectItem value="tvl">Sort by TVL</SelectItem>
            <SelectItem value="sharpe">Sort by Sharpe</SelectItem>
          </SelectContent>
        </Select>

        <Select value={riskFilter} onValueChange={setRiskFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="All Risk Levels" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Risk Levels</SelectItem>
            <SelectItem value="low">Low Risk</SelectItem>
            <SelectItem value="medium">Medium Risk</SelectItem>
            <SelectItem value="high">High Risk</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 策略卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {strategies.map((strategy) => (
          <Card
            key={strategy.id}
            onClick={() => onSelectStrategy(strategy.id)}
            className="cursor-pointer hover:shadow-xl"
          >
            {/* 策略卡片内容 */}
            <CardHeader>
              <CardTitle>{strategy.name}</CardTitle>
              <p className="text-sm text-slate-400">{strategy.subtitle}</p>
            </CardHeader>
            <CardContent>
              {/* 性能指标 - 使用后端字段名 */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <div className="text-xs text-slate-500">Annual Return</div>
                  <div className={`text-sm ${strategy.annualized_return > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {strategy.annualized_return > 0 ? '+' : ''}{strategy.annualized_return.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">Max Drawdown</div>
                  <div className="text-sm text-red-400">
                    {strategy.max_drawdown.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">Sharpe Ratio</div>
                  <div className="text-sm text-slate-300">
                    {strategy.sharpe_ratio.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">Pool Size</div>
                  <div className="text-sm text-slate-300">
                    ${(strategy.pool_size / 1000000).toFixed(1)}M
                  </div>
                </div>
              </div>

              {/* 迷你图表 - history现在包含date字段 */}
              <ResponsiveContainer width="100%" height={60}>
                <LineChart data={strategy.history}>
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#8B5CF6"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

---

## 🔧 2. StrategyDetails.tsx 集成

### Step 1: 更新TypeScript接口

```typescript
// src/types/strategy.ts
export interface StrategyDetail {
  id: string;
  name: string;
  description: string;
  tags: string[];

  performance_metrics: {
    annualized_return: number;
    max_drawdown: number;
    sharpe_ratio: number;
    sortino_ratio: number | null;  // ⚠️ 删除此字段的显示
  };

  conviction_summary: {
    score: number;
    message: string;
    updated_at: string;
  };

  squad_agents: Array<{
    name: string;
    role: string;
    weight: string;
  }>;

  performance_history: {
    strategy: number[];
    btc_benchmark: number[];
    eth_benchmark: number[];
    dates: string[];
  };

  recent_activities: Array<{
    date: string;
    signal: string;
    action: string;
    result: string;
    agent: string;
  }>;

  parameters: {
    assets: string;
    rebalance_period: string;
    risk_level: string;
    min_investment: string;
    lockup_period: string;
    management_fee: string;
    performance_fee: string;
  };

  philosophy: string;
}
```

### Step 2: 创建数据转换函数

```typescript
// src/utils/strategyUtils.ts

/**
 * 转换性能历史数据为图表格式
 */
export function convertPerformanceHistory(history: {
  strategy: number[];
  btc_benchmark: number[];
  eth_benchmark: number[];
  dates: string[];
}) {
  return history.dates.map((date, index) => ({
    date,
    strategy: history.strategy[index],
    btc: history.btc_benchmark[index],
    eth: history.eth_benchmark[index],
  }));
}

/**
 * 映射Agent图标
 */
export function getAgentIcon(role: string) {
  const iconMap = {
    'MacroAgent': Eye,
    'OnChainAgent': Database,
    'TAAgent': Zap,
  };
  return iconMap[role] || Activity;
}

/**
 * 映射Agent颜色
 */
export function getAgentColor(role: string) {
  const colorMap = {
    'MacroAgent': 'blue',
    'OnChainAgent': 'emerald',
    'TAAgent': 'amber',
  };
  return colorMap[role] || 'slate';
}
```

### Step 3: 创建API调用函数

```typescript
// src/services/marketplaceApi.ts
export async function fetchStrategyDetail(strategyId: string): Promise<StrategyDetail> {
  const response = await fetch(`${API_BASE_URL}/marketplace/${strategyId}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch strategy detail: ${response.statusText}`);
  }

  return response.json();
}
```

### Step 4: 替换Mock数据

```typescript
// src/components/StrategyDetails.tsx
import { useState, useEffect } from "react";
import { fetchStrategyDetail } from "../services/marketplaceApi";
import { convertPerformanceHistory, getAgentIcon, getAgentColor } from "../utils/strategyUtils";
import type { StrategyDetail } from "../types/strategy";

interface StrategyDetailsProps {
  strategyId: string;
  onBack: () => void;
}

export function StrategyDetails({ strategyId, onBack }: StrategyDetailsProps) {
  const [strategy, setStrategy] = useState<StrategyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStrategyDetail();
  }, [strategyId]);

  async function loadStrategyDetail() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchStrategyDetail(strategyId);
      setStrategy(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategy details');
      console.error('Failed to load strategy details:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="text-white">Loading strategy details...</div>;
  }

  if (error || !strategy) {
    return <div className="text-red-400">Error: {error || 'Strategy not found'}</div>;
  }

  // 转换性能历史数据
  const performanceData = convertPerformanceHistory(strategy.performance_history);

  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Marketplace
        </Button>
        <h1 className="text-white text-2xl mt-2">{strategy.name}</h1>
        <p className="text-slate-400">{strategy.description}</p>
      </div>

      {/* Squad Manager Insight */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-white">Squad Manager's Analysis</h3>
            <Badge className="bg-emerald-500/20 text-emerald-400">
              Conviction: {strategy.conviction_summary.score.toFixed(0)}%
            </Badge>
          </div>
          <p className="text-slate-300 text-sm">
            {strategy.conviction_summary.message}
          </p>
          <div className="text-slate-500 text-xs mt-2">
            Updated: {new Date(strategy.conviction_summary.updated_at).toLocaleString()}
          </div>
        </CardContent>
      </Card>

      {/* Squad Roster */}
      <Card>
        <CardHeader>
          <CardTitle>Squad Roster</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {strategy.squad_agents.map((agent, index) => {
              const Icon = getAgentIcon(agent.role);
              const color = getAgentColor(agent.role);

              return (
                <div key={index} className="bg-slate-800/50 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-10 h-10 bg-${color}-500 rounded-lg flex items-center justify-center`}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="text-white text-sm">{agent.name}</div>
                      <div className="text-slate-500 text-xs">{agent.role}</div>
                    </div>
                    <Badge className={`bg-${color}-500/20 text-${color}-400`}>
                      {agent.weight}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Performance History</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="strategy"
                stroke="#8B5CF6"
                strokeWidth={2.5}
                dot={false}
                name="Squad"
              />
              <Line
                type="monotone"
                dataKey="btc"
                stroke="#F59E0B"
                strokeWidth={2}
                dot={false}
                name="BTC"
                strokeDasharray="5 5"
              />
              <Line
                type="monotone"
                dataKey="eth"
                stroke="#10B981"
                strokeWidth={2}
                dot={false}
                name="ETH"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="bg-slate-800/30 rounded p-2">
            <div className="text-xs text-slate-500">Annualized Return</div>
            <div className={`text-lg ${strategy.performance_metrics.annualized_return > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {strategy.performance_metrics.annualized_return > 0 ? '+' : ''}
              {strategy.performance_metrics.annualized_return.toFixed(2)}%
            </div>
          </div>

          <div className="bg-slate-800/30 rounded p-2">
            <div className="text-xs text-slate-500">Max Drawdown</div>
            <div className="text-lg text-red-400">
              {strategy.performance_metrics.max_drawdown.toFixed(2)}%
            </div>
          </div>

          <div className="bg-slate-800/30 rounded p-2">
            <div className="text-xs text-slate-500">Sharpe Ratio</div>
            <div className="text-lg text-slate-300">
              {strategy.performance_metrics.sharpe_ratio.toFixed(2)}
            </div>
          </div>

          {/* ❌ Sortino Ratio 已删除 */}
        </CardContent>
      </Card>

      {/* Deploy & Withdraw */}
      <Card>
        <CardHeader>
          <CardTitle>Deploy & Withdraw</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="invest">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="invest">Deploy</TabsTrigger>
              <TabsTrigger value="withdraw">Withdraw</TabsTrigger>
            </TabsList>

            <TabsContent value="invest" className="space-y-3">
              {/* ⚠️ Available Balance 显示 N/A */}
              <div>
                <Label className="text-slate-400 text-sm">Available Balance</Label>
                <div className="text-white text-lg">N/A</div>
              </div>

              <div>
                <Label>Deployment Amount</Label>
                <Input
                  type="number"
                  placeholder="Enter amount"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>

              <Alert className="bg-amber-500/10 border-amber-500/50">
                <Clock className="h-4 w-4 text-amber-400" />
                <AlertDescription className="text-xs text-amber-300">
                  Deployment feature coming soon
                </AlertDescription>
              </Alert>

              <Button className="w-full" disabled>
                Deploy to Squad (Coming Soon)
              </Button>
            </TabsContent>

            <TabsContent value="withdraw" className="space-y-3">
              {/* 类似的withdraw内容 */}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Recent Activities */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Squad Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {strategy.recent_activities.map((activity, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-slate-800/30 rounded"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className="bg-purple-500/20 text-purple-400">
                      {activity.agent}
                    </Badge>
                    <span className="text-xs text-slate-500">{activity.date}</span>
                  </div>
                  <div className="text-white text-sm">
                    Signal: <span className="text-slate-300">{activity.signal}</span>
                  </div>
                  <div className="text-xs text-slate-400">Action: {activity.action}</div>
                </div>
                <div
                  className={`text-sm font-mono ${
                    activity.result.startsWith("+") ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {activity.result}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Strategy Parameters */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {Object.entries(strategy.parameters).map(([key, value]) => (
            <div key={key} className="flex justify-between bg-slate-800/30 rounded p-2">
              <span className="text-slate-400 text-sm capitalize">
                {key.replace(/_/g, ' ')}
              </span>
              <span className="text-slate-200 text-sm">{value}</span>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Philosophy */}
      <Card>
        <CardHeader>
          <CardTitle>Squad Mission</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-400 text-sm whitespace-pre-line">
            {strategy.philosophy}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## 🔐 认证配置

### 环境变量设置

```bash
# .env
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
```

### Token管理

```typescript
// src/utils/auth.ts
export function setAuthToken(token: string) {
  localStorage.setItem('token', token);
}

export function getAuthToken(): string | null {
  return localStorage.getItem('token');
}

export function clearAuthToken() {
  localStorage.removeItem('token');
}
```

---

## 🎨 关键调整总结

### 已删除的字段
- ❌ `sortinoRatio` (列表和详情页)
- ❌ `subtitle` (详情页)
- ❌ `tvl` (详情页metrics)

### 显示N/A的字段
- ⚠️ `availableBalance` → "N/A"

### 需要转换的数据
- ✅ `history[]` → 前端直接使用 `{date, value}` 结构
- ✅ `performanceData[]` → 使用 `convertPerformanceHistory()` 函数转换

### 字段名映射
- `annualized_return` ↔️ `annualizedReturn`
- `max_drawdown` ↔️ `maxDrawdown`
- `sharpe_ratio` ↔️ `sharpeRatio`
- `pool_size` ↔️ `poolSize` (原来的tvl)
- `squad_size` ↔️ `squadSize`
- `risk_level` ↔️ `riskLevel`

---

## ✅ 测试清单

前端集成完成后，请测试以下功能：

- [ ] 策略列表正常显示
- [ ] 策略卡片数据正确（年化收益、回撤等）
- [ ] 迷你图表正常渲染
- [ ] 排序功能正常工作
- [ ] 风险等级过滤正常工作
- [ ] 点击卡片跳转到详情页
- [ ] 详情页数据完整显示
- [ ] Conviction摘要正常显示
- [ ] 性能历史图表正确渲染（vs BTC/ETH）
- [ ] Squad Agents列表正确显示
- [ ] Recent Activities列表正确显示
- [ ] Available Balance显示为"N/A"
- [ ] 所有已删除字段不再显示

---

## 🐛 常见问题

### Q1: CORS错误
```
Access to fetch at 'http://localhost:8000/api/v1/marketplace' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**解决方案**: 后端已配置CORS，确保前端使用正确的URL。

### Q2: 认证失败
```
Failed to fetch strategies: Unauthorized
```

**解决方案**: 确保token正确存储在localStorage中。

### Q3: 数据结构不匹配
```
Cannot read property 'btc_benchmark' of undefined
```

**解决方案**: 使用提供的 `convertPerformanceHistory()` 函数转换数据。

---

## 📞 支持

如有问题，请联系后端团队或查看：
- [MARKETPLACE_API_COMPLETE.md](MARKETPLACE_API_COMPLETE.md) - 完整API文档
- [FRONTEND_BACKEND_DATA_MAPPING.md](FRONTEND_BACKEND_DATA_MAPPING.md) - 数据映射详情

---

**文档版本**: 1.0
**最后更新**: 2025-11-06 18:30
