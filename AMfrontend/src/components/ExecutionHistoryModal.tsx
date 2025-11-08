import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Eye, ChevronLeft, ChevronRight } from "lucide-react";
import { fetchStrategyExecutions } from "../lib/marketplaceApi";

interface ExecutionHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  strategyId: string;
  strategyName: string;
  onViewDetail: (executionId: string) => void;
}

export function ExecutionHistoryModal({
  isOpen,
  onClose,
  strategyId,
  strategyName,
  onViewDetail,
}: ExecutionHistoryModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 50;

  useEffect(() => {
    if (isOpen && strategyId) {
      loadExecutions(currentPage);
    }
  }, [isOpen, strategyId, currentPage]);

  async function loadExecutions(page: number) {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchStrategyExecutions(strategyId, page, pageSize);
      setData(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load execution history');
      console.error('Failed to load execution history:', err);
    } finally {
      setLoading(false);
    }
  }

  function handlePrevPage() {
    if (data?.has_prev) {
      setCurrentPage(prev => prev - 1);
    }
  }

  function handleNextPage() {
    if (data?.has_next) {
      setCurrentPage(prev => prev + 1);
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-white">
            Execution History - {strategyName}
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-500 mx-auto mb-4"></div>
                <p className="text-slate-400">Loading execution history...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="text-red-400 mb-4">⚠️ Error</div>
                <p className="text-slate-400 text-sm mb-4">{error}</p>
                <Button
                  onClick={() => loadExecutions(currentPage)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  Try Again
                </Button>
              </div>
            </div>
          ) : data?.items?.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <p className="text-slate-400">No execution history found</p>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {data?.items?.map((execution: any, index: number) => (
                <div
                  key={execution.execution_id}
                  className="flex items-center justify-between p-3 bg-slate-800/30 rounded border border-slate-700/50 hover:border-purple-500/50 transition-all"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50 text-xs px-2 py-0.5">
                        {execution.agent}
                      </Badge>
                      <span className="text-xs text-slate-500">
                        {new Date(execution.date).toLocaleString(undefined, {
                          year: 'numeric',
                          month: 'numeric',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                    <div className="text-white text-sm mb-1">
                      {execution.signal === 'HOLD' ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/50 font-medium text-sm">
                          HOLD
                        </span>
                      ) : (
                        <>Signal: <span className="text-slate-300">{execution.signal}</span></>
                      )}
                    </div>

                    {/* Agent Contributions */}
                    {execution.agent_contributions && execution.agent_contributions.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {execution.agent_contributions.map((agent: any, idx: number) => (
                          <div key={idx} className="flex items-center gap-2 text-xs bg-slate-900/50 rounded px-2 py-1 border border-slate-700/30">
                            <span className="text-purple-400 font-medium w-28">{agent.display_name}</span>
                            <span className={`px-1.5 py-0.5 rounded font-medium ${
                              agent.signal === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-400' :
                              agent.signal === 'BEARISH' ? 'bg-red-500/20 text-red-400' :
                              'bg-slate-500/20 text-slate-400'
                            }`}>
                              {agent.signal}
                            </span>
                            <span className="text-slate-400">
                              Confidence: <span className="text-white">{(agent.confidence * 100).toFixed(0)}%</span>
                            </span>
                            <span className="text-slate-400">
                              Score: <span className={`font-medium ${
                                agent.score > 0 ? 'text-emerald-400' :
                                agent.score < 0 ? 'text-red-400' :
                                'text-slate-400'
                              }`}>{agent.score > 0 ? '+' : ''}{agent.score.toFixed(1)}</span>
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {execution.consecutive_count !== null && execution.consecutive_count !== undefined && execution.consecutive_count > 0 && (
                      <div className={`px-1.5 py-0.5 rounded text-xs font-medium border ${
                        execution.signal === 'BUY'
                          ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'  // 看涨：绿色
                          : execution.signal === 'SELL'
                          ? 'bg-red-500/20 text-red-400 border-red-500/50'  // 看跌：红色
                          : 'bg-blue-500/20 text-blue-400 border-blue-500/50'  // 默认：蓝色
                      }`}>
                        {execution.consecutive_count}x
                      </div>
                    )}
                    {execution.conviction_score !== null && (
                      <div className={`text-base font-medium ${
                        execution.conviction_score < 30 ? 'text-orange-500' :
                        execution.conviction_score > 70 ? 'text-emerald-400' :
                        'text-purple-400'
                      }`}>
                        {execution.conviction_score.toFixed(1)}%
                      </div>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onViewDetail(execution.execution_id)}
                      className="h-8 px-3 text-xs bg-purple-500/10 border-purple-500/50 text-purple-400 hover:bg-purple-500/20"
                    >
                      <Eye className="w-3.5 h-3.5 mr-1" />
                      View
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination */}
        {data && data.total > 0 && (
          <div className="flex items-center justify-between pt-4 border-t border-slate-700">
            <div className="text-sm text-slate-400">
              Showing {((data.page - 1) * data.page_size) + 1} to {Math.min(data.page * data.page_size, data.total)} of {data.total} executions
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={handlePrevPage}
                disabled={!data.has_prev || loading}
                className="h-8 px-3 bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Previous
              </Button>
              <div className="text-sm text-slate-400">
                Page {data.page} of {data.total_pages}
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={handleNextPage}
                disabled={!data.has_next || loading}
                className="h-8 px-3 bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </div>
        )}

        <div className="flex justify-end pt-4 border-t border-slate-700">
          <Button
            onClick={onClose}
            variant="outline"
            className="bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
