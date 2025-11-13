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
  fg_circuit_breaker_threshold?: number;
  fg_position_adjust_threshold?: number;
  buy_threshold?: number;
  full_sell_threshold?: number;
  // 注意: partial_sell_threshold 已移除，部分减仓区间现在是 [full_sell_threshold, buy_threshold)
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

/**
 * 策略实例参数接口
 */
export interface StrategyInstanceParams {
  agent_weights?: { macro: number; onchain: number; ta: number };
  consecutive_signal_threshold?: number;
  acceleration_multiplier_min?: number;
  acceleration_multiplier_max?: number;
  fg_circuit_breaker_threshold?: number;
  fg_position_adjust_threshold?: number;
  buy_threshold?: number;
  full_sell_threshold?: number;
  // 注意: partial_sell_threshold 已移除，部分减仓区间现在是 [full_sell_threshold, buy_threshold)
}

/**
 * 更新策略实例参数（完整版本）
 * @param strategyId - 策略实例 ID
 * @param instanceParams - 实例参数（所有参数都是可选的）
 *
 * 注意: rebalance_period_minutes 已移至策略模板级别
 */
export async function updateStrategyParams(
  strategyId: string,
  instanceParams: StrategyInstanceParams
): Promise<{ success: boolean; message: string }> {
  const params: any = {};

  // 只添加提供的参数
  // 注意: agent_weights是对象，需要JSON序列化后作为字符串传递
  if (instanceParams.agent_weights !== undefined) {
    params.agent_weights = JSON.stringify(instanceParams.agent_weights);
  }
  if (instanceParams.consecutive_signal_threshold !== undefined) {
    params.consecutive_signal_threshold = instanceParams.consecutive_signal_threshold;
  }
  if (instanceParams.acceleration_multiplier_min !== undefined) {
    params.acceleration_multiplier_min = instanceParams.acceleration_multiplier_min;
  }
  if (instanceParams.acceleration_multiplier_max !== undefined) {
    params.acceleration_multiplier_max = instanceParams.acceleration_multiplier_max;
  }
  if (instanceParams.fg_circuit_breaker_threshold !== undefined) {
    params.fg_circuit_breaker_threshold = instanceParams.fg_circuit_breaker_threshold;
  }
  if (instanceParams.fg_position_adjust_threshold !== undefined) {
    params.fg_position_adjust_threshold = instanceParams.fg_position_adjust_threshold;
  }
  if (instanceParams.buy_threshold !== undefined) {
    params.buy_threshold = instanceParams.buy_threshold;
  }
  if (instanceParams.full_sell_threshold !== undefined) {
    params.full_sell_threshold = instanceParams.full_sell_threshold;
  }

  const response = await apiClient.patch(
    `/api/v1/admin/strategies/${strategyId}/params`,
    null,
    { params }
  );

  return response.data;
}

// ============ 策略模板管理 ============

export interface StrategyTemplate {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  rebalance_period_minutes: number;
  business_agents: string[];
  instance_count: number;
  is_active: boolean;
}

export interface StrategyTemplateListResponse {
  total: number;
  templates: StrategyTemplate[];
}

/**
 * 获取所有策略模板（仅管理员）
 */
export async function fetchStrategyTemplates(): Promise<StrategyTemplateListResponse> {
  const response = await apiClient.get<StrategyTemplateListResponse>(
    '/api/v1/admin/strategy-templates'
  );
  return response.data;
}

/**
 * 更新策略模板参数（仅管理员）
 * @param templateId - 模板 ID
 * @param rebalancePeriodMinutes - Rebalance周期（分钟）
 */
export async function updateTemplateParams(
  templateId: number,
  rebalancePeriodMinutes: number
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.patch(
    `/api/v1/admin/strategy-templates/${templateId}/params`,
    null,
    { params: { rebalance_period_minutes: rebalancePeriodMinutes } }
  );
  return response.data;
}
