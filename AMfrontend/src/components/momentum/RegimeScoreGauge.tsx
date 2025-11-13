/**
 * RegimeScoreGauge - Regime分数仪表盘组件
 * 
 * 显示当前市场环境评分(0-100)和推荐仓位乘数
 */

import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface RegimeScoreGaugeProps {
  score: number;              // 0-100
  classification: string;     // DANGEROUS/NEUTRAL/HEALTHY/VERY_HEALTHY
  recommendedMultiplier: number;  // 0.3-1.6
  timestamp?: string;
}

export function RegimeScoreGauge({
  score,
  classification,
  recommendedMultiplier,
  timestamp,
}: RegimeScoreGaugeProps) {
  
  // 根据分数确定颜色
  const getScoreColor = (score: number): string => {
    if (score < 20) return "#ef4444"; // 红色 - 极度危险
    if (score < 40) return "#f59e0b"; // 橙色 - 危险
    if (score < 60) return "#eab308"; // 黄色 - 中性
    if (score < 80) return "#10b981"; // 浅绿 - 健康
    return "#22c55e";                  // 深绿 - 极度健康
  };

  // 根据分类获取显示文本和图标
  const getClassificationDisplay = (classification: string) => {
    const map: Record<string, { label: string; emoji: string; color: string }> = {
      "DANGEROUS": { label: "危险", emoji: "🔴", color: "bg-red-500/20 text-red-400 border-red-500/50" },
      "NEUTRAL": { label: "中性", emoji: "🟡", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50" },
      "HEALTHY": { label: "健康", emoji: "🟢", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50" },
      "VERY_HEALTHY": { label: "极度健康", emoji: "💚", color: "bg-green-500/20 text-green-400 border-green-500/50" },
    };
    return map[classification] || { label: classification, emoji: "⚪", color: "bg-slate-500/20 text-slate-400" };
  };

  const scoreColor = getScoreColor(score);
  const classificationDisplay = getClassificationDisplay(classification);
  
  // 计算仪表盘角度 (0-180度)
  const needleAngle = (score / 100) * 180;
  
  // SVG仪表盘路径
  const radius = 80;
  const cx = 100;
  const cy = 100;
  const strokeWidth = 12;

  // 创建分段弧线 (5个区间)
  const segments = [
    { start: 0, end: 20, color: "#ef4444" },    // 红色
    { start: 20, end: 40, color: "#f59e0b" },   // 橙色
    { start: 40, end: 60, color: "#eab308" },   // 黄色
    { start: 60, end: 80, color: "#10b981" },   // 浅绿
    { start: 80, end: 100, color: "#22c55e" },  // 深绿
  ];

  // 生成弧线路径
  const polarToCartesian = (angle: number) => {
    const rad = ((angle - 90) * Math.PI) / 180;
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    };
  };

  const createArc = (startAngle: number, endAngle: number) => {
    const start = polarToCartesian(startAngle);
    const end = polarToCartesian(endAngle);
    const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`;
  };

  return (
    <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-white text-sm flex items-center gap-2">
          <Activity className="w-4 h-4 text-purple-400" />
          Market Regime Score
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* SVG仪表盘 */}
        <div className="relative flex justify-center">
          <svg width="200" height="120" viewBox="0 0 200 120" className="overflow-visible">
            {/* 背景轨道 */}
            <path
              d={createArc(0, 180)}
              fill="none"
              stroke="#1e293b"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />
            
            {/* 分段颜色弧线 */}
            {segments.map((segment, idx) => {
              const startAngle = (segment.start / 100) * 180;
              const endAngle = (segment.end / 100) * 180;
              return (
                <path
                  key={idx}
                  d={createArc(startAngle, endAngle)}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth={strokeWidth}
                  strokeLinecap="round"
                  opacity={0.6}
                />
              );
            })}

            {/* 当前分数高亮弧线 */}
            <path
              d={createArc(0, needleAngle)}
              fill="none"
              stroke={scoreColor}
              strokeWidth={strokeWidth + 2}
              strokeLinecap="round"
            />

            {/* 指针 */}
            <g transform={`rotate(${needleAngle - 90} ${cx} ${cy})`}>
              <circle cx={cx} cy={cy} r="6" fill={scoreColor} />
              <line
                x1={cx}
                y1={cy}
                x2={cx + radius - 10}
                y2={cy}
                stroke={scoreColor}
                strokeWidth="3"
                strokeLinecap="round"
              />
            </g>

            {/* 中心分数显示 */}
            <text
              x={cx}
              y={cy + 25}
              textAnchor="middle"
              className="fill-white font-bold"
              style={{ fontSize: "32px" }}
            >
              {score.toFixed(0)}
            </text>
            <text
              x={cx}
              y={cy + 40}
              textAnchor="middle"
              className="fill-slate-400"
              style={{ fontSize: "12px" }}
            >
              / 100
            </text>
          </svg>
        </div>

        {/* 分类和乘数信息 */}
        <div className="grid grid-cols-2 gap-2">
          {/* 市场分类 */}
          <div className="bg-slate-800/30 rounded-lg p-2 border border-slate-700/50">
            <div className="text-slate-400 text-xs mb-1">Market State</div>
            <Badge className={`${classificationDisplay.color} text-xs`}>
              {classificationDisplay.emoji} {classificationDisplay.label}
            </Badge>
          </div>

          {/* 推荐乘数 */}
          <div className="bg-slate-800/30 rounded-lg p-2 border border-slate-700/50">
            <div className="text-slate-400 text-xs mb-1">Position Multiplier</div>
            <div className="text-white font-bold text-lg">
              {recommendedMultiplier.toFixed(2)}x
            </div>
          </div>
        </div>

        {/* 时间戳 */}
        {timestamp && (
          <div className="text-slate-500 text-xs text-center">
            Updated: {new Date(timestamp).toLocaleTimeString()}
          </div>
        )}

        {/* 说明文字 */}
        <div className="bg-slate-800/50 rounded p-2 border border-slate-700/30">
          <p className="text-slate-400 text-xs leading-relaxed">
            Regime Score评估市场环境健康度。分数越高,仓位乘数越大(0.3x-1.6x)。
            低于25时拒绝逆势做多以保护资金。
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

