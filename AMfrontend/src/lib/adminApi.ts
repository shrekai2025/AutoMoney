/**
 * Admin API Service
 * 管理员功能 API 调用服务
 */

import apiClient from './api';

export interface AdminStrategy {
  id: string;
  user_id: number;
  name: string;
  strategy_name: string;
  is_active: boolean;
  total_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  rebalance_period_minutes: number;
  agent_weights?: {
    macro: number;
    onchain: number;
    ta: number;
  };
  consecutive_signal_threshold?: number;
  acceleration_multiplier_min?: number;
  acceleration_multiplier_max?: number;
  created_at: string;
  updated_at: string | null;
}

export interface AdminStrategyListResponse {
  total: number;
  strategies: AdminStrategy[];
}

export interface StrategyToggleRequest {
  is_active: boolean;
}

export interface StrategyToggleResponse {
  success: boolean;
  portfolio_id: string;
  is_active: boolean;
  message: string;
}

/**
 * 获取所有策略列表（仅管理员）
 */
export async function fetchAllStrategies(): Promise<AdminStrategyListResponse> {
  const response = await apiClient.get<AdminStrategyListResponse>(
    '/api/v1/admin/strategies'
  );
  return response.data;
}

/**
 * 切换策略的激活状态（仅管理员）
 * @param strategyId - 策略 ID
 * @param isActive - 目标状态
 */
export async function toggleStrategy(
  strategyId: string,
  isActive: boolean
): Promise<StrategyToggleResponse> {
  const response = await apiClient.patch<StrategyToggleResponse>(
    `/api/v1/admin/strategies/${strategyId}/toggle`,
    { is_active: isActive }
  );
  return response.data;
}
