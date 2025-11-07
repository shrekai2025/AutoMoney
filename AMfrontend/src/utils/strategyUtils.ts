/**
 * Strategy Utility Functions
 * 策略相关的工具函数
 */

import type {
  PerformanceHistory,
  PerformanceDataPoint,
} from '../types/strategy';
import { Eye, Database, Zap, Activity } from 'lucide-react';

/**
 * 转换性能历史数据为图表格式
 * 后端返回的是分离的数组，前端需要合并为对象数组
 */
export function convertPerformanceHistory(
  history: PerformanceHistory
): PerformanceDataPoint[] {
  return history.dates.map((date, index) => ({
    date,
    strategy: history.strategy[index],
    btc: history.btc_benchmark[index],
    eth: history.eth_benchmark[index],
  }));
}

/**
 * 映射 Agent 角色到图标
 */
export function getAgentIcon(role: string) {
  const iconMap: Record<string, any> = {
    MacroAgent: Eye,
    OnChainAgent: Database,
    TAAgent: Zap,
    // Also support lowercase with underscore format
    macro_agent: Eye,
    onchain_agent: Database,
    ta_agent: Zap,
  };
  return iconMap[role] || Activity;
}

/**
 * 映射 Agent 角色到颜色
 */
export function getAgentColor(role: string): string {
  const colorMap: Record<string, string> = {
    MacroAgent: 'blue',
    OnChainAgent: 'emerald',
    TAAgent: 'amber',
    // Also support lowercase with underscore format
    macro_agent: 'blue',
    onchain_agent: 'emerald',
    ta_agent: 'amber',
  };
  return colorMap[role] || 'slate';
}

/**
 * 格式化大数字（用于显示资金池规模）
 */
export function formatPoolSize(size: number): string {
  if (size >= 1_000_000) {
    return `$${(size / 1_000_000).toFixed(1)}M`;
  } else if (size >= 1_000) {
    return `$${(size / 1_000).toFixed(1)}K`;
  } else {
    return `$${size.toFixed(2)}`;
  }
}

/**
 * 格式化百分比
 */
export function formatPercent(value: number, showSign: boolean = false): string {
  const formatted = `${value.toFixed(2)}%`;
  if (showSign && value > 0) {
    return `+${formatted}`;
  }
  return formatted;
}

/**
 * 获取风险等级显示文本
 */
export function getRiskLevelText(riskLevel: string): string {
  const textMap: Record<string, string> = {
    low: 'Low Risk',
    medium: 'Medium Risk',
    'medium-high': 'Medium-High Risk',
    high: 'High Risk',
  };
  return textMap[riskLevel] || riskLevel;
}

/**
 * 获取风险等级颜色
 */
export function getRiskLevelColor(riskLevel: string): string {
  const colorMap: Record<string, string> = {
    low: 'text-emerald-400',
    medium: 'text-amber-400',
    'medium-high': 'text-orange-400',
    high: 'text-red-400',
  };
  return colorMap[riskLevel] || 'text-slate-400';
}
