/**
 * MultiAgentSquadActions - 旧策略(Multi-Agent BTC Strategy)的Recent Actions展示
 * 
 * 特点:
 * - 3个Agent (The Oracle, Momentum Scout, Data Warden)
 * - Conviction Score
 * - BUY/SELL/HOLD信号
 */

import { Badge } from "../ui/badge";

interface AgentContribution {
  agent_name: string;
  display_name: string;
  signal: string;
  confidence: number;
  score: number;
}

interface Activity {
  agent: string;
  date: string;
  signal: string;
  status: string;
  conviction_score: number;
  agent_contributions?: AgentContribution[];
  error_details?: {
    failed_agent?: string;
    error_message: string;
    retry_count?: number;
  };
}

interface MultiAgentSquadActionsProps {
  activities: Activity[];
}

export function MultiAgentSquadActions({ activities }: MultiAgentSquadActionsProps) {
  return (
    <div className="space-y-1.5">
      {activities.map((activity, index) => (
        <div
          key={index}
          className={`flex items-center justify-between p-2 rounded border transition-all ${
            activity.status === 'failed'
              ? 'bg-red-900/20 border-red-500/50 hover:border-red-500/70'
              : 'bg-slate-800/30 border-slate-700/50 hover:border-purple-500/50'
          }`}
        >
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-0.5">
              <Badge className={`text-xs px-1.5 py-0 h-4 ${
                activity.status === 'failed'
                  ? 'bg-red-500/20 text-red-400 border-red-500/50'
                  : 'bg-purple-500/20 text-purple-400 border-purple-500/50'
              }`}>
                {activity.agent}
              </Badge>
              {activity.status === 'failed' && (
                <Badge className="bg-red-500/30 text-red-300 border-red-500/60 text-xs px-1.5 py-0 h-4">
                  ERROR
                </Badge>
              )}
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

            {/* 显示错误信息或正常信号 */}
            {activity.status === 'failed' && activity.error_details ? (
              <div className="text-xs mb-0.5">
                <div className="text-red-400 font-medium mb-1">
                  Agent工作错误
                </div>
                <div className="text-red-300/80 text-xs">
                  失败的Agent: <span className="font-medium">{activity.error_details.failed_agent || 'multiple'}</span>
                </div>
                <div className="text-red-300/70 text-xs mt-0.5">
                  {activity.error_details.error_message}
                </div>
                {activity.error_details.retry_count && activity.error_details.retry_count > 0 && (
                  <div className="text-red-300/60 text-xs mt-0.5">
                    重试次数: {activity.error_details.retry_count}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-white text-xs mb-0.5">
                {activity.signal === 'HOLD' ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/50 font-medium">
                    HOLD
                  </span>
                ) : activity.signal === 'BUY' ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 font-medium">
                    BUY
                  </span>
                ) : activity.signal === 'SELL' ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/50 font-medium">
                    SELL
                  </span>
                ) : (
                  <>Signal: <span className="text-slate-300">{activity.signal}</span></>
                )}
              </div>
            )}

            {/* Agent Contributions - 只在成功时显示 */}
            {activity.status !== 'failed' && activity.agent_contributions && activity.agent_contributions.length > 0 && (
              <div className="mt-1.5 space-y-1">
                {activity.agent_contributions.map((agent, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs bg-slate-900/50 rounded px-2 py-1 border border-slate-700/30">
                    <span className="text-purple-400 font-medium w-28">{agent.display_name}</span>
                    <span className={`px-1.5 py-0.5 rounded font-medium ${
                      agent.signal === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-400' :
                      agent.signal === 'BEARISH' ? 'bg-red-500/20 text-red-400' :
                      'bg-slate-500/20 text-slate-300'
                    }`}>
                      {agent.signal}
                    </span>
                    <span className="text-slate-400">
                      Confidence: <span className="text-white">{agent.confidence}%</span>
                    </span>
                    <span className="text-slate-400">
                      Score: <span className={`${agent.score > 0 ? 'text-emerald-400' : agent.score < 0 ? 'text-red-400' : 'text-slate-300'}`}>
                        {agent.score > 0 ? '+' : ''}{agent.score.toFixed(1)}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right side - Conviction Score */}
          {activity.status !== 'failed' && (
            <div className="ml-4 text-right">
              <div className="text-xs text-slate-400 mb-0.5">Agent Confidence</div>
              <div className="text-sm text-slate-400">
                (reliability)
              </div>
              <div className="text-base font-bold text-white mt-0.5">
                {activity.conviction_score !== undefined ? `${activity.conviction_score.toFixed(1)}%` : 'N/A'}
              </div>
              {activity.conviction_score !== undefined && (
                <div className={`text-xs font-medium ${
                  activity.conviction_score > 70 ? 'text-emerald-400' :
                  activity.conviction_score > 40 ? 'text-amber-400' :
                  'text-red-400'
                }`}>
                  {activity.conviction_score > 70 ? '高信心' :
                   activity.conviction_score > 40 ? '中等' :
                   '低信心'}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

