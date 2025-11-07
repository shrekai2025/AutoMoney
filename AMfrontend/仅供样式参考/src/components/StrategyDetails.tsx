import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Checkbox } from "./ui/checkbox";
import { Alert, AlertDescription } from "./ui/alert";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  Info,
  Clock,
  BarChart3,
  Activity,
  Users,
  Eye,
  Database,
  Zap,
} from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import redCharacter from "figma:asset/e7df430614095df0bf6f8507a2c9ff6a9129eaaf.png";
import greenCharacter from "figma:asset/c5bd439c73b523a0fe77e12f24d55c9e5fb9c986.png";

// Mock detailed performance data
const performanceData = [
  { date: "2024-07", strategy: 100, btc: 100, eth: 100 },
  { date: "2024-08", strategy: 105, btc: 102, eth: 98 },
  { date: "2024-09", strategy: 112, btc: 108, eth: 105 },
  { date: "2024-10", strategy: 118, btc: 110, eth: 108 },
  { date: "2024-11", strategy: 125, btc: 115, eth: 112 },
  { date: "2024-12", strategy: 132, btc: 118, eth: 115 },
  { date: "2025-01", strategy: 138, btc: 122, eth: 120 },
  { date: "2025-02", strategy: 145, btc: 125, eth: 123 },
  { date: "2025-03", strategy: 152, btc: 130, eth: 128 },
  { date: "2025-04", strategy: 158, btc: 135, eth: 132 },
  { date: "2025-05", strategy: 165, btc: 140, eth: 138 },
  { date: "2025-06", strategy: 172, btc: 145, eth: 142 },
  { date: "2025-07", strategy: 180, btc: 148, eth: 145 },
  { date: "2025-08", strategy: 188, btc: 152, eth: 150 },
  { date: "2025-09", strategy: 195, btc: 158, eth: 155 },
  { date: "2025-10", strategy: 203, btc: 162, eth: 160 },
];

const recentActivities = [
  {
    date: "2025-10-30 08:00 UTC",
    signal: "Strong Bull Market",
    action: "Buy 0.5% BTC",
    result: "+1.2%",
    agent: "The Oracle"
  },
  {
    date: "2025-10-29 08:00 UTC",
    signal: "Moderate Bullish",
    action: "Hold Current Position",
    result: "+0.8%",
    agent: "Data Warden"
  },
  {
    date: "2025-10-28 08:00 UTC",
    signal: "Neutral-Bullish",
    action: "Buy 0.3% ETH",
    result: "+0.5%",
    agent: "Momentum Scout"
  },
  {
    date: "2025-10-27 08:00 UTC",
    signal: "Consolidation",
    action: "Reduce 0.2% BTC",
    result: "-0.3%",
    agent: "The Oracle"
  },
  {
    date: "2025-10-26 08:00 UTC",
    signal: "Strong Rebound",
    action: "Buy 0.8% BTC",
    result: "+2.1%",
    agent: "Data Warden"
  },
];

const squadAgents = [
  { name: "The Oracle", role: "MacroAgent", weight: "40%", icon: Eye, color: "blue" },
  { name: "Data Warden", role: "OnChainAgent", weight: "40%", icon: Database, color: "emerald" },
  { name: "Momentum Scout", role: "TAAgent", weight: "20%", icon: Zap, color: "amber" },
];

// Character avatars
const characters = [redCharacter, greenCharacter];

// Helper function to get consistent random character for each strategy
const getCharacterForStrategy = (strategyId: number) => {
  return characters[strategyId % characters.length];
};

// Manager's conviction summary messages
const getManagerSummary = (strategyId: number) => {
  const summaries = [
    {
      conviction: 78,
      message: "Market conditions are favorable. Our macro analysis shows strong institutional inflows and improving on-chain metrics. The squad maintains a bullish stance with 78% conviction. Recommended position: Accumulate on dips."
    },
    {
      conviction: 65,
      message: "We're observing mixed signals across our data feeds. Technical indicators suggest consolidation while on-chain data remains neutral. Current conviction at 65%. Strategy: Hold current positions and monitor for breakout signals."
    },
    {
      conviction: 82,
      message: "Extremely bullish setup detected! All three agents are aligned - macro tailwinds, strong on-chain fundamentals, and positive momentum. Conviction score: 82%. This is an excellent entry opportunity for long-term holders."
    },
    {
      conviction: 71,
      message: "Market sentiment is cautiously optimistic. We're seeing healthy accumulation patterns and decreasing exchange reserves. Squad conviction: 71%. Strategy execution: Gradual position building over next 48 hours."
    },
    {
      conviction: 58,
      message: "Entering a period of uncertainty. Macro headwinds and elevated volatility detected. Our conviction has moderated to 58%. Risk management protocol activated - maintaining defensive positioning until clearer signals emerge."
    },
    {
      conviction: 75,
      message: "Strong technical breakout confirmed! The Oracle identifies improving liquidity conditions while Data Warden reports whale accumulation. Combined conviction: 75%. Recommended action: Increase exposure within risk parameters."
    },
  ];
  return summaries[strategyId % summaries.length];
};

interface StrategyDetailsProps {
  strategyId: number;
  onBack: () => void;
}

export function StrategyDetails({ strategyId, onBack }: StrategyDetailsProps) {
  const [investAmount, setInvestAmount] = useState("");
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [showBTC, setShowBTC] = useState(true);
  const [showETH, setShowETH] = useState(true);
  const [timeRange, setTimeRange] = useState("all");

  const availableBalance = 15000;
  const currentInvestment = 45000;

  // Mock strategy details
  const strategy = {
    name: "HODL-Wave Squad",
    subtitle: "Macro Swing Strategy",
    description: "Elite AI squad combining macroeconomic analysis with on-chain intelligence",
    tags: ["Macro-Driven", "BTC/ETH", "Long-Term", "Low-Medium Risk"],
    annualizedReturn: 45.6,
    maxDrawdown: 18.2,
    sharpeRatio: 2.1,
    sortinoRatio: 2.8,
    tvl: 12500000,
    riskLevel: "medium",
    philosophy: `The HODL-Wave Squad is an elite team of AI agents working in perfect synchronization to capture long-term value in the crypto market.

Squad Composition:
• The Oracle (MacroAgent 40%): Monitors global liquidity, inflation expectations, and Fed policy
• Data Warden (OnChainAgent 40%): Analyzes holder distribution, exchange flows, and network metrics
• Momentum Scout (TAAgent 20%): Tracks technical trends, RSI, and chart patterns

Mission Strategy:
Our squad employs a disciplined approach to building positions during macro-favorable conditions while maintaining strict risk controls. Maximum drawdown is kept within 20% through coordinated squad decision-making.

Ideal For:
Investors seeking long-term stable returns who trust in the fundamental value proposition of Bitcoin and Ethereum.`,
    parameters: {
      assets: "BTC 60% / ETH 40%",
      rebalancePeriod: "Every 4 Hours",
      riskLevel: "Low-Medium Risk",
      minInvestment: "100 USDT",
      lockupPeriod: "No Lock-up",
      managementFee: "2% Annual",
      performanceFee: "20% on Excess Returns",
    },
  };

  const handleInvest = () => {
    if (!investAmount || parseFloat(investAmount) <= 0) return;
    alert(`Deployment Confirmed: You will deploy $${investAmount} to ${strategy.name}`);
  };

  const handleWithdraw = () => {
    if (!withdrawAmount || parseFloat(withdrawAmount) <= 0) return;
    alert(`Withdrawal Confirmed: You will withdraw $${withdrawAmount} from ${strategy.name}`);
  };

  const managerSummary = getManagerSummary(strategyId);

  return (
    <div className="space-y-3">
      {/* Back Button and Header */}
      <div>
        <Button variant="ghost" onClick={onBack} className="gap-2 mb-2 text-slate-200 hover:text-white hover:bg-slate-800 h-7 px-2 text-xs">
          <ArrowLeft className="w-3 h-3" />
          Back to Recruitment
        </Button>
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-white text-xl">{strategy.name}</h1>
              <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50 text-xs px-2 py-0.5">
                <Users className="w-3 h-3 mr-1" />
                {squadAgents.length} Agents
              </Badge>
            </div>
            <p className="text-slate-400 text-xs mb-1.5">{strategy.description}</p>
            <div className="flex flex-wrap gap-1">
              {strategy.tags.map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs px-1.5 py-0 h-4 bg-slate-800/50 text-slate-400 border-slate-700">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Squad Manager Insight */}
      <Card className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 border-purple-500/50 backdrop-blur-sm relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-blue-500/10"></div>
        <CardContent className="p-3 relative">
          <div className="flex gap-3">
            {/* Manager Avatar */}
            <div className="flex-shrink-0">
              <div className="relative">
                <div className="w-16 h-16 rounded-full overflow-hidden bg-gradient-to-br from-purple-500 to-blue-500 p-0.5 shadow-2xl shadow-purple-500/50">
                  <div className="w-full h-full rounded-full overflow-hidden bg-black flex items-center justify-center">
                    <ImageWithFallback 
                      src={getCharacterForStrategy(strategyId)}
                      alt="Squad Manager"
                      className="w-full h-full object-contain"
                    />
                  </div>
                </div>
                <div className="absolute -bottom-1 -right-1">
                  <Badge className="bg-purple-500/30 text-purple-300 border-purple-400/50 text-xs px-1.5 py-0 h-4">
                    Manager
                  </Badge>
                </div>
              </div>
            </div>

            {/* Manager's Message */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1.5">
                <h3 className="text-white text-sm">Squad Manager's Latest Analysis</h3>
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50 text-xs px-1.5 py-0 h-4">
                  Conviction: {managerSummary.conviction}%
                </Badge>
              </div>
              <div className="relative bg-slate-900/50 rounded-lg p-2.5 border border-purple-500/20">
                {/* Speech bubble tail */}
                <div className="absolute -left-2 top-4 w-0 h-0 border-t-8 border-t-transparent border-b-8 border-b-transparent border-r-8 border-r-purple-500/20"></div>
                <p className="text-slate-300 text-xs leading-relaxed">
                  {managerSummary.message}
                </p>
                <div className="flex items-center gap-1 mt-2 text-slate-500 text-xs">
                  <Clock className="w-3 h-3" />
                  <span>Updated 2 hours ago</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Squad Roster */}
      <Card className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-purple-500/30 backdrop-blur-sm relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-blue-500/5"></div>
        <CardHeader className="pb-2 pt-2.5 px-3 relative">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <Users className="w-4 h-4 text-purple-400" />
            Squad Roster
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-2.5 relative">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {squadAgents.map((agent, index) => (
              <div key={index} className="bg-slate-800/50 rounded-lg p-2 border border-slate-700/50 hover:border-slate-600/50 transition-colors">
                <div className="flex items-center gap-2 mb-1">
                  <div className={`w-8 h-8 bg-gradient-to-br from-${agent.color}-500 to-${agent.color}-600 rounded-lg flex items-center justify-center shadow-lg shadow-${agent.color}-500/50`}>
                    <agent.icon className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-white text-xs">{agent.name}</div>
                    <div className="text-slate-500 text-xs">{agent.role}</div>
                  </div>
                  <Badge className={`bg-${agent.color}-500/20 text-${agent.color}-400 border-${agent.color}-500/50 text-xs px-1.5 py-0`}>
                    {agent.weight}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Fund Pool Performance Chart */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-2 pt-2.5 px-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <CardTitle className="text-white text-sm">Squad Performance History</CardTitle>
            <div className="flex gap-1.5 flex-wrap">
              <Button
                variant={timeRange === "1m" ? "default" : "outline"}
                size="sm"
                onClick={() => setTimeRange("1m")}
                className={`h-6 text-xs px-2 ${
                  timeRange === "1m" 
                    ? "bg-purple-600 hover:bg-purple-700 text-white" 
                    : "border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white"
                }`}
              >
                1M
              </Button>
              <Button
                variant={timeRange === "3m" ? "default" : "outline"}
                size="sm"
                onClick={() => setTimeRange("3m")}
                className={`h-6 text-xs px-2 ${
                  timeRange === "3m" 
                    ? "bg-purple-600 hover:bg-purple-700 text-white" 
                    : "border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white"
                }`}
              >
                3M
              </Button>
              <Button
                variant={timeRange === "1y" ? "default" : "outline"}
                size="sm"
                onClick={() => setTimeRange("1y")}
                className={`h-6 text-xs px-2 ${
                  timeRange === "1y" 
                    ? "bg-purple-600 hover:bg-purple-700 text-white" 
                    : "border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white"
                }`}
              >
                1Y
              </Button>
              <Button
                variant={timeRange === "all" ? "default" : "outline"}
                size="sm"
                onClick={() => setTimeRange("all")}
                className={`h-6 text-xs px-2 ${
                  timeRange === "all" 
                    ? "bg-purple-600 hover:bg-purple-700 text-white" 
                    : "border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white"
                }`}
              >
                All
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="px-3 pb-2.5">
          <div className="mb-2 flex gap-3 text-xs">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <Checkbox checked={showBTC} onCheckedChange={setShowBTC} className="h-3 w-3" />
              <span className="text-slate-300">vs BTC</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <Checkbox checked={showETH} onCheckedChange={setShowETH} className="h-3 w-3" />
              <span className="text-slate-300">vs ETH</span>
            </label>
          </div>

          <div className="bg-slate-800/30 rounded-lg p-2">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" style={{ fontSize: '10px' }} />
                <YAxis stroke="#64748b" style={{ fontSize: '10px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: "6px",
                    color: "#fff",
                    fontSize: "11px"
                  }}
                  formatter={(value: number) => `${value.toFixed(2)}%`}
                />
                <Legend wrapperStyle={{ fontSize: '10px' }} />
                <Line
                  type="monotone"
                  dataKey="strategy"
                  stroke="#8B5CF6"
                  strokeWidth={2.5}
                  dot={false}
                  name="Squad"
                />
                {showBTC && (
                  <Line
                    type="monotone"
                    dataKey="btc"
                    stroke="#F59E0B"
                    strokeWidth={2}
                    dot={false}
                    name="BTC"
                    strokeDasharray="5 5"
                  />
                )}
                {showETH && (
                  <Line
                    type="monotone"
                    dataKey="eth"
                    stroke="#10B981"
                    strokeWidth={2}
                    dot={false}
                    name="ETH"
                    strokeDasharray="5 5"
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <Alert className="mt-2 bg-purple-500/10 border-purple-500/50 py-2">
            <Info className="h-3 w-3 text-purple-400" />
            <AlertDescription className="text-xs text-purple-300">
              Squad performance normalized to 100 at start. Comparison shows BTC/ETH benchmark performance.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Deploy & Withdraw Panel */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm lg:col-span-2">
          <CardHeader className="pb-2 pt-2.5 px-3">
            <CardTitle className="text-white text-sm">Deploy & Withdraw Funds</CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-2.5">
            <Tabs defaultValue="invest">
              <TabsList className="grid w-full grid-cols-2 bg-slate-800/50 h-7">
                <TabsTrigger value="invest" className="data-[state=active]:bg-purple-600 text-xs">Deploy</TabsTrigger>
                <TabsTrigger value="withdraw" className="data-[state=active]:bg-purple-600 text-xs">Withdraw</TabsTrigger>
              </TabsList>

              <TabsContent value="invest" className="space-y-2 mt-3">
                <div className="space-y-1">
                  <Label className="text-slate-400 text-xs">Available Balance</Label>
                  <div className="text-white">${availableBalance.toLocaleString()}</div>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="invest-amount" className="text-slate-400 text-xs">Deployment Amount</Label>
                  <Input
                    id="invest-amount"
                    type="number"
                    placeholder="Enter amount"
                    value={investAmount}
                    onChange={(e) => setInvestAmount(e.target.value)}
                    className="bg-slate-800/50 border-slate-700 text-white h-8 text-sm"
                  />
                </div>

                <Alert className="bg-amber-500/10 border-amber-500/50 py-2">
                  <Clock className="h-3 w-3 text-amber-400" />
                  <AlertDescription className="text-xs text-amber-300">
                    Squad will activate your funds at the next 4-hour cycle checkpoint.
                  </AlertDescription>
                </Alert>

                <Button className="w-full bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600 h-8 text-xs" onClick={handleInvest}>
                  <Users className="w-3 h-3 mr-1.5" />
                  Deploy to Squad
                </Button>
              </TabsContent>

              <TabsContent value="withdraw" className="space-y-2 mt-3">
                <div className="space-y-1">
                  <Label className="text-slate-400 text-xs">Current Deployment</Label>
                  <div className="text-white">${currentInvestment.toLocaleString()}</div>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="withdraw-amount" className="text-slate-400 text-xs">Withdrawal Amount</Label>
                  <Input
                    id="withdraw-amount"
                    type="number"
                    placeholder="Enter amount"
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(e.target.value)}
                    className="bg-slate-800/50 border-slate-700 text-white h-8 text-sm"
                  />
                </div>

                <Alert className="bg-amber-500/10 border-amber-500/50 py-2">
                  <Clock className="h-3 w-3 text-amber-400" />
                  <AlertDescription className="text-xs text-amber-300">
                    Withdrawal processed after current cycle. Funds arrive at next checkpoint.
                  </AlertDescription>
                </Alert>

                <Button className="w-full border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white h-8 text-xs" variant="outline" onClick={handleWithdraw}>
                  Confirm Withdrawal
                </Button>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Performance Metrics */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-2.5 px-3">
            <CardTitle className="flex items-center gap-1.5 text-white text-sm">
              <BarChart3 className="w-3.5 h-3.5" />
              Squad Stats
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5 px-3 pb-2.5">
            <div className="bg-slate-800/30 rounded p-1.5">
              <div className="text-xs text-slate-500 mb-0.5">Annual Return</div>
              <div className="flex items-center gap-0.5 text-emerald-400">
                <TrendingUp className="w-3 h-3" />
                <span className="text-xs">{strategy.annualizedReturn}%</span>
              </div>
            </div>
            <div className="bg-slate-800/30 rounded p-1.5">
              <div className="text-xs text-slate-500 mb-0.5">Max Drawdown</div>
              <div className="flex items-center gap-0.5 text-red-400">
                <TrendingDown className="w-3 h-3" />
                <span className="text-xs">{strategy.maxDrawdown}%</span>
              </div>
            </div>
            <div className="bg-slate-800/30 rounded p-1.5">
              <div className="text-xs text-slate-500 mb-0.5">Sharpe Ratio</div>
              <div className="flex items-center gap-0.5 text-slate-300">
                <Target className="w-3 h-3" />
                <span className="text-xs">{strategy.sharpeRatio}</span>
              </div>
            </div>
            <div className="bg-slate-800/30 rounded p-1.5">
              <div className="text-xs text-slate-500 mb-0.5">Sortino Ratio</div>
              <div className="flex items-center gap-0.5 text-slate-300">
                <Target className="w-3 h-3" />
                <span className="text-xs">{strategy.sortinoRatio}</span>
              </div>
            </div>
            <div className="bg-slate-800/30 rounded p-1.5">
              <div className="text-xs text-slate-500 mb-0.5">Total Pool Size</div>
              <div className="flex items-center gap-0.5 text-slate-300">
                <Shield className="w-3 h-3" />
                <span className="text-xs">${(strategy.tvl / 1000000).toFixed(1)}M</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Strategy Parameters */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-2.5 px-3">
            <CardTitle className="flex items-center gap-1.5 text-white text-sm">
              <Target className="w-3.5 h-3.5" />
              Squad Parameters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5 px-3 pb-2.5">
            {Object.entries(strategy.parameters).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center text-xs bg-slate-800/30 rounded p-1.5">
                <span className="text-slate-400">
                  {key === "assets" && "Asset Focus"}
                  {key === "rebalancePeriod" && "Rebalance Cycle"}
                  {key === "riskLevel" && "Risk Profile"}
                  {key === "minInvestment" && "Min Deployment"}
                  {key === "lockupPeriod" && "Lock Period"}
                  {key === "managementFee" && "Mgmt Fee"}
                  {key === "performanceFee" && "Perf Fee"}
                </span>
                <span className="text-slate-200 text-xs">{value}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Strategy Philosophy */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-2.5 px-3">
            <CardTitle className="text-white text-sm">Squad Mission</CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-2.5">
            <div className="text-slate-400 text-xs whitespace-pre-line leading-relaxed">{strategy.philosophy}</div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-2 pt-2.5 px-3">
          <CardTitle className="flex items-center gap-1.5 text-white text-sm">
            <Activity className="w-3.5 h-3.5" />
            Recent Squad Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-2.5">
          <div className="space-y-1.5">
            {recentActivities.map((activity, index) => (
              <div
                key={index}
                className="flex flex-col md:flex-row md:items-center md:justify-between gap-1 p-2 bg-slate-800/30 rounded hover:bg-slate-800/50 transition-colors border border-slate-700/30"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50 text-xs px-1.5 py-0">
                      {activity.agent}
                    </Badge>
                    <span className="text-xs text-slate-500">{activity.date}</span>
                  </div>
                  <div className="text-white text-xs">
                    Signal: <span className="text-slate-300">{activity.signal}</span>
                  </div>
                  <div className="text-xs text-slate-400">Action: {activity.action}</div>
                </div>
                <div
                  className={`text-xs font-mono ${
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
    </div>
  );
}
