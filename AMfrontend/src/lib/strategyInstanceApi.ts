/**
 * Strategy Instance API - 策略实例管理API
 */

import apiClient from './api';

// ========== Types ==========

export interface StrategyDefinition {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  decision_agent_module: string;
  decision_agent_class: string;
  business_agents: string[];
  trade_channel: string;
  trade_symbol: string;
  rebalance_period_minutes: number;
  default_params: any;
  is_active: boolean;
}

export interface CreateInstanceRequest {
  strategy_definition_id: number;
  instance_name?: string;
  instance_description?: string;
  initial_balance: number;
  instance_params?: any;
  tags?: string[];
  risk_level?: string;
}

export interface CreateInstanceResponse {
  success: boolean;
  portfolio_id: string;
  instance_name: string;
  strategy_definition_id: number;
  initial_balance: number;
  created_at: string;
}

// ========== API Functions ==========

/**
 * 获取所有策略定义（模板）
 */
export async function fetchStrategyDefinitions(): Promise<StrategyDefinition[]> {
  const response = await apiClient.get<{ definitions: StrategyDefinition[]; total: number }>(
    '/api/v1/strategy-definitions/'
  );

  // Backend returns { definitions: [...], total: N }
  return response.data.definitions || [];
}

/**
 * 创建新的策略实例
 */
export async function createStrategyInstance(
  data: CreateInstanceRequest
): Promise<CreateInstanceResponse> {
  const response = await apiClient.post<CreateInstanceResponse>('/api/v1/strategies/', data);
  return response.data;
}
