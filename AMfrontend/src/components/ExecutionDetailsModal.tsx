import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  Brain,
  TrendingUp,
  Database,
  Clock,
  CheckCircle2,
  XCircle,
  MessageSquare,
  Code2,
  BarChart3,
  Zap,
  DollarSign,
} from "lucide-react";
import { fetchExecutionDetail } from "../lib/marketplaceApi";
import type { StrategyExecutionDetail, AgentExecutionDetail } from "../types/strategy";
import { getAgentIcon, getAgentColor } from "../utils/strategyUtils";
import { useAuth } from "../contexts/AuthContext";

interface ExecutionDetailsModalProps {
  executionId: string | null;
  onClose: () => void;
}

export function ExecutionDetailsModal({
  executionId,
  onClose,
}: ExecutionDetailsModalProps) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [execution, setExecution] = useState<StrategyExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  useEffect(() => {
    if (executionId && !authLoading && isAuthenticated) {
      loadExecutionDetail();
    }
  }, [executionId, authLoading, isAuthenticated]);

  async function loadExecutionDetail() {
    if (!executionId) return;

    try {
      setLoading(true);
      setError(null);
      const data = await fetchExecutionDetail(executionId);
      setExecution(data);
      // Select first agent by default
      if (data.agent_executions.length > 0) {
        setSelectedAgent(data.agent_executions[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load execution details");
      console.error("Failed to load execution details:", err);
    } finally {
      setLoading(false);
    }
  }

  if (!executionId) return null;

  const selectedAgentData = execution?.agent_executions.find(
    (agent) => agent.id === selectedAgent
  );

  return (
    <Dialog open={!!executionId} onOpenChange={() => onClose()}>
      <DialogContent
        className="overflow-hidden bg-slate-900 border-slate-700 p-0 [&>button]:text-white [&>button:hover]:text-slate-200"
        style={{
          maxWidth: '96vw',
          width: '96vw',
          maxHeight: '90vh',
          height: '90vh',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <DialogHeader className="flex-shrink-0 pb-3 pt-6 px-6 border-b border-slate-700/50">
          <DialogTitle className="text-white text-xl flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            Strategy Execution Details
          </DialogTitle>
        </DialogHeader>

        <div
          className="flex-1 px-6"
          style={{
            overflowY: 'auto',
            overflowX: 'hidden'
          }}
        >{/* Scrollable content wrapper */}

        {authLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
              <p className="text-slate-400">Checking authentication...</p>
            </div>
          </div>
        ) : !isAuthenticated ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <XCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <p className="text-slate-400">Please log in to view execution details</p>
            </div>
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
              <p className="text-slate-400">Loading execution details...</p>
            </div>
          </div>
        ) : error || !execution ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <XCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <p className="text-slate-400">{error || "Execution not found"}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3 py-3">
            {/* Execution Summary - Compact */}
            <Card className="bg-slate-900/50 border-slate-700/50">
              <CardHeader className="pb-2 pt-2.5 px-3">
                <CardTitle className="text-white text-xs font-semibold flex items-center gap-2">
                  <BarChart3 className="w-3.5 h-3.5 text-purple-400" />
                  Execution Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="px-3 pb-2.5">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <div className="bg-slate-800/30 rounded p-2">
                    <div className="text-xs text-slate-500 mb-1">Status</div>
                    <Badge
                      className={`text-xs ${
                        execution.status === "completed"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/50"
                          : execution.status === "failed"
                          ? "bg-red-500/20 text-red-400 border-red-500/50"
                          : "bg-amber-500/20 text-amber-400 border-amber-500/50"
                      }`}
                    >
                      {execution.status === "completed" && (
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                      )}
                      {execution.status === "failed" && <XCircle className="w-3 h-3 mr-1" />}
                      {execution.status}
                    </Badge>
                  </div>

                  <div className="bg-slate-800/30 rounded p-2">
                    <div className="text-xs text-slate-500 mb-1">Executed At</div>
                    <div className="text-white text-xs font-medium">
                      {new Date(execution.execution_time).toLocaleString()}
                    </div>
                  </div>

                  {execution.conviction_score !== null && (
                    <div className="bg-slate-800/30 rounded p-2">
                      <div className="text-xs text-slate-500 mb-1">Conviction</div>
                      <div className="text-white text-sm font-semibold">
                        {execution.conviction_score.toFixed(1)}%
                      </div>
                    </div>
                  )}

                  {execution.execution_duration_ms && (
                    <div className="bg-slate-800/30 rounded p-2">
                      <div className="text-xs text-slate-500 mb-1">Duration</div>
                      <div className="text-white text-xs font-medium flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {(execution.execution_duration_ms / 1000).toFixed(2)}s
                      </div>
                    </div>
                  )}
                </div>

                {execution.signal && (
                  <div className="bg-slate-800/30 rounded p-2 mt-2">
                    <div className="text-xs text-slate-500 mb-1">Final Signal</div>
                    <Badge
                      className={`text-xs ${
                        execution.signal === "BUY"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/50"
                          : execution.signal === "SELL"
                          ? "bg-red-500/20 text-red-400 border-red-500/50"
                          : execution.signal === "HOLD"
                          ? "bg-blue-500/20 text-blue-400 border-blue-500/50"
                          : "bg-slate-500/20 text-slate-400 border-slate-500/50"
                      }`}
                    >
                      {execution.signal}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Trade Details - Only show if trades exist */}
            {execution.trades && execution.trades.length > 0 && (
              <Card className="bg-slate-900/50 border-slate-700/50">
                <CardHeader className="pb-2 pt-2.5 px-3">
                  <CardTitle className="text-white text-xs font-semibold flex items-center gap-2">
                    <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                    Trade Executed ({execution.trades.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="px-3 pb-2.5">
                  {execution.trades.map((trade, index) => (
                    <div key={trade.id} className={`${index > 0 ? 'mt-3 pt-3 border-t border-slate-700/30' : ''}`}>
                      {/* Trade Header */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge
                            className={`text-xs ${
                              trade.trade_type === "BUY"
                                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/50"
                                : "bg-red-500/20 text-red-400 border-red-500/50"
                            }`}
                          >
                            {trade.trade_type === "BUY" ? "BUY" : "SELL"} {trade.symbol}
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-400">
                          {new Date(trade.executed_at).toLocaleString()}
                        </div>
                      </div>

                      {/* Trade Details Grid */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        <div className="bg-slate-800/30 rounded p-2">
                          <div className="text-xs text-slate-500 mb-1">Amount</div>
                          <div className="text-white text-xs font-medium">
                            {Number(trade.amount).toFixed(8)} {trade.symbol}
                          </div>
                        </div>

                        <div className="bg-slate-800/30 rounded p-2">
                          <div className="text-xs text-slate-500 mb-1">Price</div>
                          <div className="text-white text-xs font-medium">
                            ${Number(trade.price).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                          </div>
                        </div>

                        <div className="bg-slate-800/30 rounded p-2">
                          <div className="text-xs text-slate-500 mb-1">Total Value</div>
                          <div className="text-white text-xs font-medium">
                            ${Number(trade.total_value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                          </div>
                        </div>

                        <div className="bg-slate-800/30 rounded p-2">
                          <div className="text-xs text-slate-500 mb-1">Fee</div>
                          <div className="text-white text-xs font-medium">
                            ${Number(trade.fee).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                          </div>
                        </div>
                      </div>

                      {/* Balance Changes */}
                      {(trade.balance_before !== null || trade.holding_before !== null) && (
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          {trade.balance_before !== null && trade.balance_after !== null && (
                            <div className="bg-slate-800/30 rounded p-2">
                              <div className="text-xs text-slate-500 mb-1">Cash Balance</div>
                              <div className="text-white text-xs">
                                ${Number(trade.balance_before).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} → ${Number(trade.balance_after).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                              </div>
                            </div>
                          )}

                          {trade.holding_before !== null && trade.holding_after !== null && (
                            <div className="bg-slate-800/30 rounded p-2">
                              <div className="text-xs text-slate-500 mb-1">{trade.symbol} Holding</div>
                              <div className="text-white text-xs">
                                {Number(trade.holding_before).toFixed(8)} → {Number(trade.holding_after).toFixed(8)}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* PnL if SELL */}
                      {trade.trade_type === "SELL" && trade.realized_pnl !== null && (
                        <div className="bg-slate-800/30 rounded p-2 mt-2">
                          <div className="text-xs text-slate-500 mb-1">Realized PnL</div>
                          <div className={`text-xs font-semibold ${Number(trade.realized_pnl) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {Number(trade.realized_pnl) >= 0 ? '+' : ''}${Number(trade.realized_pnl).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                            {trade.realized_pnl_percent !== null && (
                              <span className="ml-1">
                                ({Number(trade.realized_pnl_percent) >= 0 ? '+' : ''}{Number(trade.realized_pnl_percent).toFixed(2)}%)
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Trade Reason */}
                      {trade.reason && (
                        <div className="bg-slate-800/30 rounded p-2 mt-2">
                          <div className="text-xs text-slate-500 mb-1">Reason</div>
                          <div className="text-white text-xs">
                            {trade.reason}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Agent Executions */}
            <Card className="bg-slate-900/50 border-slate-700/50">
              <CardHeader className="pb-2 pt-2.5 px-3">
                <CardTitle className="text-white text-xs font-semibold flex items-center gap-2">
                  <Brain className="w-3.5 h-3.5 text-purple-400" />
                  Agent Executions ({execution.agent_executions.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="px-3 pb-3">
                {/* Agent Selection Buttons - Improved visibility */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {execution.agent_executions.map((agent) => {
                    const Icon = getAgentIcon(agent.agent_name);
                    const color = getAgentColor(agent.agent_name);
                    const isSelected = agent.id === selectedAgent;

                    return (
                      <button
                        key={agent.id}
                        onClick={() => setSelectedAgent(agent.id)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all text-xs font-medium ${
                          isSelected
                            ? `bg-purple-500/30 border-purple-400 text-white shadow-lg shadow-purple-500/20`
                            : "bg-slate-800/50 border-slate-600 text-slate-300 hover:border-slate-500 hover:bg-slate-800"
                        }`}
                      >
                        <Icon className={`w-4 h-4 ${isSelected ? 'text-purple-300' : 'text-slate-400'}`} />
                        <span>
                          {agent.agent_display_name || agent.agent_name}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {selectedAgentData && (
                  <AgentExecutionView agent={selectedAgentData} />
                )}
              </CardContent>
            </Card>
          </div>
        )}
        </div>{/* End scrollable content wrapper */}
      </DialogContent>
    </Dialog>
  );
}

function AgentExecutionView({ agent }: { agent: AgentExecutionDetail }) {
  return (
    <div className="space-y-3">
      {/* Agent Summary - Compact */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div className="bg-slate-800/30 rounded p-2">
          <div className="text-xs text-slate-500 mb-1">Signal</div>
          <Badge
            className={`text-xs ${
              agent.signal === "BULLISH"
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/50"
                : agent.signal === "BEARISH"
                ? "bg-red-500/20 text-red-400 border-red-500/50"
                : "bg-slate-500/20 text-slate-400 border-slate-500/50"
            }`}
          >
            {agent.signal}
          </Badge>
        </div>

        <div className="bg-slate-800/30 rounded p-2">
          <div className="text-xs text-slate-500 mb-1 flex items-center gap-1">
            <span>Agent Confidence</span>
            <span className="text-[10px] text-slate-600" title="AI's certainty about its own analysis">(reliability)</span>
          </div>
          <div className="text-white text-sm font-semibold">
            {(agent.confidence * 100).toFixed(1)}%
          </div>
        </div>

        {agent.score !== null && (
          <div className="bg-slate-800/30 rounded p-2">
            <div className="text-xs text-slate-500 mb-1 flex items-center gap-1">
              <span>Conviction Score</span>
              <span className="text-[10px] text-slate-600" title="Investment recommendation strength">(investment)</span>
            </div>
            <div
              className={`text-sm font-semibold ${
                agent.score > 0 ? "text-emerald-400" : agent.score < 0 ? "text-red-400" : "text-slate-400"
              }`}
            >
              {agent.score > 0 ? "+" : ""}
              {agent.score.toFixed(1)}
            </div>
          </div>
        )}

        {agent.execution_duration_ms && (
          <div className="bg-slate-800/30 rounded p-2">
            <div className="text-xs text-slate-500 mb-1">Duration</div>
            <div className="text-white text-xs font-medium flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {(agent.execution_duration_ms / 1000).toFixed(2)}s
            </div>
          </div>
        )}
      </div>

      {/* Tabs for different sections - Improved colors */}
      <Tabs defaultValue="reasoning" className="w-full">
        <TabsList className="bg-slate-800/50 border border-slate-700 w-full justify-start">
          <TabsTrigger
            value="reasoning"
            className="data-[state=active]:bg-purple-500/30 data-[state=active]:text-white text-slate-400 text-xs"
          >
            <MessageSquare className="w-3 h-3 mr-1" />
            Reasoning
          </TabsTrigger>
          <TabsTrigger
            value="data"
            className="data-[state=active]:bg-purple-500/30 data-[state=active]:text-white text-slate-400 text-xs"
          >
            <Database className="w-3 h-3 mr-1" />
            Data
          </TabsTrigger>
          <TabsTrigger
            value="llm"
            className="data-[state=active]:bg-purple-500/30 data-[state=active]:text-white text-slate-400 text-xs"
          >
            <Brain className="w-3 h-3 mr-1" />
            LLM
          </TabsTrigger>
        </TabsList>

        <TabsContent value="reasoning" className="mt-3">
          <Card className="bg-slate-800/30 border-slate-700/50">
            <CardContent className="pt-3 pb-3 px-3">
              <div className="max-h-[400px] overflow-y-auto overflow-x-hidden">
                <pre className="text-xs text-slate-300 font-mono leading-relaxed" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                  {agent.reasoning}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="data" className="mt-3 space-y-2">
          {/* Agent Specific Data */}
          <Card className="bg-slate-800/30 border-slate-700/50">
            <CardHeader className="pb-2 pt-2.5 px-3">
              <CardTitle className="text-white text-xs font-semibold flex items-center gap-2">
                <BarChart3 className="w-3 h-3 text-purple-400" />
                Agent Specific Data
              </CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3">
              <div className="max-h-[400px] overflow-y-auto">
                <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono">
                  {JSON.stringify(agent.agent_specific_data, null, 2)}
                </pre>
              </div>
            </CardContent>
          </Card>

          {/* Market Data Snapshot */}
          {agent.market_data_snapshot && (
            <Card className="bg-slate-800/30 border-slate-700/50">
              <CardHeader className="pb-2 pt-2.5 px-3">
                <CardTitle className="text-white text-xs font-semibold flex items-center gap-2">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  Market Data Snapshot
                </CardTitle>
              </CardHeader>
              <CardContent className="px-3 pb-3">
                <div className="max-h-[400px] overflow-y-auto">
                  <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono">
                    {JSON.stringify(agent.market_data_snapshot, null, 2)}
                  </pre>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="llm" className="mt-3 space-y-2">
          {/* LLM Info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {agent.llm_provider && (
              <div className="bg-slate-800/30 rounded p-2">
                <div className="text-xs text-slate-500 mb-1">Provider</div>
                <div className="text-white text-xs font-medium">{agent.llm_provider}</div>
              </div>
            )}

            {agent.llm_model && (
              <div className="bg-slate-800/30 rounded p-2">
                <div className="text-xs text-slate-500 mb-1">Model</div>
                <div className="text-white text-xs font-medium break-all">{agent.llm_model}</div>
              </div>
            )}

            {agent.tokens_used && (
              <div className="bg-slate-800/30 rounded p-2">
                <div className="text-xs text-slate-500 mb-1">Tokens</div>
                <div className="text-white text-xs font-medium flex items-center gap-1">
                  <Zap className="w-3 h-3 text-amber-400" />
                  {agent.tokens_used.toLocaleString()}
                </div>
              </div>
            )}

            {agent.llm_cost !== null && (
              <div className="bg-slate-800/30 rounded p-2">
                <div className="text-xs text-slate-500 mb-1">Cost</div>
                <div className="text-white text-xs font-medium flex items-center gap-1">
                  <DollarSign className="w-3 h-3 text-emerald-400" />
                  ${agent.llm_cost.toFixed(4)}
                </div>
              </div>
            )}
          </div>

          {/* LLM Prompt */}
          {agent.llm_prompt && (
            <Card className="bg-slate-800/30 border-slate-700/50">
              <CardHeader className="pb-2 pt-2.5 px-3">
                <CardTitle className="text-white text-xs font-semibold flex items-center gap-2">
                  <Code2 className="w-3 h-3 text-blue-400" />
                  LLM Prompt
                </CardTitle>
              </CardHeader>
              <CardContent className="px-3 pb-3">
                <div className="max-h-[400px] overflow-y-auto overflow-x-hidden">
                  <pre className="text-xs text-slate-300 font-mono" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                    {agent.llm_prompt}
                  </pre>
                </div>
              </CardContent>
            </Card>
          )}

          {/* LLM Response */}
          {agent.llm_response && (
            <Card className="bg-slate-800/30 border-slate-700/50">
              <CardHeader className="pb-2 pt-2.5 px-3">
                <CardTitle className="text-white text-xs font-semibold flex items-center gap-2">
                  <Brain className="w-3 h-3 text-purple-400" />
                  LLM Response
                </CardTitle>
              </CardHeader>
              <CardContent className="px-3 pb-3">
                <div className="max-h-[400px] overflow-y-auto overflow-x-hidden">
                  <pre className="text-xs text-slate-300 font-mono" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                    {agent.llm_response}
                  </pre>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
