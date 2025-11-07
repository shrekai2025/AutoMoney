import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { LineChart, Line, ResponsiveContainer } from "recharts";
import { TrendingUp, TrendingDown, Shield, Target, Users, Flame, Clock } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import redCharacter from "figma:asset/e7df430614095df0bf6f8507a2c9ff6a9129eaaf.png";
import greenCharacter from "figma:asset/c5bd439c73b523a0fe77e12f24d55c9e5fb9c986.png";

// Character avatars
const characters = [redCharacter, greenCharacter];

// Helper function to get consistent random character for each strategy
const getCharacterForStrategy = (strategyId: number) => {
  return characters[strategyId % characters.length];
};

// Mock strategy data
const strategies = [
  {
    id: 1,
    name: "HODL-Wave Squad",
    subtitle: "Macro Swing Strategy",
    tags: ["Macro-Driven", "BTC/ETH", "Long-Term"],
    annualizedReturn: 45.6,
    maxDrawdown: 18.2,
    sharpeRatio: 2.1,
    tvl: 12500000,
    squadSize: 3,
    history: [
      { value: 100 },
      { value: 95 },
      { value: 108 },
      { value: 103 },
      { value: 118 },
      { value: 112 },
      { value: 125 },
      { value: 122 },
    ],
    riskLevel: "medium",
  },
  {
    id: 2,
    name: "ArbitrageX Squad",
    subtitle: "High-Frequency Trading",
    tags: ["Quantitative", "Multi-Asset", "Arbitrage"],
    annualizedReturn: 68.3,
    maxDrawdown: 25.5,
    sharpeRatio: 1.8,
    tvl: 8300000,
    squadSize: 4,
    history: [
      { value: 100 },
      { value: 110 },
      { value: 105 },
      { value: 118 },
      { value: 112 },
      { value: 125 },
      { value: 120 },
      { value: 132 },
    ],
    riskLevel: "medium-high",
  },
  {
    id: 3,
    name: "MomentumPro Squad",
    subtitle: "Trend Following",
    tags: ["Technical", "Trend-Following", "BTC-Focused"],
    annualizedReturn: 52.1,
    maxDrawdown: 22.8,
    sharpeRatio: 1.9,
    tvl: 6700000,
    squadSize: 3,
    history: [
      { value: 100 },
      { value: 88 },
      { value: 95 },
      { value: 108 },
      { value: 102 },
      { value: 115 },
      { value: 108 },
      { value: 120 },
    ],
    riskLevel: "medium",
  },
  {
    id: 4,
    name: "StableGuard Squad",
    subtitle: "Stable Yield Strategy",
    tags: ["Low Risk", "Stablecoin", "Conservative"],
    annualizedReturn: 28.5,
    maxDrawdown: 8.3,
    sharpeRatio: 2.5,
    tvl: 15200000,
    squadSize: 2,
    history: [
      { value: 100 },
      { value: 102 },
      { value: 99 },
      { value: 105 },
      { value: 103 },
      { value: 109 },
      { value: 107 },
      { value: 113 },
    ],
    riskLevel: "low",
  },
  {
    id: 5,
    name: "DeFiYield Squad",
    subtitle: "Yield Optimizer",
    tags: ["DeFi", "Yield Farming", "Multi-Protocol"],
    annualizedReturn: 78.9,
    maxDrawdown: 32.1,
    sharpeRatio: 1.6,
    tvl: 4500000,
    squadSize: 5,
    history: [
      { value: 100 },
      { value: 115 },
      { value: 108 },
      { value: 125 },
      { value: 118 },
      { value: 135 },
      { value: 128 },
      { value: 142 },
    ],
    riskLevel: "high",
  },
  {
    id: 6,
    name: "AIPredict Squad",
    subtitle: "Predictive Trading",
    tags: ["AI-Powered", "Machine Learning", "Multi-Factor"],
    annualizedReturn: 61.2,
    maxDrawdown: 20.5,
    sharpeRatio: 2.0,
    tvl: 9800000,
    squadSize: 4,
    history: [
      { value: 100 },
      { value: 108 },
      { value: 102 },
      { value: 115 },
      { value: 110 },
      { value: 125 },
      { value: 120 },
      { value: 128 },
    ],
    riskLevel: "medium",
  },
  {
    id: 7,
    name: "GridMaster Squad",
    subtitle: "Grid Trading Strategy",
    tags: ["Quantitative", "Range-Bound", "Auto-Rebalance"],
    annualizedReturn: -8.3,
    maxDrawdown: 35.2,
    sharpeRatio: 0.4,
    tvl: 2100000,
    squadSize: 3,
    history: [
      { value: 100 },
      { value: 95 },
      { value: 88 },
      { value: 92 },
      { value: 85 },
      { value: 90 },
      { value: 83 },
      { value: 87 },
    ],
    riskLevel: "high",
  },
  {
    id: 8,
    name: "VolatilityX Squad",
    subtitle: "Volatility Arbitrage",
    tags: ["Options", "Volatility", "Derivatives"],
    annualizedReturn: -12.5,
    maxDrawdown: 42.8,
    sharpeRatio: 0.2,
    tvl: 1500000,
    squadSize: 4,
    history: [
      { value: 100 },
      { value: 92 },
      { value: 98 },
      { value: 85 },
      { value: 90 },
      { value: 78 },
      { value: 85 },
      { value: 82 },
    ],
    riskLevel: "high",
  },
];

interface StrategyMarketplaceProps {
  onSelectStrategy: (strategyId: number) => void;
}

export function StrategyMarketplace({ onSelectStrategy }: StrategyMarketplaceProps) {
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "low":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/50";
      case "medium":
        return "bg-blue-500/20 text-blue-400 border-blue-500/50";
      case "medium-high":
        return "bg-amber-500/20 text-amber-400 border-amber-500/50";
      case "high":
        return "bg-red-500/20 text-red-400 border-red-500/50";
      default:
        return "bg-slate-500/20 text-slate-400 border-slate-500/50";
    }
  };

  const getRiskLabel = (risk: string) => {
    switch (risk) {
      case "low":
        return "🛡️ Low";
      case "medium":
        return "⚖️ Medium";
      case "medium-high":
        return "⚡ Med-High";
      case "high":
        return "🔥 High";
      default:
        return "Unknown";
    }
  };

  return (
    <div className="space-y-3">
      {/* Page Header and Filters */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <h1 className="text-white mb-0.5 text-xl flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            Strategy By AI Squads
          </h1>
          <p className="text-slate-400 text-xs">Discover and deploy elite AI trading squads</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Select defaultValue="7d">
            <SelectTrigger className="w-[120px] h-7 text-xs bg-slate-800/50 border-slate-700 text-slate-200">
              <SelectValue placeholder="Time Range" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700 text-slate-200">
              <SelectItem value="24h" className="text-xs">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3 h-3" />
                  24 Hours
                </div>
              </SelectItem>
              <SelectItem value="7d" className="text-xs">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3 h-3" />
                  7 Days
                </div>
              </SelectItem>
              <SelectItem value="30d" className="text-xs">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3 h-3" />
                  30 Days
                </div>
              </SelectItem>
              <SelectItem value="90d" className="text-xs">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3 h-3" />
                  90 Days
                </div>
              </SelectItem>
              <SelectItem value="1y" className="text-xs">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3 h-3" />
                  1 Year
                </div>
              </SelectItem>
              <SelectItem value="all" className="text-xs">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3 h-3" />
                  All Time
                </div>
              </SelectItem>
            </SelectContent>
          </Select>

          <Select defaultValue="return">
            <SelectTrigger className="w-[140px] h-7 text-xs bg-slate-800/50 border-slate-700 text-slate-200">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700 text-slate-200">
              <SelectItem value="return" className="text-xs">Sort by Return</SelectItem>
              <SelectItem value="risk" className="text-xs">Sort by Risk</SelectItem>
              <SelectItem value="tvl" className="text-xs">Sort by TVL</SelectItem>
              <SelectItem value="sharpe" className="text-xs">Sort by Sharpe</SelectItem>
            </SelectContent>
          </Select>

          <Select defaultValue="all">
            <SelectTrigger className="w-[140px] h-7 text-xs bg-slate-800/50 border-slate-700 text-slate-200">
              <SelectValue placeholder="Risk Level" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700 text-slate-200">
              <SelectItem value="all" className="text-xs">All Risk Levels</SelectItem>
              <SelectItem value="low" className="text-xs">Low Risk</SelectItem>
              <SelectItem value="medium" className="text-xs">Medium Risk</SelectItem>
              <SelectItem value="high" className="text-xs">High Risk</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Strategy Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {strategies.map((strategy) => {
          const isNegativeReturn = strategy.annualizedReturn < 0;
          const lineColor = isNegativeReturn ? "#EF4444" : "#8B5CF6";
          
          return (
            <Card 
              key={strategy.id} 
              className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm hover:bg-slate-800/70 hover:shadow-xl hover:shadow-purple-500/10 transition-all duration-300 hover:scale-[1.02] cursor-pointer group relative overflow-hidden"
              onClick={() => onSelectStrategy(strategy.id)}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              
              <CardHeader className="pb-1.5 pt-2.5 px-3 relative">
                <div className="flex items-start gap-2 mb-1.5">
                  {/* Character Avatar */}
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 rounded-full overflow-hidden bg-gradient-to-br from-purple-500/20 to-blue-500/20 p-0.5 shadow-lg">
                      <div className="w-full h-full rounded-full overflow-hidden bg-black flex items-center justify-center">
                        <ImageWithFallback 
                          src={getCharacterForStrategy(strategy.id)}
                          alt={`${strategy.name} Character`}
                          className="w-full h-full object-contain"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-0.5">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-white text-xs leading-tight mb-0.5">{strategy.name}</CardTitle>
                        <p className="text-slate-500 text-xs">{strategy.subtitle}</p>
                      </div>
                      <Badge className={`${getRiskColor(strategy.riskLevel)} text-xs px-1.5 py-0 h-4 leading-none flex items-center ml-2 flex-shrink-0`} variant="outline">
                        {getRiskLabel(strategy.riskLevel)}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50 text-xs px-1.5 py-0 h-4">
                    <Users className="w-2.5 h-2.5 mr-1" />
                    {strategy.squadSize} Agents
                  </Badge>
                  {strategy.tags.slice(0, 2).map((tag, index) => (
                    <Badge key={index} variant="secondary" className="text-xs px-1.5 py-0 h-4 bg-slate-800/50 text-slate-400 border-slate-700">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </CardHeader>

              <CardContent className="space-y-2 px-3 pb-2.5 relative">
                {/* Mini Performance Chart */}
                <div className="h-14 -mx-1 bg-slate-800/30 rounded-lg overflow-hidden relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={strategy.history}>
                      <defs>
                        <linearGradient id={`gradient-${strategy.id}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={lineColor} stopOpacity={0.3}/>
                          <stop offset="95%" stopColor={lineColor} stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={lineColor}
                        strokeWidth={2}
                        dot={false}
                        fill={`url(#gradient-${strategy.id})`}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Key Performance Indicators */}
                <div className="grid grid-cols-2 gap-1.5">
                  <div className="bg-slate-800/30 rounded p-1.5">
                    <div className="text-xs text-slate-500 mb-0.5 flex items-center gap-1">
                      <Flame className={`w-2.5 h-2.5 ${isNegativeReturn ? 'text-red-400' : 'text-emerald-400'}`} />
                      Return Power
                    </div>
                    <div className={`flex items-center gap-0.5 ${isNegativeReturn ? 'text-red-400' : 'text-emerald-400'}`}>
                      <span className="text-xs">{strategy.annualizedReturn > 0 ? '+' : ''}{strategy.annualizedReturn}%</span>
                    </div>
                  </div>
                  <div className="bg-slate-800/30 rounded p-1.5">
                    <div className="text-xs text-slate-500 mb-0.5 flex items-center gap-1">
                      <Shield className="w-2.5 h-2.5 text-blue-400" />
                      Defense
                    </div>
                    <div className="flex items-center gap-0.5 text-red-400">
                      <span className="text-xs">{strategy.maxDrawdown}%</span>
                    </div>
                  </div>
                  <div className="bg-slate-800/30 rounded p-1.5">
                    <div className="text-xs text-slate-500 mb-0.5">Sharpe</div>
                    <div className="flex items-center gap-0.5 text-slate-300">
                      <Target className="w-2.5 h-2.5" />
                      <span className="text-xs">{strategy.sharpeRatio}</span>
                    </div>
                  </div>
                  <div className="bg-slate-800/30 rounded p-1.5">
                    <div className="text-xs text-slate-500 mb-0.5">Pool Size</div>
                    <div className="flex items-center gap-0.5 text-slate-300">
                      <span className="text-xs">${(strategy.tvl / 1000000).toFixed(1)}M</span>
                    </div>
                  </div>
                </div>

                <Button
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600 border-0 shadow-lg shadow-purple-500/30 group-hover:shadow-purple-500/50 transition-shadow h-7 text-xs"
                  onClick={() => onSelectStrategy(strategy.id)}
                >
                  <Users className="w-3 h-3 mr-1.5" />
                  Deploy Squad
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
