import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { ScrollArea } from "./ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { Skeleton } from "./ui/skeleton";
import { TrendingUp, TrendingDown, Activity, Shield, Zap, Eye, Database, Target, ExternalLink } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import aiCommanderImage from "figma:asset/c5bd439c73b523a0fe77e12f24d55c9e5fb9c986.png";
import { explorationApi, type SquadDecisionCore, type CommanderAnalysis, type ActiveDirective, type DirectiveHistory, type DataStream, type AvailableStrategies } from "../lib/explorationApi";

export function Exploration() {
  // API数据状态
  const [squadData, setSquadData] = useState<SquadDecisionCore | null>(null);
  const [commanderData, setCommanderData] = useState<CommanderAnalysis | null>(null);
  const [directiveData, setDirectiveData] = useState<ActiveDirective | null>(null);
  const [directiveHistory, setDirectiveHistory] = useState<DirectiveHistory | null>(null);
  const [dataStream, setDataStream] = useState<DataStream | null>(null);
  const [availableStrategies, setAvailableStrategies] = useState<AvailableStrategies | null>(null);
  
  // UI状态
  const [selectedStrategyId, setSelectedStrategyId] = useState<number | undefined>(undefined);
  const [isLive, setIsLive] = useState(false);
  const [lastPollTime, setLastPollTime] = useState<Date | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // 加载策略列表（不依赖selectedStrategyId）
  const loadStrategies = useCallback(async () => {
    try {
      const strategies = await explorationApi.getAvailableStrategies();
      setAvailableStrategies(strategies);
      
      // 如果还没有选择策略，默认选择第一个
      if (strategies.strategies.length > 0) {
        setSelectedStrategyId((prev) => prev || strategies.strategies[0].id);
      }
    } catch (error) {
      console.error('Failed to load strategies:', error);
    }
  }, []);
  
  // 首次加载策略列表
  useEffect(() => {
    loadStrategies();
  }, [loadStrategies]);

  // 30秒轮询刷新函数
  const pollData = useCallback(async () => {
    // 如果没有选择策略，不发送请求
    if (!selectedStrategyId) {
      return;
    }
    
    try {
      setPollError(null);
      const startTime = new Date();
      
      // 并行获取所有数据（不包括策略列表，策略列表单独加载）
      const [squad, commander, directive, history, stream] = await Promise.all([
        explorationApi.getSquadDecisionCore(),
        explorationApi.getCommanderAnalysis(selectedStrategyId),
        explorationApi.getActiveDirective(selectedStrategyId),
        explorationApi.getDirectiveHistory(selectedStrategyId, 100),
        explorationApi.getDataStream(),
      ]);
      
      setSquadData(squad);
      setCommanderData(commander);
      setDirectiveData(directive);
      setDirectiveHistory(history);
      setDataStream(stream);
      
      setLastPollTime(startTime);
      setIsLive(true); // 轮询成功，显示LIVE状态
      setIsLoading(false); // 首次加载完成
    } catch (error) {
      console.error('Polling error:', error);
      setPollError(error instanceof Error ? error.message : 'Unknown error');
      setIsLive(false); // 轮询失败，隐藏LIVE状态
      setIsLoading(false); // 即使出错也停止loading
    }
  }, [selectedStrategyId]);

  // 初始加载和30秒轮询
  useEffect(() => {
    // 只有在选择了策略后才开始轮询
    if (!selectedStrategyId) {
      return;
    }
    
    // 立即执行一次
    pollData();
    
    // 设置30秒轮询
    const interval = setInterval(() => {
      pollData();
    }, 30000); // 30秒

    return () => clearInterval(interval);
  }, [pollData, selectedStrategyId]);

  // 本地倒计时状态（每秒更新）
  const [localCountdown, setLocalCountdown] = useState<{ formatted: string; progress: number } | null>(null);
  
  // 倒计时本地更新（每秒更新一次，基于API返回的execution_time和countdown）
  useEffect(() => {
    if (!directiveData?.execution_time || !directiveData?.countdown) {
      setLocalCountdown(null);
      return;
    }
    
    const updateCountdown = () => {
      const executionTime = new Date(directiveData.execution_time!);
      const now = new Date();
      
      // 从API返回的countdown获取remaining_seconds，计算period_seconds
      const remainingSeconds = directiveData.countdown.remaining_seconds;
      const elapsed = Math.floor((now.getTime() - executionTime.getTime()) / 1000);
      const periodSeconds = elapsed + remainingSeconds; // 总周期 = 已过时间 + 剩余时间
      
      // 重新计算剩余时间（基于当前时间）
      const remaining = Math.max(0, periodSeconds - elapsed);
      
      const hours = Math.floor(remaining / 3600);
      const minutes = Math.floor((remaining % 3600) / 60);
      const seconds = remaining % 60;
      
      const formatted = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      const progress = periodSeconds > 0 ? Math.min(100, (elapsed / periodSeconds) * 100) : 0;
      
      setLocalCountdown({ formatted, progress });
    };
    
    // 立即更新一次
    updateCountdown();
    
    // 每秒更新
    const timer = setInterval(updateCountdown, 1000);

    return () => clearInterval(timer);
  }, [directiveData]);

  // 假数据：Twitter Feed（暂时不接真实数据）
  const tweets = [
    { author: "@SEC_Chairman", text: "Digital asset enforcement will continue to be a priority...", time: "Just Now" },
    { author: "@realDonaldTrump", text: "Big announcement coming about the economy...", time: "5m ago" },
    { author: "@a16zCrypto", text: "Layer 2 scaling is the next wave.", time: "10m ago" },
    { author: "@VitalikButerin", text: "Excited about the progress on zkEVM technology...", time: "15m ago" },
    { author: "@CathieDWood", text: "Bitcoin remains our conviction buy for 2025.", time: "20m ago" },
  ];

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
            {availableStrategies && availableStrategies.strategies.length > 0 ? (
              <Select 
                value={selectedStrategyId?.toString() || availableStrategies.strategies[0].id.toString()} 
                onValueChange={(value) => {
                  setSelectedStrategyId(parseInt(value));
                }}
              >
                <SelectTrigger className="w-[180px] h-6 text-xs bg-slate-800/50 border-slate-700 text-white">
                  <SelectValue placeholder="Select a strategy" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  {availableStrategies.strategies.map((strategy) => (
                    <SelectItem 
                      key={strategy.id} 
                      value={strategy.id.toString()} 
                      className="text-xs text-white"
                    >
                      <div className="flex items-center gap-2">
                        <span>{strategy.display_name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <span className="text-slate-500 text-xs">No strategies available</span>
            )}
          </div>
        </div>
        <div className="relative">
          {isLive ? (
            <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50 text-sm px-3 py-1.5 shadow-lg shadow-blue-500/50" style={{ animation: 'breath 2s ease-in-out infinite' }}>
              <div className="relative flex items-center gap-2">
                <div className="relative">
                  <span className="w-2.5 h-2.5 bg-blue-400 rounded-full block"></span>
                  <span className="absolute inset-0 w-2.5 h-2.5 bg-blue-400 rounded-full" style={{ animation: 'pulse-ring 1.5s ease-out infinite' }}></span>
                </div>
                <span className="font-semibold">LIVE</span>
              </div>
            </Badge>
          ) : (
            <Badge className="bg-slate-700/20 text-slate-400 border-slate-700/50 text-sm px-3 py-1.5">
              <div className="relative flex items-center gap-2">
                <span className="w-2.5 h-2.5 bg-slate-500 rounded-full block"></span>
                <span className="font-semibold">OFFLINE</span>
              </div>
            </Badge>
          )}
          {pollError && (
            <div className="absolute top-full mt-1 text-xs text-red-400">
              {pollError}
            </div>
          )}
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
          {squadData?.squad.find(a => a.agent_name === 'macro_agent') ? (
            (() => {
              const agent = squadData.squad.find(a => a.agent_name === 'macro_agent')!;
              return (
                <Card className="bg-slate-900/50 border-blue-500/30 backdrop-blur-sm hover:border-blue-500/50 transition-all relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <CardHeader className="pb-2 pt-3 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/50 relative">
                        <Eye className="w-5 h-5 text-white" />
                        <div className="absolute inset-0 bg-blue-400/30 rounded-lg animate-pulse"></div>
                      </div>
                      <div className="flex-1">
                        <CardTitle className="text-white text-xs">{agent.display_name}</CardTitle>
                        <p className="text-slate-500 text-xs">MacroAgent ({agent.weight})</p>
                      </div>
                      <div className={`text-right ${agent.score > 0 ? 'text-emerald-400' : agent.score < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                        <div className="text-sm font-mono">
                          {agent.score > 0 ? (
                            <span className="text-emerald-400">Bullish {Math.abs(agent.score).toFixed(0)}</span>
                          ) : agent.score < 0 ? (
                            <span className="text-red-400">Bearish {Math.abs(agent.score).toFixed(0)}</span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500">Score</div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="px-3 pb-3 space-y-2">
                    {/* Core Inputs */}
                    <div className="space-y-1.5">
                      {agent.core_inputs.map((input, idx) => (
                        <div key={idx}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-slate-400">{input.label}</span>
                            <span className={input.value.includes('+') || input.value.includes('-') ? 
                              (input.value.includes('+') ? 'text-emerald-400' : 'text-red-400') : 
                              'text-blue-400'}>
                              {input.value}
                            </span>
                          </div>
                          {input.progress > 0 && (
                            <Progress value={input.progress} className="h-1.5 bg-slate-800" />
                          )}
                        </div>
                      ))}
                    </div>
                    
                    {/* LLM Conclusion */}
                    <div className="bg-slate-800/50 rounded p-2 border border-slate-700/50">
                      <p className="text-xs text-slate-300 leading-relaxed">
                        "{agent.reasoning}"
                      </p>
                    </div>
                  </CardContent>
                </Card>
              );
            })()
          ) : isLoading ? (
            <Card className="bg-slate-900/50 border-blue-500/30 backdrop-blur-sm">
              <CardHeader className="pb-2 pt-3 px-3">
                <div className="flex items-center gap-2">
                  <Skeleton className="w-10 h-10 rounded-lg" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-3 w-24" />
                    <Skeleton className="h-2 w-32" />
                  </div>
                  <Skeleton className="h-8 w-12" />
                </div>
              </CardHeader>
              <CardContent className="px-3 pb-3 space-y-2">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-3/4" />
                <Skeleton className="h-16 w-full rounded" />
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-slate-900/50 border-blue-500/30 backdrop-blur-sm">
              <CardContent className="px-3 py-3">
                <p className="text-xs text-slate-400 text-center">No MacroAgent data available</p>
              </CardContent>
            </Card>
          )}

          {/* OnChainAgent - Data Warden */}
          {squadData?.squad.find(a => a.agent_name === 'onchain_agent') ? (
            (() => {
              const agent = squadData.squad.find(a => a.agent_name === 'onchain_agent')!;
              return (
                <Card className="bg-slate-900/50 border-emerald-500/30 backdrop-blur-sm hover:border-emerald-500/50 transition-all relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <CardHeader className="pb-2 pt-3 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/50 relative">
                        <Database className="w-5 h-5 text-white" />
                        <div className="absolute inset-0 bg-emerald-400/30 rounded-lg animate-pulse"></div>
                      </div>
                      <div className="flex-1">
                        <CardTitle className="text-white text-xs">{agent.display_name}</CardTitle>
                        <p className="text-slate-500 text-xs">OnChainAgent ({agent.weight})</p>
                      </div>
                      <div className={`text-right ${agent.score > 0 ? 'text-emerald-400' : agent.score < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                        <div className="text-sm font-mono">
                          {agent.score > 0 ? (
                            <span className="text-emerald-400">Bullish {Math.abs(agent.score).toFixed(0)}</span>
                          ) : agent.score < 0 ? (
                            <span className="text-red-400">Bearish {Math.abs(agent.score).toFixed(0)}</span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500">Score</div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="px-3 pb-3 space-y-2">
                    {/* Core Inputs */}
                    <div className="space-y-1.5">
                      {agent.core_inputs.map((input, idx) => (
                        <div key={idx}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-slate-400">{input.label}</span>
                            <span className={
                              input.label === 'Exchange Flow' && input.value.includes('-') ? 
                                'text-emerald-400' : // Exchange流出是看涨（绿色）
                              input.label === 'Exchange Flow' && !input.value.includes('-') && input.value !== 'N/A' ? 
                                'text-red-400' : // Exchange流入是看跌（红色）
                              input.value.includes('+') ? 
                                'text-emerald-400' : 
                              input.value.includes('-') && input.label !== 'Exchange Flow' ? 
                                'text-red-400' : 
                              'text-amber-400'
                            }>
                              {input.value}
                            </span>
                          </div>
                          {input.progress > 0 && (
                            <Progress value={input.progress} className="h-1.5 bg-slate-800" />
                          )}
                        </div>
                      ))}
                    </div>
                    
                    {/* LLM Conclusion */}
                    <div className="bg-slate-800/50 rounded p-2 border border-slate-700/50">
                      <p className="text-xs text-slate-300 leading-relaxed">
                        "{agent.reasoning}"
                      </p>
                    </div>
                  </CardContent>
                </Card>
              );
            })()
          ) : isLoading ? (
            <Card className="bg-slate-900/50 border-emerald-500/30 backdrop-blur-sm">
              <CardHeader className="pb-2 pt-3 px-3">
                <div className="flex items-center gap-2">
                  <Skeleton className="w-10 h-10 rounded-lg" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-3 w-24" />
                    <Skeleton className="h-2 w-32" />
                  </div>
                  <Skeleton className="h-8 w-12" />
                </div>
              </CardHeader>
              <CardContent className="px-3 pb-3 space-y-2">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-3/4" />
                <Skeleton className="h-16 w-full rounded" />
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-slate-900/50 border-emerald-500/30 backdrop-blur-sm">
              <CardContent className="px-3 py-3">
                <p className="text-xs text-slate-400 text-center">No OnChainAgent data available</p>
              </CardContent>
            </Card>
          )}

          {/* TAAgent - Momentum Scout */}
          {squadData?.squad.find(a => a.agent_name === 'ta_agent') ? (
            (() => {
              const agent = squadData.squad.find(a => a.agent_name === 'ta_agent')!;
              const trendStatus = agent.core_inputs.find(i => i.label === 'Trend Status');
              return (
                <Card className="bg-slate-900/50 border-amber-500/30 backdrop-blur-sm hover:border-amber-500/50 transition-all relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <CardHeader className="pb-2 pt-3 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center shadow-lg shadow-amber-500/50 relative">
                        <Zap className="w-5 h-5 text-white" />
                        <div className="absolute inset-0 bg-amber-400/30 rounded-lg animate-pulse"></div>
                      </div>
                      <div className="flex-1">
                        <CardTitle className="text-white text-xs">{agent.display_name}</CardTitle>
                        <p className="text-slate-500 text-xs">TAAgent ({agent.weight})</p>
                      </div>
                      <div className={`text-right ${agent.score > 0 ? 'text-emerald-400' : agent.score < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                        <div className="text-sm font-mono">
                          {agent.score > 0 ? (
                            <span className="text-emerald-400">Bullish {Math.abs(agent.score).toFixed(0)}</span>
                          ) : agent.score < 0 ? (
                            <span className="text-red-400">Bearish {Math.abs(agent.score).toFixed(0)}</span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500">Score</div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="px-3 pb-3 space-y-2">
                    {/* Core Inputs */}
                    <div className="space-y-1.5">
                      {agent.core_inputs.map((input, idx) => (
                        input.label === 'Trend Status' ? (
                          <div key={idx} className="flex items-center justify-between">
                            <span className="text-xs text-slate-400">{input.label}</span>
                            <Badge className={`text-xs px-2 py-0 ${
                              input.value.includes('Golden') || input.value.includes('Bullish') ?
                                'bg-emerald-500/20 text-emerald-400 border-emerald-500/50' :
                                input.value.includes('Death') || input.value.includes('Bearish') ?
                                'bg-red-500/20 text-red-400 border-red-500/50' :
                                'bg-slate-500/20 text-slate-400 border-slate-500/50'
                            }`}>
                              {input.value}
                            </Badge>
                          </div>
                        ) : (
                          <div key={idx}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-400">{input.label}</span>
                              <span className="text-amber-400">{input.value}</span>
                            </div>
                            {input.progress > 0 && (
                              <Progress value={input.progress} className="h-1.5 bg-slate-800" />
                            )}
                          </div>
                        )
                      ))}
                    </div>
                    
                    {/* LLM Conclusion */}
                    <div className="bg-slate-800/50 rounded p-2 border border-slate-700/50">
                      <p className="text-xs text-slate-300 leading-relaxed">
                        "{agent.reasoning}"
                      </p>
                    </div>
                  </CardContent>
                </Card>
              );
            })()
          ) : isLoading ? (
            <Card className="bg-slate-900/50 border-amber-500/30 backdrop-blur-sm">
              <CardHeader className="pb-2 pt-3 px-3">
                <div className="flex items-center gap-2">
                  <Skeleton className="w-10 h-10 rounded-lg" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-3 w-24" />
                    <Skeleton className="h-2 w-32" />
                  </div>
                  <Skeleton className="h-8 w-12" />
                </div>
              </CardHeader>
              <CardContent className="px-3 pb-3 space-y-2">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-3/4" />
                <Skeleton className="h-16 w-full rounded" />
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-slate-900/50 border-amber-500/30 backdrop-blur-sm">
              <CardContent className="px-3 py-3">
                <p className="text-xs text-slate-400 text-center">No TAAgent data available</p>
              </CardContent>
            </Card>
          )}
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
              {isLoading ? (
                <>
                  {/* AI Avatar Skeleton */}
                  <div className="flex justify-center mb-3">
                    <Skeleton className="w-32 h-32 rounded-full" />
                  </div>
                  {/* Commander Name Skeleton */}
                  <div className="text-center mb-3 space-y-1">
                    <Skeleton className="h-4 w-32 mx-auto" />
                    <Skeleton className="h-3 w-40 mx-auto" />
                  </div>
                  {/* Market Analysis Skeleton */}
                  <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50 mb-3">
                    <Skeleton className="h-3 w-40 mb-2" />
                    <div className="space-y-2">
                      <Skeleton className="h-3 w-full" />
                      <Skeleton className="h-3 w-5/6" />
                      <Skeleton className="h-3 w-4/6" />
                    </div>
                  </div>
                  {/* Conviction Score Skeleton */}
                  <div className="flex items-center justify-center gap-2">
                    <Skeleton className="h-8 w-12" />
                    <Skeleton className="h-6 w-20" />
                  </div>
                </>
              ) : (
                <>
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
                <h3 className="text-white text-sm mb-0.5">{commanderData?.commander_name || "Commander Nova"}</h3>
                <p className="text-slate-400 text-xs">AI Strategy Coordinator</p>
              </div>

              {/* Market Analysis */}
              <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50 mb-3">
                <div className="text-xs text-slate-400 mb-2">Market Analysis Summary:</div>
                <div className="text-xs text-slate-200 leading-relaxed">
                      "{commanderData?.market_analysis || "No analysis data available"}"
                  {commanderData?.conviction_score && commanderData.conviction_score > 70 && (
                    <span className="text-emerald-400 font-medium"> Overall conviction: STRONG BUY.</span>
                  )}
                </div>
              </div>

              {/* Conviction Score Badge */}
              <div className="flex items-center justify-center gap-2">
                <div className="text-center">
                  <div className={`text-2xl font-bold mb-0.5 ${
                    (commanderData?.conviction_score || 0) > 70 ? 'text-emerald-400' :
                    (commanderData?.conviction_score || 0) > 40 ? 'text-amber-400' :
                    'text-red-400'
                  }`}>
                    {commanderData?.conviction_score || 0}
                  </div>
                  <div className="text-xs text-slate-400">Conviction</div>
                </div>
                <Badge className={`text-xs px-3 py-1 ${
                  commanderData?.conviction_level === 'Strong' ?
                    'bg-emerald-500/20 text-emerald-400 border-emerald-500/50' :
                  commanderData?.conviction_level === 'Moderate' ?
                    'bg-amber-500/20 text-amber-400 border-amber-500/50' :
                    'bg-red-500/20 text-red-400 border-red-500/50'
                }`}>
                  {commanderData?.conviction_level === 'Strong' ? '🔥 Strong' :
                   commanderData?.conviction_level === 'Moderate' ? '⚡ Moderate' :
                   '⚠️ Weak'}
                </Badge>
              </div>
                </>
              )}
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
                        {directiveHistory?.directives.length ? (
                          directiveHistory.directives.map((directive) => (
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
                                  {directive.strategy_subtitle && (
                                    <div className="text-xs text-slate-400 mb-1">{directive.strategy_subtitle}</div>
                                  )}
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
                          ))
                        ) : (
                          <div className="text-center text-xs text-slate-400 py-8">
                            No history records
                          </div>
                        )}
                      </div>
                    </ScrollArea>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent className="px-3 pb-3 space-y-2">
              {/* Strategy Info */}
              {directiveData?.strategy_name ? (
                <>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50 text-xs px-2 py-0.5">
                      {directiveData.strategy_name}
                    </Badge>
                    {directiveData.strategy_subtitle && (
                      <span className="text-xs text-slate-500">{directiveData.strategy_subtitle}</span>
                    )}
                  </div>

                  {/* Countdown */}
                  <div className="bg-slate-800/50 rounded p-2 border border-slate-700/50">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs text-slate-400">Next Update In:</span>
                      <Badge className="bg-cyan-500/20 text-cyan-400 border-cyan-500/50 text-xs px-2 py-0 font-mono">
                        {localCountdown?.formatted || directiveData.countdown.formatted}
                      </Badge>
                    </div>
                    <Progress value={localCountdown?.progress ?? directiveData.countdown.progress} className="h-1.5 bg-slate-700" />
                  </div>

                  {/* Current Action */}
                  <div className={`bg-gradient-to-br rounded-lg p-2.5 border ${
                    directiveData.action.type === 'BUY' ?
                      'from-emerald-500/10 to-cyan-500/10 border-emerald-500/30' :
                    directiveData.action.type === 'SELL' ?
                      'from-red-500/10 to-rose-500/10 border-red-500/30' :
                      'from-slate-500/10 to-slate-500/10 border-slate-500/30'
                  }`}>
                    <div className="text-center mb-2">
                      <div className={`text-xs mb-1 tracking-wider uppercase flex items-center justify-center gap-1.5 ${
                        directiveData.action.type === 'BUY' ? 'text-emerald-400' :
                        directiveData.action.type === 'SELL' ? 'text-red-400' :
                        'text-slate-400'
                      }`}>
                        {directiveData.action.type === 'BUY' && <TrendingUp className="w-3.5 h-3.5" />}
                        {directiveData.action.type === 'SELL' && <TrendingDown className="w-3.5 h-3.5" />}
                        {directiveData.status}
                      </div>
                    </div>
                    
                    <div className="bg-slate-900/50 rounded p-2 mb-1.5">
                      <div className={`text-center text-sm ${
                        directiveData.action.type === 'BUY' ? 'text-white' :
                        directiveData.action.type === 'SELL' ? 'text-white' :
                        'text-slate-400'
                      }`}>
                        {directiveData.action.type} {directiveData.action.amount !== '0%' && (
                          <span className={directiveData.action.type === 'BUY' ? 'text-emerald-400' : 'text-red-400'}>
                            {directiveData.action.amount}
                          </span>
                        )} {directiveData.action.asset}
                      </div>
                    </div>

                    <div className="text-xs text-slate-300 text-center">
                      {directiveData.description}
                    </div>
                  </div>
                </>
              ) : isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-4 w-24 mx-auto" />
                  <Skeleton className="h-16 w-full rounded" />
                  <Skeleton className="h-20 w-full rounded" />
                </div>
              ) : (
                <div className="text-center text-xs text-slate-400 py-4">
                  No active directive
                </div>
              )}
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
                  {isLoading ? (
                    <div className="space-y-2">
                      <Skeleton className="h-3 w-full" />
                      <Skeleton className="h-3 w-5/6" />
                      <Skeleton className="h-3 w-4/6" />
                      <Skeleton className="h-3 w-3/4" />
                    </div>
                  ) : dataStream?.stream && dataStream.stream.length > 0 ? (
                    dataStream.stream.map((item, index) => (
                      <div key={index} className="flex items-center gap-2 text-cyan-400/80 hover:text-cyan-400 transition-colors">
                        <span className="text-slate-600">[{item.type}]</span>
                        <span className="flex-1">{item.text}</span>
                        {item.trend === 'up' && <TrendingUp className="w-3 h-3 text-emerald-400" />}
                        {item.trend === 'down' && <TrendingDown className="w-3 h-3 text-red-400" />}
                      </div>
                    ))
                  ) : (
                    <div className="text-center text-slate-500 text-xs py-4">
                      No data flow
                    </div>
                  )}
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
