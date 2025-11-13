/**
 * MomentumSquadActions - 动量策略(H.I.M.E.)的Recent Actions展示
 * 
 * 特点:
 * - 2个Agent (Regime Filter, Momentum TA)
 * - Regime Score (0-100市场健康度)
 * - 多资产分析 (BTC/ETH/SOL)
 * - OCO订单 (Stop Loss + Take Profit)
 */

import { Badge } from "../ui/badge";
import { TrendingUp, TrendingDown, Shield } from "lucide-react";

interface AgentContribution {
  agent_name: string;
  display_name: string;
  signal: string;
  confidence: number;
  score?: number;
}

interface Activity {
  agent: string;
  date: string;
  signal: string;
  status: string;
  conviction_score?: number;
  agent_contributions?: AgentContribution[];
  metadata?: {
    regime_score?: number;
    regime_classification?: string;
    regime_multiplier?: number;
    ta_decision?: {
      asset?: string;
      signal_strength?: number;
      trend?: string;
    };
    oco_order?: {
      asset?: string;
      side?: string;
      entry_price?: number;
      stop_loss_price?: number;
      take_profit_price?: number;
      leverage?: number;
    };
  };
  error_details?: {
    failed_agent?: string;
    error_message: string;
    retry_count?: number;
  };
}

interface MomentumSquadActionsProps {
  activities: Activity[];
}

export function MomentumSquadActions({ activities }: MomentumSquadActionsProps) {
  return (
    <div className="space-y-2">
      {activities.map((activity, index) => {
        const regimeScore = activity.metadata?.regime_score;
        const regimeClassification = activity.metadata?.regime_classification;
        const regimeMultiplier = activity.metadata?.regime_multiplier;
        const taDecision = activity.metadata?.ta_decision;
        const ocoOrder = activity.metadata?.oco_order;
        
        return (
          <div 
            key={index} 
            className={`flex flex-col p-3 rounded border transition-all ${
              activity.status === 'failed'
                ? 'bg-red-900/20 border-red-500/50'
                : 'bg-slate-800/30 border-slate-700/50 hover:border-purple-500/50'
            }`}
          >
            {/* Header: Badge + Time + Signal */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50 text-xs px-2 py-0.5">
                  Momentum Strategy
                </Badge>
                {activity.status === 'failed' && (
                  <Badge className="bg-red-500/30 text-red-300 border-red-500/60 text-xs px-2 py-0.5">
                    ERROR
                  </Badge>
                )}
                <span className="text-xs text-slate-500">
                  {new Date(activity.date).toLocaleString(undefined, {
                    month: 'numeric',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
              
              {/* Signal Badge */}
              {activity.status !== 'failed' && (
                <Badge className={`text-sm px-2.5 py-0.5 font-semibold ${
                  activity.signal === 'LONG' 
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
                    : activity.signal === 'SHORT'
                    ? 'bg-red-500/20 text-red-400 border-red-500/50'
                    : 'bg-blue-500/20 text-blue-400 border-blue-500/50'
                }`}>
                  {activity.signal === 'LONG' && <TrendingUp className="w-3 h-3 inline mr-1" />}
                  {activity.signal === 'SHORT' && <TrendingDown className="w-3 h-3 inline mr-1" />}
                  {activity.signal}
                </Badge>
              )}
            </div>
            
            {/* Error Display */}
            {activity.status === 'failed' && activity.error_details && (
              <div className="bg-red-900/30 border border-red-500/30 rounded p-2 mb-2">
                <div className="text-red-400 font-medium text-xs mb-1">Agent工作错误</div>
                <div className="text-red-300/80 text-xs">
                  失败的Agent: <span className="font-medium">{activity.error_details.failed_agent || 'multiple'}</span>
                </div>
                <div className="text-red-300/70 text-xs mt-0.5">{activity.error_details.error_message}</div>
              </div>
            )}
            
            {/* Regime Score Gauge */}
            {activity.status !== 'failed' && regimeScore !== undefined && (
              <div className="mb-2">
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-blue-400" />
                    <span className="text-slate-400 font-medium">Market Regime</span>
                  </div>
                  <span className={`font-bold ${
                    regimeScore >= 70 ? 'text-emerald-400' :
                    regimeScore >= 50 ? 'text-blue-400' :
                    regimeScore >= 30 ? 'text-amber-400' :
                    'text-red-400'
                  }`}>
                    {regimeClassification || 'NEUTRAL'}
                  </span>
                </div>
                <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
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
                  <span>DANGEROUS</span>
                  <span className="text-white font-medium">{regimeScore.toFixed(0)}</span>
                  <span>HEALTHY</span>
                </div>
                {regimeMultiplier !== undefined && (
                  <div className="text-xs text-slate-400 mt-1">
                    Position Multiplier: <span className="text-purple-400 font-medium">{regimeMultiplier.toFixed(2)}x</span>
                  </div>
                )}
              </div>
            )}
            
            {/* TA Decision (Target Asset) */}
            {activity.status !== 'failed' && taDecision?.asset && (
              <div className="bg-slate-900/50 border border-slate-700/30 rounded px-2.5 py-1.5 mb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-purple-400 font-medium">Target:</span>
                    <span className="text-white font-bold text-sm">{taDecision.asset}</span>
                    {taDecision.trend && (
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        taDecision.trend.includes('UP') ? 'bg-emerald-500/20 text-emerald-400' :
                        taDecision.trend.includes('DOWN') ? 'bg-red-500/20 text-red-400' :
                        'bg-slate-500/20 text-slate-300'
                      }`}>
                        {taDecision.trend}
                      </span>
                    )}
                  </div>
                  {taDecision.signal_strength !== undefined && (
                    <div className="text-xs">
                      <span className="text-slate-400">Strength: </span>
                      <span className="text-emerald-400 font-medium">
                        {(taDecision.signal_strength * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* OCO Order Details */}
            {activity.status !== 'failed' && ocoOrder && ocoOrder.entry_price && (
              <div className="grid grid-cols-3 gap-1.5 mb-2">
                <div className="bg-red-500/10 border border-red-500/30 rounded px-2 py-1.5 text-center">
                  <div className="text-red-400 font-semibold text-xs mb-0.5">STOP LOSS</div>
                  <div className="text-white font-bold text-sm">
                    ${ocoOrder.stop_loss_price?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                  </div>
                  {ocoOrder.entry_price && ocoOrder.stop_loss_price && (
                    <div className="text-red-300 text-xs mt-0.5">
                      {(((ocoOrder.stop_loss_price - ocoOrder.entry_price) / ocoOrder.entry_price) * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
                <div className="bg-slate-700/30 border border-slate-600/50 rounded px-2 py-1.5 text-center">
                  <div className="text-slate-300 font-semibold text-xs mb-0.5">ENTRY</div>
                  <div className="text-white font-bold text-sm">
                    ${ocoOrder.entry_price?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                  </div>
                  {ocoOrder.leverage && (
                    <div className="text-purple-400 text-xs mt-0.5">
                      {ocoOrder.leverage.toFixed(1)}x
                    </div>
                  )}
                </div>
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded px-2 py-1.5 text-center">
                  <div className="text-emerald-400 font-semibold text-xs mb-0.5">TAKE PROFIT</div>
                  <div className="text-white font-bold text-sm">
                    ${ocoOrder.take_profit_price?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                  </div>
                  {ocoOrder.entry_price && ocoOrder.take_profit_price && (
                    <div className="text-emerald-300 text-xs mt-0.5">
                      +{(((ocoOrder.take_profit_price - ocoOrder.entry_price) / ocoOrder.entry_price) * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Agent Contributions */}
            {activity.status !== 'failed' && activity.agent_contributions && activity.agent_contributions.length > 0 && (
              <div className="pt-2 border-t border-slate-700/30 space-y-1">
                {activity.agent_contributions.map((agent, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        agent.agent_name === 'regime_filter' ? 'bg-blue-400' : 'bg-purple-400'
                      }`} />
                      <span className={`font-medium ${
                        agent.agent_name === 'regime_filter' ? 'text-blue-400' : 'text-purple-400'
                      }`}>
                        {agent.display_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      {agent.score !== undefined && agent.agent_name === 'regime_filter' && (
                        <span className="text-slate-400">
                          Score: <span className="text-white font-medium">{agent.score.toFixed(1)}</span>
                        </span>
                      )}
                      <span className="text-slate-400">
                        Confidence: <span className="text-white font-medium">{agent.confidence}%</span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

