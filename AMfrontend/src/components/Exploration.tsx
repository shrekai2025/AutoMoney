import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { ScrollArea } from "./ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { TrendingUp, TrendingDown, Activity, Shield, Zap, Eye, Database, Target, ExternalLink } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import aiCommanderImage from "figma:asset/c5bd439c73b523a0fe77e12f24d55c9e5fb9c986.png";

// Mock real-time data
const generateScore = (base: number) => {
  return base + (Math.random() - 0.5) * 0.3;
};

export function Exploration() {
  const [macroScore, setMacroScore] = useState(0.8);
  const [onChainScore, setOnChainScore] = useState(0.7);
  const [taScore, setTaScore] = useState(0.5);
  const [convictionScore, setConvictionScore] = useState(75);
  const [countdown, setCountdown] = useState(5750);

  // Simulate real-time score updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMacroScore(generateScore(0.8));
      setOnChainScore(generateScore(0.7));
      setTaScore(generateScore(0.5));
      setConvictionScore(Math.floor(70 + Math.random() * 10));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => (prev > 0 ? prev - 1 : 14400));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const getConvictionColor = (score: number) => {
    if (score > 70) return "from-emerald-500 to-green-400";
    if (score > 40) return "from-amber-500 to-yellow-400";
    return "from-red-500 to-rose-400";
  };

  const getConvictionAnimation = (score: number) => {
    if (score > 70) return "animate-pulse";
    if (score > 40) return "";
    return "animate-pulse";
  };

  const feedData = [
    { type: "Macro", text: "CME Rate Prob: 80%", trend: "up" },
    { type: "OnChain", text: "LTH Change: +2.01%", trend: "up" },
    { type: "TA", text: "BTC RSI(14): 75.25", trend: "neutral" },
    { type: "Risk", text: "ATR Volatility: 6.1% [High Freq]", trend: "down" },
    { type: "Macro", text: "ETF Net Flow: +$250M", trend: "up" },
    { type: "OnChain", text: "Exchange Flow: -10,000 BTC", trend: "up" },
    { type: "TA", text: "Golden Cross Active", trend: "up" },
    { type: "Sentiment", text: "Fear & Greed: 20 [Extreme Fear]", trend: "down" },
  ];

  const tweets = [
    { author: "@SEC_Chairman", text: "Digital asset enforcement will continue to be a priority...", time: "Just Now" },
    { author: "@realDonaldTrump", text: "Big announcement coming about the economy...", time: "5m ago" },
    { author: "@a16zCrypto", text: "Layer 2 scaling is the next wave.", time: "10m ago" },
    { author: "@VitalikButerin", text: "Excited about the progress on zkEVM technology...", time: "15m ago" },
    { author: "@CathieDWood", text: "Bitcoin remains our conviction buy for 2025.", time: "20m ago" },
  ];

  // Mock historical directives data
  const generateHistoricalDirectives = () => {
    const directives = [];
    const strategies = [
      { name: "HODL-Wave Squad", subtitle: "Macro Swing Strategy" },
      { name: "ArbitrageX Squad", subtitle: "High-Frequency Trading" },
      { name: "MomentumPro Squad", subtitle: "Trend Following" },
      { name: "StableGuard Squad", subtitle: "Stable Yield Strategy" },
      { name: "DeFiYield Squad", subtitle: "Yield Optimizer" },
      { name: "AIPredict Squad", subtitle: "Predictive Trading" },
    ];
    
    const actions = [
      { type: "BUY", asset: "BTC", amount: "0.75%", sentiment: "bullish" },
      { type: "BUY", asset: "ETH", amount: "0.5%", sentiment: "bullish" },
      { type: "SELL", asset: "BTC", amount: "0.3%", sentiment: "bearish" },
      { type: "SELL", asset: "ETH", amount: "0.4%", sentiment: "bearish" },
      { type: "HOLD", asset: "-", amount: "-", sentiment: "neutral" },
    ];

    const statuses = ["Accelerate Accumulation", "Reduce Exposure", "Hold Position", "Defensive Mode", "Rebalance"];
    
    for (let i = 0; i < 100; i++) {
      const strategy = strategies[Math.floor(Math.random() * strategies.length)];
      const action = actions[Math.floor(Math.random() * actions.length)];
      const status = statuses[Math.floor(Math.random() * statuses.length)];
      const conviction = Math.floor(Math.random() * 100);
      const hoursAgo = i * 4; // Every 4 hours
      
      directives.push({
        id: i,
        timestamp: `${Math.floor(hoursAgo / 24)}d ${hoursAgo % 24}h ago`,
        strategy: strategy.name,
        strategySubtitle: strategy.subtitle,
        status: status,
        action: action,
        conviction: conviction,
        result: (Math.random() - 0.4) * 5 // Random result between -2% and +3%
      });
    }
    
    return directives;
  };

  const historicalDirectives = generateHistoricalDirectives();

  return (
    <div className="space-y-3">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div className="flex-1">
          <h1 className="text-white mb-1 text-xl flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            Exploration Hub
          </h1>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-xs">Currently focused on:</span>
            <Select defaultValue="hodl-wave" disabled={false}>
              <SelectTrigger className="w-[180px] h-6 text-xs bg-slate-800/50 border-slate-700 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="hodl-wave" className="text-xs text-white">
                  <div className="flex items-center gap-2">
                    <span>HODL-Wave Squad</span>
                  </div>
                </SelectItem>
                <SelectItem value="arbitrage" disabled className="text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <span>ArbitrageX Squad</span>
                    <Badge className="bg-slate-700 text-slate-500 text-xs px-1 py-0">Locked</Badge>
                  </div>
                </SelectItem>
                <SelectItem value="momentum" disabled className="text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <span>MomentumPro Squad</span>
                    <Badge className="bg-slate-700 text-slate-500 text-xs px-1 py-0">Locked</Badge>
                  </div>
                </SelectItem>
                <SelectItem value="stable" disabled className="text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <span>StableGuard Squad</span>
                    <Badge className="bg-slate-700 text-slate-500 text-xs px-1 py-0">Locked</Badge>
                  </div>
                </SelectItem>
                <SelectItem value="defi" disabled className="text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <span>DeFiYield Squad</span>
                    <Badge className="bg-slate-700 text-slate-500 text-xs px-1 py-0">Locked</Badge>
                  </div>
                </SelectItem>
                <SelectItem value="ai" disabled className="text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <span>AIPredict Squad</span>
                    <Badge className="bg-slate-700 text-slate-500 text-xs px-1 py-0">Locked</Badge>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="relative">
          <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50 text-sm px-3 py-1.5 shadow-lg shadow-blue-500/50" style={{ animation: 'breath 2s ease-in-out infinite' }}>
            <div className="relative flex items-center gap-2">
              <div className="relative">
                <span className="w-2.5 h-2.5 bg-blue-400 rounded-full block"></span>
                <span className="absolute inset-0 w-2.5 h-2.5 bg-blue-400 rounded-full" style={{ animation: 'pulse-ring 1.5s ease-out infinite' }}></span>
              </div>
              <span className="font-semibold">LIVE</span>
            </div>
          </Badge>
        </div>
      </div>

      {/* Three Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
        {/* LEFT: Agents - Squad Decision Core */}
        <div className="lg:col-span-4 space-y-3">
          <div className="text-white text-sm mb-2 flex items-center gap-2">
            <Shield className="w-4 h-4 text-purple-400" />
            <span>Squad Decision Core</span>
          </div>

          {/* MacroAgent - The Oracle */}
          <Card className="bg-slate-900/50 border-blue-500/30 backdrop-blur-sm hover:border-blue-500/50 transition-all relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <CardHeader className="pb-2 pt-3 px-3">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/50 relative">
                  <Eye className="w-5 h-5 text-white" />
                  <div className="absolute inset-0 bg-blue-400/30 rounded-lg animate-pulse"></div>
                </div>
                <div className="flex-1">
                  <CardTitle className="text-white text-xs">The Oracle</CardTitle>
                  <p className="text-slate-500 text-xs">MacroAgent (40%)</p>
                </div>
                <div className={`text-right ${macroScore > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  <div className="text-sm font-mono">{macroScore > 0 ? '+' : ''}{macroScore.toFixed(2)}</div>
                  <div className="text-xs text-slate-500">Score</div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="px-3 pb-3 space-y-2">
              {/* Core Inputs */}
              <div className="space-y-1.5">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">ETF Net Flow</span>
                    <span className="text-emerald-400">+$250M</span>
                  </div>
                  <Progress value={75} className="h-1.5 bg-slate-800" />
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Fed Cut Prob</span>
                    <span className="text-blue-400">80%</span>
                  </div>
                  <Progress value={80} className="h-1.5 bg-slate-800" />
                </div>
              </div>
              
              {/* LLM Conclusion */}
              <div className="bg-slate-800/50 rounded p-2 border border-slate-700/50">
                <p className="text-xs text-slate-300 leading-relaxed">
                  "Global liquidity easing expectations strong, institutional funds continue to flow in."
                </p>
              </div>
            </CardContent>
          </Card>

          {/* OnChainAgent - Data Warden */}
          <Card className="bg-slate-900/50 border-emerald-500/30 backdrop-blur-sm hover:border-emerald-500/50 transition-all relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <CardHeader className="pb-2 pt-3 px-3">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/50 relative">
                  <Database className="w-5 h-5 text-white" />
                  <div className="absolute inset-0 bg-emerald-400/30 rounded-lg animate-pulse"></div>
                </div>
                <div className="flex-1">
                  <CardTitle className="text-white text-xs">Data Warden</CardTitle>
                  <p className="text-slate-500 text-xs">OnChainAgent (40%)</p>
                </div>
                <div className={`text-right ${onChainScore > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  <div className="text-sm font-mono">{onChainScore > 0 ? '+' : ''}{onChainScore.toFixed(2)}</div>
                  <div className="text-xs text-slate-500">Score</div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="px-3 pb-3 space-y-2">
              {/* Core Inputs */}
              <div className="space-y-1.5">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">MVRV Z-Score</span>
                    <span className="text-amber-400">2.5</span>
                  </div>
                  <Progress value={60} className="h-1.5 bg-slate-800" />
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Exchange Flow</span>
                    <span className="text-emerald-400">-10K BTC</span>
                  </div>
                  <Progress value={85} className="h-1.5 bg-slate-800" />
                </div>
              </div>
              
              {/* LLM Conclusion */}
              <div className="bg-slate-800/50 rounded p-2 border border-slate-700/50">
                <p className="text-xs text-slate-300 leading-relaxed">
                  "On-chain activity healthy, long-term holder accumulation signal strong."
                </p>
              </div>
            </CardContent>
          </Card>

          {/* TAAgent - Momentum Scout */}
          <Card className="bg-slate-900/50 border-amber-500/30 backdrop-blur-sm hover:border-amber-500/50 transition-all relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <CardHeader className="pb-2 pt-3 px-3">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center shadow-lg shadow-amber-500/50 relative">
                  <Zap className="w-5 h-5 text-white" />
                  <div className="absolute inset-0 bg-amber-400/30 rounded-lg animate-pulse"></div>
                </div>
                <div className="flex-1">
                  <CardTitle className="text-white text-xs">Momentum Scout</CardTitle>
                  <p className="text-slate-500 text-xs">TAAgent (20%)</p>
                </div>
                <div className={`text-right ${taScore > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  <div className="text-sm font-mono">{taScore > 0 ? '+' : ''}{taScore.toFixed(2)}</div>
                  <div className="text-xs text-slate-500">Score</div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="px-3 pb-3 space-y-2">
              {/* Core Inputs */}
              <div className="space-y-1.5">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">RSI(14)</span>
                    <span className="text-amber-400">75</span>
                  </div>
                  <Progress value={75} className="h-1.5 bg-slate-800" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Trend Status</span>
                  <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50 text-xs px-2 py-0">
                    Golden Cross
                  </Badge>
                </div>
              </div>
              
              {/* LLM Conclusion */}
              <div className="bg-slate-800/50 rounded p-2 border border-slate-700/50">
                <p className="text-xs text-slate-300 leading-relaxed">
                  "Technical trend bullish, but short-term overbought risk requires caution."
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* MIDDLE: AI Commander Analysis */}
        <div className="lg:col-span-4 space-y-3">
          <div className="text-white text-sm mb-2 flex items-center gap-2">
            <Target className="w-4 h-4 text-emerald-400" />
            <span>AI Commander</span>
          </div>

          {/* AI Commander Card */}
          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-emerald-500/30 backdrop-blur-sm relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-cyan-500/10"></div>
            <CardHeader className="pb-2 pt-3 px-3 relative">
              <CardTitle className="text-white text-sm text-center">Squad Commander</CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3 relative">
              {/* AI Avatar */}
              <div className="flex justify-center mb-3">
                <div className="relative">
                  <div className="w-32 h-32 rounded-full overflow-hidden bg-gradient-to-br from-emerald-400 to-cyan-500 p-0.5 shadow-2xl shadow-emerald-500/50">
                    <div className="w-full h-full rounded-full overflow-hidden bg-black flex items-center justify-center">
                      <ImageWithFallback 
                        src={aiCommanderImage}
                        alt="AI Commander"
                        className="w-full h-full object-contain"
                      />
                    </div>
                  </div>
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-400 rounded-full animate-pulse"></div>
                  <div className="absolute -bottom-1 -left-1">
                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50 text-xs px-2 py-0.5">
                      ONLINE
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Commander Name */}
              <div className="text-center mb-3">
                <h3 className="text-white text-sm mb-0.5">Commander Nova</h3>
                <p className="text-slate-400 text-xs">AI Strategy Coordinator</p>
              </div>

              {/* Market Analysis */}
              <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50 mb-3">
                <div className="text-xs text-slate-400 mb-2">Market Analysis Summary:</div>
                <div className="text-xs text-slate-200 leading-relaxed">
                  "Current market conditions are highly favorable. Our macro indicators show strong institutional inflows with ETF net flow at +$250M. 
                  On-chain metrics reveal robust accumulation by long-term holders with -10K BTC leaving exchanges. 
                  Technical momentum remains bullish despite short-term overbought signals. 
                  <span className="text-emerald-400 font-medium"> Overall conviction: STRONG BUY.</span>"
                </div>
              </div>

              {/* Conviction Score Badge */}
              <div className="flex items-center justify-center gap-2">
                <div className="text-center">
                  <div className="text-2xl font-bold text-emerald-400 mb-0.5">{convictionScore}</div>
                  <div className="text-xs text-slate-400">Conviction</div>
                </div>
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50 text-xs px-3 py-1">
                  🔥 Strong
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Current Directive */}
          <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
            <CardHeader className="pb-2 pt-3 px-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-white text-sm">Active Directive</CardTitle>
                <Dialog>
                  <DialogTrigger asChild>
                    <button className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors">
                      View All
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </DialogTrigger>
                  <DialogContent className="bg-slate-900 border-slate-700 max-w-2xl max-h-[80vh]">
                    <DialogHeader>
                      <DialogTitle className="text-white">Directive History</DialogTitle>
                      <p className="text-slate-400 text-xs">Last 100 squad directives across all strategies</p>
                    </DialogHeader>
                    <ScrollArea className="h-[60vh] pr-4">
                      <div className="space-y-2">
                        {historicalDirectives.map((directive) => (
                          <div
                            key={directive.id}
                            className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-3 hover:bg-slate-800/70 transition-colors"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50 text-xs px-2 py-0">
                                    {directive.strategy}
                                  </Badge>
                                  <span className="text-xs text-slate-500">{directive.timestamp}</span>
                                </div>
                                <div className="text-xs text-slate-400 mb-1">{directive.strategySubtitle}</div>
                              </div>
                              <Badge className={`text-xs px-2 py-0 ${
                                directive.conviction > 70 
                                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
                                  : directive.conviction > 40
                                  ? 'bg-amber-500/20 text-amber-400 border-amber-500/50'
                                  : 'bg-red-500/20 text-red-400 border-red-500/50'
                              }`}>
                                {directive.conviction}
                              </Badge>
                            </div>
                            
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className={`text-xs ${
                                  directive.action.sentiment === 'bullish' 
                                    ? 'text-emerald-400' 
                                    : directive.action.sentiment === 'bearish'
                                    ? 'text-red-400'
                                    : 'text-slate-400'
                                }`}>
                                  {directive.status}
                                </span>
                                <span className="text-slate-600">•</span>
                                <span className="text-xs text-white">
                                  {directive.action.type} {directive.action.amount !== '-' && <span className="text-slate-400">{directive.action.amount}</span>} {directive.action.asset}
                                </span>
                              </div>
                              <span className={`text-xs font-mono ${
                                directive.result >= 0 ? 'text-emerald-400' : 'text-red-400'
                              }`}>
                                {directive.result >= 0 ? '+' : ''}{directive.result.toFixed(2)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent className="px-3 pb-3 space-y-2">
              {/* Strategy Info */}
              <div className="flex items-center gap-2 mb-1">
                <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50 text-xs px-2 py-0.5">
                  HODL-Wave Squad
                </Badge>
                <span className="text-xs text-slate-500">Macro Swing Strategy</span>
              </div>

              {/* Countdown */}
              <div className="bg-slate-800/50 rounded p-2 border border-slate-700/50">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-slate-400">Next Update In:</span>
                  <Badge className="bg-cyan-500/20 text-cyan-400 border-cyan-500/50 text-xs px-2 py-0 font-mono">
                    {formatTime(countdown)}
                  </Badge>
                </div>
                <Progress value={(countdown / 14400) * 100} className="h-1.5 bg-slate-700" />
              </div>

              {/* Current Action */}
              <div className="bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 rounded-lg p-2.5 border border-emerald-500/30">
                <div className="text-center mb-2">
                  <div className="text-emerald-400 text-xs mb-1 tracking-wider uppercase flex items-center justify-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5" />
                    Accelerate Accumulation
                  </div>
                </div>
                
                <div className="bg-slate-900/50 rounded p-2 mb-1.5">
                  <div className="text-center text-white text-sm">
                    BUY <span className="text-emerald-400">0.75%</span> BTC
                  </div>
                </div>

                <div className="text-xs text-slate-300 text-center">
                  All agents aligned • Maximum confidence deployment
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* RIGHT: Intel - Real-Time Intelligence */}
        <div className="lg:col-span-4 space-y-3">
          <div className="text-white text-sm mb-2 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span>Real-Time Intel</span>
          </div>

          {/* Sentiment Tower */}
          <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
            <CardHeader className="pb-2 pt-3 px-3">
              <CardTitle className="text-white text-xs">Sentiment Filter</CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400">Fear & Greed Index</span>
                <Badge className="bg-red-500/20 text-red-400 border-red-500/50 text-xs px-2 py-0">
                  20 - Extreme Fear
                </Badge>
              </div>
              <Progress value={20} className="h-2 bg-slate-800 mb-2" />
              <div className="bg-amber-500/10 border border-amber-500/50 rounded p-2">
                <p className="text-xs text-amber-300">
                  ⚠️ Sentiment Filter Active: Extreme fear detected, strategy conservatively de-weighted by 10%.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Data Stream */}
          <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
            <CardHeader className="pb-2 pt-3 px-3">
              <CardTitle className="text-white text-xs flex items-center justify-between">
                <span>Matrix Data Flow</span>
                <span className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></span>
              </CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3">
              <ScrollArea className="h-48 bg-black/30 rounded p-2 font-mono text-xs">
                <div className="space-y-1">
                  {feedData.map((item, index) => (
                    <div key={index} className="flex items-center gap-2 text-cyan-400/80 hover:text-cyan-400 transition-colors">
                      <span className="text-slate-600">[{item.type}]</span>
                      <span className="flex-1">{item.text}</span>
                      {item.trend === 'up' && <TrendingUp className="w-3 h-3 text-emerald-400" />}
                      {item.trend === 'down' && <TrendingDown className="w-3 h-3 text-red-400" />}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Twitter Feed */}
          <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
            <CardHeader className="pb-2 pt-3 px-3">
              <CardTitle className="text-white text-xs">External Intelligence Feed</CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3">
              <ScrollArea className="h-56">
                <div className="space-y-2">
                  {tweets.map((tweet, index) => (
                    <div key={index} className="bg-slate-800/30 rounded p-2 border border-slate-700/50 hover:border-slate-600/50 transition-colors">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-blue-400">{tweet.author}</span>
                        <span className="text-xs text-slate-500">{tweet.time}</span>
                      </div>
                      <p className="text-xs text-slate-300">{tweet.text}</p>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
