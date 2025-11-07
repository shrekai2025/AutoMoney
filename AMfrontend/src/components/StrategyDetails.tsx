import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
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
  Coins,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import redCharacter from "figma:asset/e7df430614095df0bf6f8507a2c9ff6a9129eaaf.png";
import greenCharacter from "figma:asset/c5bd439c73b523a0fe77e12f24d55c9e5fb9c986.png";
import { fetchStrategyDetail } from "../lib/marketplaceApi";
import type { StrategyDetail } from "../types/strategy";
import { convertPerformanceHistory, getAgentIcon, getAgentColor } from "../utils/strategyUtils";
import { ExecutionDetailsModal } from "./ExecutionDetailsModal";
import { binancePriceService } from "../lib/binancePriceService";
import { useAuth } from "../contexts/AuthContext";

// Character avatars
const characters = [redCharacter, greenCharacter];

// Helper function to get consistent random character for each strategy
const getCharacterForStrategy = (strategyId: string) => {
  // Use hash of UUID to get consistent character
  const hash = strategyId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return characters[hash % characters.length];
};

interface StrategyDetailsProps {
  strategyId: string;
  onBack: () => void;
}

export function StrategyDetails({ strategyId, onBack }: StrategyDetailsProps) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [strategy, setStrategy] = useState<StrategyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBTC, setShowBTC] = useState(true);
  const [showETH, setShowETH] = useState(true);
  const [timeRange, setTimeRange] = useState("all");
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [livePrices, setLivePrices] = useState<Record<string, number>>({});
  const [squadDetailsExpanded, setSquadDetailsExpanded] = useState(false);

  // Load strategy details from API - only when authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      loadStrategyDetail();
    }
  }, [strategyId, authLoading, isAuthenticated]);

  // Update live prices every 5 seconds
  useEffect(() => {
    if (!strategy || strategy.holdings.length === 0) return;

    // 获取所有持仓的交易对符号
    const symbols = strategy.holdings.map(h => h.symbol);

    // 立即获取一次价格
    updateLivePrices(symbols);

    // 设置定时器每5秒更新一次
    const interval = setInterval(() => {
      updateLivePrices(symbols);
    }, 5000);

    return () => clearInterval(interval);
  }, [strategy]);

  async function updateLivePrices(symbols: string[]) {
    try {
      const prices: Record<string, number> = {};

      // 并行获取所有价格
      await Promise.all(
        symbols.map(async (symbol) => {
          try {
            const price = await binancePriceService.getPrice(symbol);
            prices[symbol] = price;
          } catch (err) {
            console.error(`Failed to fetch price for ${symbol}:`, err);
          }
        })
      );

      setLivePrices(prices);
    } catch (err) {
      console.error('Failed to update live prices:', err);
    }
  }

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

  // Show loading if auth is still loading
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p>Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Show error if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-red-400 mb-4">⚠️ Authentication Required</div>
          <p className="text-slate-400 text-sm mb-4">Please log in to view strategy details</p>
          <Button onClick={() => window.location.href = '/login'} className="bg-purple-600 hover:bg-purple-700">
            Go to Login
          </Button>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p>Loading strategy details...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !strategy) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-red-400 mb-4">⚠️ Error loading strategy</div>
          <p className="text-slate-400 text-sm mb-4">{error || 'Strategy not found'}</p>
          <Button onClick={loadStrategyDetail} className="bg-purple-600 hover:bg-purple-700">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  // Convert performance history data
  const performanceData = convertPerformanceHistory(strategy.performance_history);

  return (
    <div className="space-y-3">
      {/* Back Button and Header */}
      <div>
        <Button variant="ghost" onClick={onBack} className="gap-2 mb-3 text-slate-200 hover:text-white hover:bg-slate-800 h-7 px-2 text-xs">
          <ArrowLeft className="w-3 h-3" />
          Back to Recruitment
        </Button>
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h1 className="text-white text-xl font-semibold">{strategy.name}</h1>
              <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50 text-xs px-2 py-0.5">
                <Users className="w-3 h-3 mr-1" />
                {strategy.squad_agents.length} Agents
              </Badge>
            </div>
            <p className="text-slate-400 text-xs mb-2">{strategy.description}</p>
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
                {/* Conviction Badge */}
                <div className="absolute -bottom-1 -right-1 bg-gradient-to-r from-purple-600 to-pink-500 rounded-full px-2 py-0.5 text-xs font-bold shadow-lg">
                  {strategy.conviction_summary.score.toFixed(0)}%
                </div>
              </div>
            </div>

            {/* Manager Message */}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-white text-sm font-semibold">Manager Said:</h3>
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50 text-xs px-1.5 py-0 h-4">
                  <BarChart3 className="w-2.5 h-2.5 mr-1" />
                  Conviction: {strategy.conviction_summary.score.toFixed(0)}%
                </Badge>
              </div>
              <p className="text-slate-300 text-xs leading-relaxed mb-1">
                {strategy.conviction_summary.message}
              </p>
              <div className="text-slate-500 text-xs flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Updated: {new Date(strategy.conviction_summary.updated_at).toLocaleString()}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Squad Details (Mission + Roster) */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-0 pt-3 px-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white text-sm flex items-center gap-2">
              <Shield className="w-4 h-4 text-purple-400" />
              Squad Details
            </CardTitle>
            <button
              onClick={() => setSquadDetailsExpanded(!squadDetailsExpanded)}
              className="text-slate-400 hover:text-white transition-colors flex items-center gap-1 text-xs"
            >
              {squadDetailsExpanded ? (
                <>
                  <span>Show Less</span>
                  <ChevronUp className="w-3 h-3" />
                </>
              ) : (
                <>
                  <span>Show More</span>
                  <ChevronDown className="w-3 h-3" />
                </>
              )}
            </button>
          </div>
        </CardHeader>
        <CardContent className="px-3 pb-3 pt-0">
          {/* Mission Section */}
          <div className="mb-4">
            <div className="relative">
              <div
                className={`text-slate-400 text-xs leading-relaxed overflow-hidden ${
                  squadDetailsExpanded ? '' : 'line-clamp-3'
                }`}
                style={{
                  display: '-webkit-box',
                  WebkitBoxOrient: 'vertical',
                  ...(squadDetailsExpanded ? {} : { WebkitLineClamp: 3 })
                }}
              >
                {strategy.philosophy}
              </div>
              {!squadDetailsExpanded && (
                <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-slate-900/50 to-transparent pointer-events-none" />
              )}
            </div>
          </div>

          {/* Roster Section */}
          <div>
            <div className="text-slate-500 text-xs mb-2 font-medium">Squad Roster</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {strategy.squad_agents.map((agent, index) => {
                const Icon = getAgentIcon(agent.role);
                const color = getAgentColor(agent.role);

                // Map to Tailwind classes instead of inline styles
                const colorClasses: Record<string, { bg: string, border: string, text: string, badgeBg: string }> = {
                  'purple': {
                    bg: 'bg-purple-500/20',
                    border: 'border-purple-500/50',
                    text: 'text-purple-400',
                    badgeBg: 'bg-purple-500/20'
                  },
                  'blue': {
                    bg: 'bg-blue-500/20',
                    border: 'border-blue-500/50',
                    text: 'text-blue-400',
                    badgeBg: 'bg-blue-500/20'
                  },
                  'emerald': {
                    bg: 'bg-emerald-500/20',
                    border: 'border-emerald-500/50',
                    text: 'text-emerald-400',
                    badgeBg: 'bg-emerald-500/20'
                  },
                  'amber': {
                    bg: 'bg-amber-500/20',
                    border: 'border-amber-500/50',
                    text: 'text-amber-400',
                    badgeBg: 'bg-amber-500/20'
                  },
                  'red': {
                    bg: 'bg-red-500/20',
                    border: 'border-red-500/50',
                    text: 'text-red-400',
                    badgeBg: 'bg-red-500/20'
                  },
                  'slate': {
                    bg: 'bg-slate-500/20',
                    border: 'border-slate-500/50',
                    text: 'text-slate-400',
                    badgeBg: 'bg-slate-500/20'
                  }
                };

                const classes = colorClasses[color] || colorClasses['slate'];

                return (
                  <div
                    key={index}
                    className="bg-slate-800/30 rounded px-2.5 py-1.5 border border-slate-700/50 hover:border-purple-500/30 transition-all"
                  >
                    <div className="flex items-center gap-2">
                      <div className={`w-6 h-6 rounded flex items-center justify-center border flex-shrink-0 ${classes.bg} ${classes.border}`}>
                        <Icon className={`w-3.5 h-3.5 ${classes.text}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-white text-xs font-medium truncate">{agent.name}</div>
                      </div>
                      <Badge className={`text-xs px-1.5 py-0.5 h-auto flex-shrink-0 border font-medium ${classes.badgeBg} ${classes.text} ${classes.border}`}>
                        {agent.weight}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Chart */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-0 pt-3 px-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-purple-400" />
              Performance vs Benchmarks
            </CardTitle>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1">
                <Checkbox
                  id="showBTC"
                  checked={showBTC}
                  onCheckedChange={(checked) => setShowBTC(checked as boolean)}
                  className="w-3 h-3 data-[state=checked]:bg-amber-500 data-[state=checked]:border-amber-500"
                />
                <label htmlFor="showBTC" className="text-xs text-slate-400 cursor-pointer">BTC</label>
              </div>
              <div className="flex items-center gap-1">
                <Checkbox
                  id="showETH"
                  checked={showETH}
                  onCheckedChange={(checked) => setShowETH(checked as boolean)}
                  className="w-3 h-3 data-[state=checked]:bg-emerald-500 data-[state=checked]:border-emerald-500"
                />
                <label htmlFor="showETH" className="text-xs text-slate-400 cursor-pointer">ETH</label>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="px-3 pb-3 pt-0">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="date"
                stroke="#64748b"
                style={{ fontSize: "10px" }}
                tick={{ fill: "#64748b" }}
              />
              <YAxis
                stroke="#64748b"
                style={{ fontSize: "10px" }}
                tick={{ fill: "#64748b" }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  fontSize: "11px",
                }}
                labelStyle={{ color: "#cbd5e1" }}
              />
              <Legend
                wrapperStyle={{ fontSize: "11px" }}
                iconType="line"
              />
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
        </CardContent>
      </Card>

      {/* Current Holdings */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-0 pt-3 px-3">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <Coins className="w-4 h-4 text-purple-400" />
            Current Holdings
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3 pt-0">
          {strategy.holdings.length === 0 ? (
            <div className="text-center py-4 text-slate-400 text-xs">
              No holdings yet. Strategy will execute trades based on market conditions.
            </div>
          ) : (
            <div className="space-y-2">
              {strategy.holdings.map((holding, index) => {
                // 使用实时价格或后端返回的价格
                const currentPrice = livePrices[holding.symbol] || holding.current_price;
                const marketValue = holding.amount * currentPrice;
                const unrealizedPnl = marketValue - holding.cost_basis;
                const unrealizedPnlPercent = holding.cost_basis > 0
                  ? (unrealizedPnl / holding.cost_basis) * 100
                  : 0;

                return (
                  <div
                    key={index}
                    className="bg-slate-800/30 rounded p-2.5 border border-slate-700/50 hover:border-purple-500/50 transition-all"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/50 text-xs px-2 py-0.5 h-5 font-bold">
                          {holding.symbol}
                        </Badge>
                        <span className="text-slate-400 text-xs">
                          {holding.amount.toFixed(8)}
                        </span>
                      </div>
                      <div className={`text-sm font-mono font-semibold ${
                        unrealizedPnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {unrealizedPnl >= 0 ? '+' : ''}${unrealizedPnl.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        })}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-1.5">
                      <div>
                        <div className="text-xs text-slate-500">Avg Buy</div>
                        <div className="text-white text-xs font-medium">
                          ${holding.avg_buy_price.toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Current</div>
                        <div className="text-white text-xs font-medium flex items-center gap-1">
                          ${currentPrice.toLocaleString()}
                          {livePrices[holding.symbol] && (
                            <span className="text-emerald-400 text-xs">●</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Value</div>
                        <div className="text-white text-xs font-medium">
                          ${marketValue.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                          })}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">P&L %</div>
                        <div className={`text-xs font-medium ${
                          unrealizedPnlPercent >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          {unrealizedPnlPercent >= 0 ? '+' : ''}{unrealizedPnlPercent.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
              {/* Total Summary */}
              <div className="bg-purple-900/20 rounded p-2.5 border border-purple-500/30 mt-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-400 mb-0.5">Portfolio Summary</div>
                    <div className="flex items-center gap-3">
                      <div>
                        <span className="text-xs text-slate-500">Cash: </span>
                        <span className="text-white text-xs font-medium">
                          ${strategy.current_balance.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                          })}
                        </span>
                      </div>
                      <div>
                        <span className="text-xs text-slate-500">Total Unrealized P&L: </span>
                        <span className={`text-xs font-semibold ${
                          (() => {
                            // 计算总的未实现盈亏（使用实时价格）
                            const totalUnrealizedPnl = strategy.holdings.reduce((sum, holding) => {
                              const currentPrice = livePrices[holding.symbol] || holding.current_price;
                              const marketValue = holding.amount * currentPrice;
                              const unrealizedPnl = marketValue - holding.cost_basis;
                              return sum + unrealizedPnl;
                            }, 0);
                            return totalUnrealizedPnl >= 0 ? 'text-emerald-400' : 'text-red-400';
                          })()
                        }`}>
                          {(() => {
                            const totalUnrealizedPnl = strategy.holdings.reduce((sum, holding) => {
                              const currentPrice = livePrices[holding.symbol] || holding.current_price;
                              const marketValue = holding.amount * currentPrice;
                              const unrealizedPnl = marketValue - holding.cost_basis;
                              return sum + unrealizedPnl;
                            }, 0);
                            return `${totalUnrealizedPnl >= 0 ? '+' : ''}$${totalUnrealizedPnl.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2
                            })}`;
                          })()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-0 pt-3 px-3">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-400" />
            Performance Metrics
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3 pt-0">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            <div className="bg-slate-800/30 rounded p-2">
              <div className="text-xs text-slate-500 mb-0.5">Annualized Return</div>
              <div className={`text-base font-semibold ${strategy.performance_metrics.annualized_return > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {strategy.performance_metrics.annualized_return > 0 ? '+' : ''}{strategy.performance_metrics.annualized_return.toFixed(2)}%
              </div>
            </div>

            <div className="bg-slate-800/30 rounded p-2">
              <div className="text-xs text-slate-500 mb-0.5">Max Drawdown</div>
              <div className="text-base font-semibold text-red-400">
                {strategy.performance_metrics.max_drawdown.toFixed(2)}%
              </div>
            </div>

            <div className="bg-slate-800/30 rounded p-2">
              <div className="text-xs text-slate-500 mb-0.5">Sharpe Ratio</div>
              <div className="text-base font-semibold text-slate-300">
                {strategy.performance_metrics.sharpe_ratio.toFixed(2)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Squad Actions */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-0 pt-3 px-3">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <Activity className="w-4 h-4 text-purple-400" />
            Recent Squad Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3 pt-0">
          <div className="space-y-1.5">
            {strategy.recent_activities.map((activity, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 bg-slate-800/30 rounded border border-slate-700/50 hover:border-purple-500/50 transition-all"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50 text-xs px-1.5 py-0 h-4">
                      {activity.agent}
                    </Badge>
                    <span className="text-xs text-slate-500">
                      {new Date(activity.date).toLocaleString(undefined, {
                        year: 'numeric',
                        month: 'numeric',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                  <div className="text-white text-xs mb-0.5">
                    Signal: <span className="text-slate-300">{activity.signal}</span>
                  </div>
                  <div className="text-xs text-slate-400">Action: {activity.action}</div>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className={`text-sm font-mono font-semibold ${
                      activity.result.startsWith("+") ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {activity.result}
                  </div>
                  {activity.execution_id && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedExecutionId(activity.execution_id!)}
                      className="h-7 px-2 text-xs bg-purple-500/10 border-purple-500/50 text-purple-400 hover:bg-purple-500/20"
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      View
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Strategy Parameters */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-0 pt-3 px-3">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <Info className="w-4 h-4 text-purple-400" />
            Strategy Parameters
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3 pt-0">
          <div className="space-y-1.5">
            {Object.entries(strategy.parameters).map(([key, value]) => (
              <div key={key} className="flex justify-between bg-slate-800/30 rounded p-2 border border-slate-700/50">
                <span className="text-slate-400 text-xs capitalize">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="text-slate-200 text-xs font-medium">{value}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Execution Details Modal */}
      <ExecutionDetailsModal
        executionId={selectedExecutionId}
        onClose={() => setSelectedExecutionId(null)}
      />
    </div>
  );
}
