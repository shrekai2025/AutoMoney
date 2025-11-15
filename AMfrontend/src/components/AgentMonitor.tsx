/**
 * Agent Execution Monitor - Agent执行监控
 *
 * 实时查看所有Agent的执行状态和历史记录
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { RefreshCw, Activity, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface AgentStat {
  agent_name: string;
  agent_display_name: string;
  total_executions: number;
  recent_signal: string;
  recent_score: number;
  last_executed: string;
  avg_duration_ms: number;
}

interface AgentExecution {
  id: string;
  agent_name: string;
  agent_display_name: string;
  executed_at: string;
  execution_duration_ms: number;
  status: string;
  signal: string;
  confidence: number;
  score: number;
  reasoning: string;
}

export function AgentMonitor() {
  const [stats, setStats] = useState<AgentStat[]>([]);
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(24);

  const fetchStats = async () => {
    try {
      const response = await fetch(`/api/v1/agent-monitor/stats?hours=${timeRange}`);
      const data = await response.json();
      setStats(data.stats || []);
    } catch (error) {
      console.error('Failed to fetch agent stats:', error);
    }
  };

  const fetchExecutions = async (agentName?: string) => {
    try {
      setLoading(true);
      const url = agentName
        ? `/api/v1/agent-monitor/executions?hours=${timeRange}&agent_name=${agentName}&limit=50`
        : `/api/v1/agent-monitor/executions?hours=${timeRange}&limit=50`;
      const response = await fetch(url);
      const data = await response.json();
      setExecutions(data.executions || []);
    } catch (error) {
      console.error('Failed to fetch executions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchExecutions(selectedAgent || undefined);

    // 每30秒自动刷新
    const interval = setInterval(() => {
      fetchStats();
      fetchExecutions(selectedAgent || undefined);
    }, 30000);

    return () => clearInterval(interval);
  }, [timeRange, selectedAgent]);

  const getSignalIcon = (signal: string) => {
    switch (signal.toUpperCase()) {
      case 'BULLISH':
      case 'BUY':
        return <TrendingUp className="w-4 h-4 text-green-400" />;
      case 'BEARISH':
      case 'SELL':
        return <TrendingDown className="w-4 h-4 text-red-400" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal.toUpperCase()) {
      case 'BULLISH':
      case 'BUY':
        return 'text-green-400 bg-green-400/10';
      case 'BEARISH':
      case 'SELL':
        return 'text-red-400 bg-red-400/10';
      default:
        return 'text-gray-400 bg-gray-400/10';
    }
  };

  const formatRelativeTime = (isoTime: string) => {
    const date = new Date(isoTime);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-blue-400" />
            Agent Execution Monitor
          </h2>
          <p className="text-gray-400 mt-1">实时监控所有Agent的执行状态</p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="bg-slate-800 text-white border border-slate-700 rounded-lg px-3 py-2 text-sm"
          >
            <option value={1}>Last 1 hour</option>
            <option value={6}>Last 6 hours</option>
            <option value={24}>Last 24 hours</option>
            <option value={48}>Last 48 hours</option>
            <option value={168}>Last 7 days</option>
          </select>

          <Button
            onClick={() => {
              fetchStats();
              fetchExecutions(selectedAgent || undefined);
            }}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Agent Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {stats.map((stat) => (
          <Card
            key={stat.agent_name}
            className={`cursor-pointer transition-all ${
              selectedAgent === stat.agent_name
                ? 'ring-2 ring-blue-500 bg-slate-800/80'
                : 'hover:bg-slate-800/50'
            }`}
            onClick={() => {
              setSelectedAgent(selectedAgent === stat.agent_name ? null : stat.agent_name);
            }}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-300">
                {stat.agent_display_name}
              </CardTitle>
              <CardDescription className="text-xs text-gray-500">
                {stat.agent_name}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Signal:</span>
                <div className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${getSignalColor(stat.recent_signal)}`}>
                  {getSignalIcon(stat.recent_signal)}
                  {stat.recent_signal}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Score:</span>
                <span className="text-sm font-mono text-white">{stat.recent_score.toFixed(1)}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Executions:</span>
                <span className="text-sm font-mono text-white">{stat.total_executions}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Last Run:</span>
                <span className="text-xs text-gray-300">{formatRelativeTime(stat.last_executed)}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Avg Time:</span>
                <span className="text-xs text-gray-300">{(stat.avg_duration_ms / 1000).toFixed(1)}s</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Execution History Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {selectedAgent ? `${stats.find(s => s.agent_name === selectedAgent)?.agent_display_name} - ` : ''}
            Execution History
          </CardTitle>
          <CardDescription>
            {selectedAgent ? 'Filtered by selected agent' : 'Showing all agents'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-gray-400">Loading...</div>
          ) : executions.length === 0 ? (
            <div className="text-center py-8 text-gray-400">No executions found in the selected time range</div>
          ) : (
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="w-full text-sm min-w-[1000px]">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Agent</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Time</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Signal</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">Score</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">Confidence</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">Duration</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Reasoning</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.map((ex) => (
                    <tr key={ex.id} className="border-b border-slate-800 hover:bg-slate-800/30">
                      <td className="py-3 px-4">
                        <div>
                          <div className="font-medium text-white">{ex.agent_display_name}</div>
                          <div className="text-xs text-gray-500">{ex.agent_name}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-gray-300 text-xs">
                        <div>{new Date(ex.executed_at).toLocaleString()}</div>
                        <div className="text-gray-500">{formatRelativeTime(ex.executed_at)}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${getSignalColor(ex.signal)}`}>
                          {getSignalIcon(ex.signal)}
                          {ex.signal}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-white">{ex.score.toFixed(1)}</td>
                      <td className="py-3 px-4 text-right font-mono text-gray-300">{(ex.confidence * 100).toFixed(0)}%</td>
                      <td className="py-3 px-4 text-right text-gray-300">{(ex.execution_duration_ms / 1000).toFixed(2)}s</td>
                      <td className="py-3 px-4 text-gray-400 text-xs max-w-xs truncate">{ex.reasoning}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
