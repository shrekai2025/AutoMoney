/**
 * Strategy Marketplace API Service
 * 策略市场 API 调用服务
 */

import apiClient from './api';
import type {
  MarketplaceResponse,
  StrategyDetail,
  StrategyExecutionDetail,
} from '../types/strategy';

/**
 * 获取策略市场列表
 * @param sortBy - 排序方式: 'return' | 'risk' | 'tvl' | 'sharpe'
 * @param riskLevel - 风险等级过滤: 'low' | 'medium' | 'medium-high' | 'high'
 */
export async function fetchMarketplaceStrategies(
  sortBy: string = 'return',
  riskLevel?: string
): Promise<MarketplaceResponse> {
  const params = new URLSearchParams({
    sort_by: sortBy,
  });

  if (riskLevel && riskLevel !== 'all') {
    params.append('risk_level', riskLevel);
  }

  // 使用新的 /strategies 接口（带尾部斜杠以避免重定向）
  const response = await apiClient.get<MarketplaceResponse>(
    `/api/v1/strategies/?${params.toString()}`
  );

  return response.data;
}

/**
 * 获取策略详情
 * @param strategyId - 策略 ID (UUID)
 */
export async function fetchStrategyDetail(
  strategyId: string
): Promise<StrategyDetail> {
  const response = await apiClient.get<StrategyDetail>(
    `/api/v1/strategies/${strategyId}`
  );

  return response.data;
}

/**
 * 部署资金到策略 (占位实现)
 * @param strategyId - 策略 ID
 * @param amount - 金额
 */
export async function deployFunds(
  strategyId: string,
  amount: number
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post(
    `/api/v1/strategies/${strategyId}/deploy`,
    null,
    {
      params: { amount },
    }
  );

  return response.data;
}

/**
 * 从策略提现资金 (占位实现)
 * @param strategyId - 策略 ID
 * @param amount - 金额
 */
export async function withdrawFunds(
  strategyId: string,
  amount: number
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post(
    `/api/v1/strategies/${strategyId}/withdraw`,
    null,
    {
      params: { amount },
    }
  );

  return response.data;
}

/**
 * 获取策略执行详情
 * @param executionId - 执行记录 ID (UUID)
 */
export async function fetchExecutionDetail(
  executionId: string
): Promise<StrategyExecutionDetail> {
  const response = await apiClient.get<StrategyExecutionDetail>(
    `/api/v1/strategies/executions/${executionId}`
  );

  return response.data;
}

/**
 * 获取策略执行历史列表（分页）
 * @param strategyId - 策略 ID (UUID)
 * @param page - 页码（从1开始）
 * @param pageSize - 每页数量（默认50）
 */
export async function fetchStrategyExecutions(
  strategyId: string,
  page: number = 1,
  pageSize: number = 50
): Promise<{
  items: Array<{
    execution_id: string;
    date: string;
    signal: string;
    action: string;
    result: string;
    agent: string;
    conviction_score: number | null;
    signal_strength: number | null;
  }>;
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}> {
  const response = await apiClient.get(
    `/api/v1/strategies/${strategyId}/executions`,
    {
      params: {
        page,
        page_size: pageSize,
      },
    }
  );

  return response.data;
}

/**
 * 更新策略设置
 * @param strategyId - 策略ID (Portfolio UUID)
 * @param settings - 策略设置对象
 * @param settings.rebalancePeriodMinutes - 策略执行周期（分钟）(可选)
 * @param settings.agentWeights - Agent权重配置 (可选)
 * @param settings.consecutiveSignalConfig - 连续信号配置 (可选)
 * @param settings.tradingThresholds - 交易阈值配置 (可选)
 */
export async function updateStrategySettings(
  strategyId: string,
  settings: {
    rebalancePeriodMinutes?: number;
    agentWeights?: {
      macro: number;
      onchain: number;
      ta: number;
    };
    consecutiveSignalConfig?: {
      consecutiveSignalThreshold: number;
      accelerationMultiplierMin: number;
      accelerationMultiplierMax: number;
    };
    tradingThresholds?: {
      fgCircuitBreakerThreshold: number;
      fgPositionAdjustThreshold: number;
      buyThreshold: number;
      partialSellThreshold: number;
      fullSellThreshold: number;
    };
  }
): Promise<any> {
  const body: any = {};

  // 只添加提供的参数
  if (settings.agentWeights !== undefined) {
    body.agent_weights = {
      macro: settings.agentWeights.macro / 100, // 转换为0-1范围
      onchain: settings.agentWeights.onchain / 100,
      ta: settings.agentWeights.ta / 100,
    };
  }

  const params: any = {};
  if (settings.rebalancePeriodMinutes !== undefined) {
    params.rebalance_period_minutes = settings.rebalancePeriodMinutes;
  }

  // 添加连续信号配置参数
  if (settings.consecutiveSignalConfig !== undefined) {
    params.consecutive_signal_threshold = settings.consecutiveSignalConfig.consecutiveSignalThreshold;
    params.acceleration_multiplier_min = settings.consecutiveSignalConfig.accelerationMultiplierMin;
    params.acceleration_multiplier_max = settings.consecutiveSignalConfig.accelerationMultiplierMax;
  }

  // 添加交易阈值配置参数
  if (settings.tradingThresholds !== undefined) {
    params.fg_circuit_breaker_threshold = settings.tradingThresholds.fgCircuitBreakerThreshold;
    params.fg_position_adjust_threshold = settings.tradingThresholds.fgPositionAdjustThreshold;
    params.buy_threshold = settings.tradingThresholds.buyThreshold;
    params.partial_sell_threshold = settings.tradingThresholds.partialSellThreshold;
    params.full_sell_threshold = settings.tradingThresholds.fullSellThreshold;
  }

  const response = await apiClient.patch(
    `/api/v1/strategies/${strategyId}/settings`,
    body,
    { params }
  );

  return response.data;
}

/**
 * 手动触发策略执行
 * @param strategyId - 策略 ID (Portfolio UUID)
 */
export async function executeStrategyNow(
  strategyId: string
): Promise<{
  id: string;
  portfolio_id: string;
  execution_time: string;
  signal: string;
  status: string;
  message?: string;
}> {
  const response = await apiClient.post(
    `/api/v1/strategy/manual-trigger`,
    null,
    {
      params: {
        portfolio_id: strategyId,
      },
    }
  );

  return response.data;
}
