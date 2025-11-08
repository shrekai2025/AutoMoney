/**
 * Strategy Type Definitions
 * 策略相关的 TypeScript 类型定义
 */

// ============ Marketplace List ============

export interface HistoryPoint {
  date: string;
  value: number;
}

export interface StrategyCard {
  id: string;                    // UUID (string format)
  name: string;
  subtitle: string;
  description: string;
  tags: string[];
  annualized_return: number;     // 使用 snake_case (匹配后端)
  max_drawdown: number;
  sharpe_ratio: number;
  pool_size: number;             // 不是 tvl
  total_pnl: number;             // 总盈亏
  squad_size: number;
  risk_level: string;
  history: HistoryPoint[];
}

export interface MarketplaceResponse {
  strategies: StrategyCard[];
}

// ============ Strategy Detail ============

export interface PerformanceMetrics {
  annualized_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  sortino_ratio: number | null;  // 后端返回 null
}

export interface ConvictionSummary {
  score: number;
  message: string;
  updated_at: string;
}

export interface SquadAgent {
  name: string;
  role: string;
  weight: string;
}

export interface PerformanceHistory {
  strategy: number[];
  btc_benchmark: number[];
  eth_benchmark: number[];
  dates: string[];
}

export interface AgentContribution {
  agent_name: string;
  display_name: string;
  signal: string;
  confidence: number;
  score: number;
}

export interface RecentActivity {
  date: string;
  signal: string;
  action: string;
  result: string;
  agent: string;
  execution_id?: string;
  conviction_score?: number | null;
  consecutive_count?: number | null;  // 连续信号计数
  agent_contributions?: AgentContribution[] | null;  // 各Agent的贡献详情
  status?: string;  // 执行状态: 'success', 'failed'
  error_details?: ErrorDetails | null;  // 错误详情
}

export interface StrategyParameters {
  assets: string;
  rebalance_period: string;
  risk_level: string;
  min_investment: string;
  lockup_period: string;
  management_fee: string;
  performance_fee: string;
}

export interface HoldingInfo {
  symbol: string;
  amount: number;
  avg_buy_price: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

export interface StrategyDetail {
  id: string;
  name: string;
  description: string;
  tags: string[];
  performance_metrics: PerformanceMetrics;
  conviction_summary: ConvictionSummary;
  squad_agents: SquadAgent[];
  performance_history: PerformanceHistory;
  recent_activities: RecentActivity[];
  parameters: StrategyParameters;
  philosophy: string;
  holdings: HoldingInfo[];
  total_unrealized_pnl: number;
  total_realized_pnl: number;
  total_pnl: number;
  total_pnl_percent: number;
  current_balance: number;
  initial_balance: number;
  total_fees: number;
}

// ============ Chart Data (前端使用) ============

export interface PerformanceDataPoint {
  date: string;
  strategy: number;
  btc: number;
  eth: number;
}

// ============ Strategy Execution Details ============

export interface AgentExecutionDetail {
  id: string;
  agent_name: string;
  agent_display_name: string | null;
  executed_at: string;
  execution_duration_ms: number | null;
  status: string;
  signal: string;
  confidence: number;
  score: number | null;
  reasoning: string;
  agent_specific_data: Record<string, any>;
  market_data_snapshot: Record<string, any> | null;
  llm_provider: string | null;
  llm_model: string | null;
  llm_prompt: string | null;
  llm_response: string | null;
  tokens_used: number | null;
  llm_cost: number | null;
}

export interface ErrorDetails {
  error_type: string;
  failed_agent?: string;
  error_message: string;
  retry_count?: number;
}

export interface TradeResponse {
  id: string;
  symbol: string;
  trade_type: 'BUY' | 'SELL';
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
  created_at: string;
}

export interface StrategyExecutionDetail {
  id: string;
  execution_time: string;
  strategy_name: string;
  status: string;
  market_snapshot: Record<string, any>;
  conviction_score: number | null;
  signal: string | null;
  signal_strength: number | null;
  position_size: number | null;
  risk_level: string | null;
  execution_duration_ms: number | null;
  error_message: string | null;
  error_details: ErrorDetails | null;
  agent_executions: AgentExecutionDetail[];
  trades: TradeResponse[];
}
