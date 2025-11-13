import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import { TrendingUp, TrendingDown, Shield, Target, Users, Flame, Clock, Rocket } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import redCharacter from "figma:asset/e7df430614095df0bf6f8507a2c9ff6a9129eaaf.png";
import greenCharacter from "figma:asset/c5bd439c73b523a0fe77e12f24d55c9e5fb9c986.png";
import { fetchMarketplaceStrategies } from "../lib/marketplaceApi";
import type { StrategyCard } from "../types/strategy";
import { formatPoolSize } from "../utils/strategyUtils";
import { useAuth } from "../contexts/AuthContext";
import { LoginPlaceholder } from "./LoginPlaceholder";
import { LaunchStrategyModal } from "./LaunchStrategyModal";
import { toast } from "sonner";

// Character avatars
const characters = [redCharacter, greenCharacter];

// Helper function to get consistent random character for each strategy
const getCharacterForStrategy = (strategyId: string) => {
  // Use hash of UUID to get consistent character
  const hash = strategyId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return characters[hash % characters.length];
};

interface StrategyMarketplaceProps {
  onSelectStrategy: (strategyId: string) => void;
}

export function StrategyMarketplace({ onSelectStrategy }: StrategyMarketplaceProps) {
  const { isAuthenticated, user } = useAuth();
  const [strategies, setStrategies] = useState<StrategyCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState("return");
  const [riskFilter, setRiskFilter] = useState<string>("all");

  // Launch strategy modal state
  const [launchModalOpen, setLaunchModalOpen] = useState(false);

  // Check if user can launch strategies (trader or admin)
  const canLaunchStrategy = user && (user.role === 'trader' || user.role === 'admin');

  // 使用 useCallback 包装 loadStrategies，确保函数引用稳定
  const loadStrategies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchMarketplaceStrategies(
        sortBy,
        riskFilter === 'all' ? undefined : riskFilter
      );
      setStrategies(data.strategies);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategies');
      console.error('Failed to load strategies:', err);
    } finally {
      setLoading(false);
    }
  }, [sortBy, riskFilter]);

  // 将所有 Hooks 移到条件返回之前，确保每次渲染时 Hooks 调用顺序一致
  useEffect(() => {
    // 只有在用户已认证时才加载数据
    if (isAuthenticated) {
      loadStrategies();
    }
  }, [isAuthenticated, loadStrategies]);

  // Show login placeholder if not authenticated
  if (!isAuthenticated) {
    return (
      <LoginPlaceholder
        title="Strategy Marketplace"
        description="Sign in to explore and deploy elite AI trading squads. Browse strategies, compare performance metrics, and join successful trading communities."
        icon={Users}
      />
    );
  }


  const handleCardClick = (strategy: StrategyCard) => {
    // Navigate to strategy details page
    onSelectStrategy(strategy.id);
  };
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

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p>Loading strategies...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-red-400 mb-4">⚠️ Error loading strategies</div>
          <p className="text-slate-400 text-sm mb-4">{error}</p>
          <Button onClick={loadStrategies} className="bg-purple-600 hover:bg-purple-700">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

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
          {canLaunchStrategy && (
            <Button
              onClick={() => setLaunchModalOpen(true)}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              <Rocket className="w-4 h-4 mr-2" />
              Launch Strategy
            </Button>
          )}
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

          <Select value={sortBy} onValueChange={setSortBy}>
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

          <Select value={riskFilter} onValueChange={setRiskFilter}>
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
          const isNegativeReturn = strategy.annualized_return < 0;
          const lineColor = isNegativeReturn ? "#EF4444" : "#8B5CF6";

          return (
            <Card
              key={strategy.id}
              className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm transition-all duration-300 group relative overflow-hidden hover:bg-slate-800/70 hover:shadow-xl hover:shadow-purple-500/10 hover:scale-[1.02] cursor-pointer"
              onClick={() => handleCardClick(strategy)}
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
                      <Badge className={`${getRiskColor(strategy.risk_level)} text-xs px-1.5 py-0 h-4 leading-none flex items-center ml-2 flex-shrink-0`} variant="outline">
                        {getRiskLabel(strategy.risk_level)}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50 text-xs px-1.5 py-0 h-4">
                    <Users className="w-2.5 h-2.5 mr-1" />
                    {strategy.squad_size} Agents
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
                      <YAxis
                        hide
                        domain={(() => {
                          const values = strategy.history.map(h => h.value);
                          const minValue = Math.min(...values);
                          const yMin = Math.max(0, minValue - 1000);
                          return [yMin, 'auto'];
                        })()}
                      />
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
                      APY
                    </div>
                    <div className={`flex items-center gap-0.5 ${isNegativeReturn ? 'text-red-400' : 'text-emerald-400'}`}>
                      <span className="text-xs">{strategy.annualized_return > 0 ? '+' : ''}{strategy.annualized_return.toFixed(2)}%</span>
                    </div>
                  </div>
                  <div className="bg-slate-800/30 rounded p-1.5">
                    <div className="text-xs text-slate-500 mb-0.5 flex items-center gap-1">
                      <Shield className="w-2.5 h-2.5 text-blue-400" />
                      Total Account Value
                    </div>
                    <div className="flex items-center gap-0.5 text-slate-300">
                      <span className="text-xs">${formatPoolSize(strategy.pool_size)}</span>
                    </div>
                  </div>
                  <div className="bg-slate-800/30 rounded p-1.5">
                    <div className="text-xs text-slate-500 mb-0.5">Total P&L</div>
                    <div className={`flex items-center gap-0.5 ${strategy.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      <Target className="w-2.5 h-2.5" />
                      <span className="text-xs">{strategy.total_pnl >= 0 ? '+' : ''}${strategy.total_pnl.toFixed(2)}</span>
                    </div>
                  </div>
                  <div className="bg-slate-800/30 rounded p-1.5">
                    <div className="text-xs text-slate-500 mb-0.5">Pool Size</div>
                    <div className="flex items-center gap-0.5 text-slate-300">
                      <span className="text-xs">{formatPoolSize(strategy.pool_size)}</span>
                    </div>
                  </div>
                </div>

                <Button
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600 border-0 shadow-lg shadow-purple-500/30 group-hover:shadow-purple-500/50 transition-shadow h-7 text-xs"
                  onClick={() => handleCardClick(strategy)}
                >
                  <Users className="w-3 h-3 mr-1.5" />
                  View Details
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Launch Strategy Modal */}
      <LaunchStrategyModal
        open={launchModalOpen}
        onOpenChange={setLaunchModalOpen}
        onSuccess={(portfolioId) => {
          // Reload strategies to show the new instance
          loadStrategies();
          // Navigate to the new portfolio
          onSelectStrategy(portfolioId);
        }}
      />
    </div>
  );
}
