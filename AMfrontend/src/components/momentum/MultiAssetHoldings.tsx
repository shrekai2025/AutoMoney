/**
 * MultiAssetHoldings - 多币种持仓展示组件
 * 
 * 支持BTC/ETH/SOL多币种持仓,带OCO订单状态
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Coins, TrendingUp, TrendingDown } from "lucide-react";
import { OCOOrderStatus } from "./OCOOrderStatus";

// 币种配置
const ASSET_CONFIG = {
  BTC: { name: "Bitcoin", color: "#f7931a", emoji: "₿" },
  ETH: { name: "Ethereum", color: "#627eea", emoji: "Ξ" },
  SOL: { name: "Solana", color: "#14f195", emoji: "◎" },
};

interface OCOOrder {
  stop_loss_price: number;
  take_profit_price: number;
  entry_price: number;
  side: "LONG" | "SHORT";
  created_at: string;
}

interface MomentumHolding {
  symbol: string;
  amount: number;
  avg_buy_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  oco_order: OCOOrder | null;
}

interface MultiAssetHoldingsProps {
  holdings: MomentumHolding[];
  totalValue: number;
}

export function MultiAssetHoldings({ holdings, totalValue }: MultiAssetHoldingsProps) {
  const [selectedAsset, setSelectedAsset] = useState<string>("ALL");

  // 按币种分组
  const groupedHoldings = holdings.reduce((acc, holding) => {
    const asset = holding.symbol;
    if (!acc[asset]) acc[asset] = [];
    acc[asset].push(holding);
    return acc;
  }, {} as Record<string, MomentumHolding[]>);

  // 计算每个币种的总价值和盈亏
  const assetSummary = Object.entries(groupedHoldings).map(([asset, holdings]) => {
    const totalValue = holdings.reduce((sum, h) => sum + h.market_value, 0);
    const totalPnl = holdings.reduce((sum, h) => sum + h.unrealized_pnl, 0);
    const totalPnlPercent = totalPnl / (totalValue - totalPnl) * 100;
    return { asset, totalValue, totalPnl, totalPnlPercent, holdings };
  });

  // 过滤显示的持仓
  const filteredHoldings = selectedAsset === "ALL"
    ? holdings
    : groupedHoldings[selectedAsset] || [];

  return (
    <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <Coins className="w-4 h-4 text-purple-400" />
            Multi-Asset Holdings
          </CardTitle>
          <div className="text-slate-400 text-xs">
            Total: <span className="text-white font-bold">${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* 币种Tab切换 */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setSelectedAsset("ALL")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
              selectedAsset === "ALL"
                ? "bg-purple-600 text-white"
                : "bg-slate-800/50 text-slate-400 hover:bg-slate-700/50"
            }`}
          >
            All Assets
          </button>
          {assetSummary.map(({ asset, totalValue, totalPnl, totalPnlPercent }) => {
            const config = ASSET_CONFIG[asset as keyof typeof ASSET_CONFIG];
            return (
              <button
                key={asset}
                onClick={() => setSelectedAsset(asset)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-2 ${
                  selectedAsset === asset
                    ? "bg-slate-700 text-white border-2"
                    : "bg-slate-800/50 text-slate-400 hover:bg-slate-700/50"
                }`}
                style={{
                  borderColor: selectedAsset === asset ? config?.color : "transparent",
                }}
              >
                <span style={{ color: config?.color }}>{config?.emoji}</span>
                <span>{asset}</span>
                <span className={totalPnl >= 0 ? "text-green-400" : "text-red-400"}>
                  {totalPnl >= 0 ? "+" : ""}{totalPnlPercent.toFixed(1)}%
                </span>
              </button>
            );
          })}
        </div>

        {/* 持仓列表 */}
        <div className="space-y-3">
          {filteredHoldings.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <Coins className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No holdings in this asset</p>
            </div>
          ) : (
            filteredHoldings.map((holding, idx) => {
              const config = ASSET_CONFIG[holding.symbol as keyof typeof ASSET_CONFIG];
              const pnlPositive = holding.unrealized_pnl >= 0;

              return (
                <div
                  key={idx}
                  className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/50 space-y-3"
                >
                  {/* 持仓Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {/* 币种标识 */}
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-xl font-bold"
                        style={{
                          backgroundColor: `${config?.color}20`,
                          color: config?.color,
                        }}
                      >
                        {config?.emoji}
                      </div>
                      
                      {/* 币种信息 */}
                      <div>
                        <div className="text-white font-medium">{holding.symbol}</div>
                        <div className="text-slate-400 text-xs">{config?.name}</div>
                      </div>
                    </div>

                    {/* 盈亏显示 */}
                    <div className="text-right">
                      <div className={`font-bold ${pnlPositive ? "text-green-400" : "text-red-400"}`}>
                        {pnlPositive ? <TrendingUp className="w-4 h-4 inline" /> : <TrendingDown className="w-4 h-4 inline" />}
                        {pnlPositive ? "+" : ""}${holding.unrealized_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                      <div className={`text-xs ${pnlPositive ? "text-green-400" : "text-red-400"}`}>
                        ({pnlPositive ? "+" : ""}{holding.unrealized_pnl_percent.toFixed(2)}%)
                      </div>
                    </div>
                  </div>

                  {/* 持仓详情 */}
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="bg-slate-700/30 rounded p-2">
                      <div className="text-slate-400 mb-1">Amount</div>
                      <div className="text-white font-mono">{holding.amount.toFixed(6)}</div>
                    </div>
                    <div className="bg-slate-700/30 rounded p-2">
                      <div className="text-slate-400 mb-1">Avg Buy</div>
                      <div className="text-white font-mono">${holding.avg_buy_price.toLocaleString()}</div>
                    </div>
                    <div className="bg-slate-700/30 rounded p-2">
                      <div className="text-slate-400 mb-1">Current</div>
                      <div className="text-white font-mono">${holding.current_price.toLocaleString()}</div>
                    </div>
                  </div>

                  {/* OCO订单状态 */}
                  {holding.oco_order ? (
                    <OCOOrderStatus
                      entryPrice={holding.oco_order.entry_price}
                      currentPrice={holding.current_price}
                      stopLossPrice={holding.oco_order.stop_loss_price}
                      takeProfitPrice={holding.oco_order.take_profit_price}
                      side={holding.oco_order.side}
                      symbol={holding.symbol}
                    />
                  ) : (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-2 text-center">
                      <span className="text-yellow-400 text-xs">
                        ⚠️ No OCO protection active
                      </span>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Summary */}
        {filteredHoldings.length > 0 && (
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/30">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <div className="text-slate-400 mb-1">Total Position Value</div>
                <div className="text-white font-bold text-lg">
                  ${filteredHoldings.reduce((sum, h) => sum + h.market_value, 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div>
                <div className="text-slate-400 mb-1">Total Unrealized P&L</div>
                <div className={`font-bold text-lg ${
                  filteredHoldings.reduce((sum, h) => sum + h.unrealized_pnl, 0) >= 0
                    ? "text-green-400"
                    : "text-red-400"
                }`}>
                  {filteredHoldings.reduce((sum, h) => sum + h.unrealized_pnl, 0) >= 0 ? "+" : ""}
                  ${filteredHoldings.reduce((sum, h) => sum + h.unrealized_pnl, 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

