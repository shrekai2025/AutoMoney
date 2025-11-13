/**
 * OCOOrderStatus - OCO订单状态显示组件
 * 
 * 显示止损、当前价、止盈的价格和距离百分比
 */

import { Shield, TrendingDown, TrendingUp } from "lucide-react";

interface OCOOrderStatusProps {
  entryPrice: number;
  currentPrice: number;
  stopLossPrice: number;
  takeProfitPrice: number;
  side: "LONG" | "SHORT";
  symbol: string;
}

export function OCOOrderStatus({
  entryPrice,
  currentPrice,
  stopLossPrice,
  takeProfitPrice,
  side,
  symbol,
}: OCOOrderStatusProps) {
  
  // 计算距离百分比
  const distanceToSL = ((currentPrice - stopLossPrice) / currentPrice) * 100;
  const distanceToTP = ((takeProfitPrice - currentPrice) / currentPrice) * 100;
  
  // 计算当前盈亏百分比
  const pnlPercent = side === "LONG"
    ? ((currentPrice - entryPrice) / entryPrice) * 100
    : ((entryPrice - currentPrice) / entryPrice) * 100;

  // 计算进度条位置 (止损0% - 止盈100%)
  const totalRange = Math.abs(takeProfitPrice - stopLossPrice);
  const currentPosition = side === "LONG"
    ? ((currentPrice - stopLossPrice) / totalRange) * 100
    : ((stopLossPrice - currentPrice) / totalRange) * 100;
  
  const safePosition = Math.max(0, Math.min(100, currentPosition));

  // 根据PnL确定颜色
  const pnlColor = pnlPercent >= 0 ? "text-green-400" : "text-red-400";
  const pnlBg = pnlPercent >= 0 ? "bg-green-500/10" : "bg-red-500/10";

  return (
    <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/50 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-purple-400" />
          <span className="text-slate-300 text-sm font-medium">OCO Order Protection</span>
        </div>
        <div className={`${pnlBg} ${pnlColor} px-2 py-0.5 rounded text-xs font-bold`}>
          {pnlPercent >= 0 ? "+" : ""}{pnlPercent.toFixed(2)}%
        </div>
      </div>

      {/* 价格进度条 */}
      <div className="relative">
        {/* 进度条轨道 */}
        <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
          {/* 渐变填充 */}
          <div
            className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 transition-all duration-500"
            style={{ width: `${safePosition}%` }}
          />
        </div>
        
        {/* 当前位置指示器 */}
        <div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
          style={{ left: `${safePosition}%` }}
        >
          <div className="w-4 h-4 bg-white border-2 border-purple-500 rounded-full shadow-lg animate-pulse" />
        </div>
      </div>

      {/* 三个价格点 */}
      <div className="grid grid-cols-3 gap-2">
        {/* 止损价 */}
        <div className="bg-red-500/10 border border-red-500/30 rounded p-2">
          <div className="flex items-center gap-1 mb-1">
            <TrendingDown className="w-3 h-3 text-red-400" />
            <span className="text-red-400 text-xs font-medium">Stop Loss</span>
          </div>
          <div className="text-white font-mono text-sm">
            ${stopLossPrice.toLocaleString()}
          </div>
          <div className="text-red-400 text-xs mt-0.5">
            {side === "LONG" ? distanceToSL.toFixed(2) : (-distanceToSL).toFixed(2)}%
          </div>
        </div>

        {/* 当前价 */}
        <div className="bg-purple-500/10 border border-purple-500/30 rounded p-2">
          <div className="text-purple-400 text-xs font-medium mb-1">
            Current
          </div>
          <div className="text-white font-mono text-sm font-bold">
            ${currentPrice.toLocaleString()}
          </div>
          <div className={`${pnlColor} text-xs mt-0.5`}>
            Entry: ${entryPrice.toLocaleString()}
          </div>
        </div>

        {/* 止盈价 */}
        <div className="bg-green-500/10 border border-green-500/30 rounded p-2">
          <div className="flex items-center gap-1 mb-1">
            <TrendingUp className="w-3 h-3 text-green-400" />
            <span className="text-green-400 text-xs font-medium">Take Profit</span>
          </div>
          <div className="text-white font-mono text-sm">
            ${takeProfitPrice.toLocaleString()}
          </div>
          <div className="text-green-400 text-xs mt-0.5">
            +{distanceToTP.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* 风险回报比 */}
      <div className="flex items-center justify-between text-xs bg-slate-700/30 rounded p-2">
        <span className="text-slate-400">Risk/Reward Ratio:</span>
        <span className="text-white font-medium">
          {(Math.abs(distanceToTP) / Math.abs(side === "LONG" ? distanceToSL : -distanceToSL)).toFixed(2)}:1
        </span>
      </div>
    </div>
  );
}

