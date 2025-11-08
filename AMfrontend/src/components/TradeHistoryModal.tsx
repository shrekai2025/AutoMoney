import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { DollarSign, ChevronLeft, ChevronRight } from "lucide-react";

interface Trade {
  id: string;
  symbol: string;
  trade_type: "BUY" | "SELL";
  amount: number;
  price: number;
  total_value: number;
  fee: number;
  balance_before: number | null;
  balance_after: number | null;
  holding_before: number | null;
  holding_after: number | null;
  realized_pnl: number | null;
  realized_pnl_percent: number | null;
  conviction_score: number | null;
  reason: string | null;
  executed_at: string;
}

interface TradeHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioId: string;
}

export function TradeHistoryModal({
  isOpen,
  onClose,
  portfolioId,
}: TradeHistoryModalProps) {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    if (isOpen && portfolioId) {
      loadTrades();
    }
  }, [isOpen, portfolioId, currentPage]);

  const loadTrades = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `/api/v1/marketplace/${portfolioId}/trades?page=${currentPage}&page_size=${pageSize}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to load trades");
      }

      const data = await response.json();
      setTrades(data.items || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error("Error loading trades:", error);
    } finally {
      setLoading(false);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-400" />
            Trade History
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="text-center text-slate-400 py-8">Loading trades...</div>
        ) : trades.length === 0 ? (
          <div className="text-center text-slate-400 py-8">No trades found</div>
        ) : (
          <div className="space-y-3">
            {trades.map((trade) => (
              <div
                key={trade.id}
                className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50"
              >
                {/* Trade Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Badge
                      className={`text-xs ${
                        trade.trade_type === "BUY"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/50"
                          : "bg-red-500/20 text-red-400 border-red-500/50"
                      }`}
                    >
                      {trade.trade_type} {trade.symbol}
                    </Badge>
                    {trade.conviction_score !== null && (
                      <span className="text-xs text-slate-400">
                        Conviction: <span className="text-white">{trade.conviction_score.toFixed(1)}</span>
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400">
                    {new Date(trade.executed_at).toLocaleString()}
                  </div>
                </div>

                {/* Trade Details Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
                  <div className="bg-slate-900/50 rounded p-2">
                    <div className="text-xs text-slate-500 mb-0.5">Amount</div>
                    <div className="text-white text-sm font-medium">
                      {Number(trade.amount).toFixed(8)} {trade.symbol}
                    </div>
                  </div>

                  <div className="bg-slate-900/50 rounded p-2">
                    <div className="text-xs text-slate-500 mb-0.5">Price</div>
                    <div className="text-white text-sm font-medium">
                      ${Number(trade.price).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </div>
                  </div>

                  <div className="bg-slate-900/50 rounded p-2">
                    <div className="text-xs text-slate-500 mb-0.5">Total Value</div>
                    <div className="text-white text-sm font-medium">
                      ${Number(trade.total_value).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </div>
                  </div>

                  <div className="bg-slate-900/50 rounded p-2">
                    <div className="text-xs text-slate-500 mb-0.5">Fee</div>
                    <div className="text-white text-sm font-medium">
                      ${Number(trade.fee).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </div>
                  </div>
                </div>

                {/* Balance Changes */}
                {(trade.balance_before !== null || trade.holding_before !== null) && (
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    {trade.balance_before !== null && trade.balance_after !== null && (
                      <div className="bg-slate-900/50 rounded p-2">
                        <div className="text-xs text-slate-500 mb-0.5">Cash Balance</div>
                        <div className="text-white text-sm">
                          ${Number(trade.balance_before).toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}{" "}
                          →{" "}
                          ${Number(trade.balance_after).toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </div>
                      </div>
                    )}

                    {trade.holding_before !== null && trade.holding_after !== null && (
                      <div className="bg-slate-900/50 rounded p-2">
                        <div className="text-xs text-slate-500 mb-0.5">{trade.symbol} Holding</div>
                        <div className="text-white text-sm">
                          {Number(trade.holding_before).toFixed(8)} →{" "}
                          {Number(trade.holding_after).toFixed(8)}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* PnL for SELL trades */}
                {trade.trade_type === "SELL" && trade.realized_pnl !== null && (
                  <div className="bg-slate-900/50 rounded p-2 mb-3">
                    <div className="text-xs text-slate-500 mb-0.5">Realized PnL</div>
                    <div
                      className={`text-sm font-semibold ${
                        Number(trade.realized_pnl) >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {Number(trade.realized_pnl) >= 0 ? "+" : ""}$
                      {Number(trade.realized_pnl).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                      {trade.realized_pnl_percent !== null && (
                        <span className="ml-1">
                          ({Number(trade.realized_pnl_percent) >= 0 ? "+" : ""}
                          {Number(trade.realized_pnl_percent).toFixed(2)}%)
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Reason */}
                {trade.reason && (
                  <div className="bg-slate-900/50 rounded p-2">
                    <div className="text-xs text-slate-500 mb-0.5">Reason</div>
                    <div className="text-white text-xs">{trade.reason}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-700">
            <Button
              onClick={handlePrevPage}
              disabled={currentPage === 1}
              variant="outline"
              size="sm"
              className="bg-slate-800 border-slate-700 text-white hover:bg-slate-700"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </Button>
            <span className="text-sm text-slate-400">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              onClick={handleNextPage}
              disabled={currentPage >= totalPages}
              variant="outline"
              size="sm"
              className="bg-slate-800 border-slate-700 text-white hover:bg-slate-700"
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
