/**
 * Exploration API - Mind Hub页面数据获取
 */

import { getAuthInstance, initializeFirebase } from './firebase';

const API_BASE = '/api/v1/exploration';

// Firebase 初始化状态
let firebaseInitialized = false;
let firebaseInitPromise: Promise<boolean> | null = null;

/**
 * 尝试初始化 Firebase（不抛出错误）
 * 如果初始化失败，返回false但不阻塞
 */
async function tryInitializeFirebase(): Promise<boolean> {
  if (firebaseInitialized) {
    return true;
  }

  if (firebaseInitPromise) {
    try {
      await firebaseInitPromise;
      return true;
    } catch {
      return false;
    }
  }

  firebaseInitPromise = (async () => {
    try {
      await initializeFirebase();
      firebaseInitialized = true;
      return true;
    } catch (error) {
      console.warn('[ExplorationAPI] Firebase initialization failed (non-blocking):', error);
      firebaseInitPromise = null;
      return false;
    }
  })();

  return firebaseInitPromise;
}

export interface SquadAgent {
  agent_name: string;
  display_name: string;
  weight: string;
  color: string;
  score: number;
  confidence: number;
  signal: string | null;
  reasoning: string;
  core_inputs: Array<{
    label: string;
    value: string;
    progress: number;
  }>;
  executed_at: string | null;
}

export interface SquadDecisionCore {
  squad: SquadAgent[];
  last_updated: string | null;
}

export interface CommanderAnalysis {
  commander_name: string;
  status: string;
  conviction_score: number;
  conviction_level: string;
  market_analysis: string;
  signal: string | null;
  signal_strength: number;
  risk_level: string | null;
  last_updated: string | null;
}

export interface ActiveDirective {
  strategy_name: string | null;
  strategy_subtitle: string | null;
  countdown: {
    remaining_seconds: number;
    formatted: string;
    progress: number;
  };
  status: string;
  action: {
    type: string;
    amount: string;
    asset: string;
  };
  description: string;
  execution_time: string | null;
}

export interface DirectiveHistory {
  directives: Array<{
    id: string;
    timestamp: string;
    execution_time: string | null;
    strategy: string;
    strategy_subtitle: string;
    status: string;
    action: {
      type: string;
      amount: string;
      asset: string;
      sentiment: string;
    };
    conviction: number;
    result: number;
  }>;
  total: number;
  last_updated: string;
}

export interface DataStreamItem {
  type: string;
  text: string;
  trend: 'up' | 'down' | 'neutral';
}

export interface DataStream {
  stream: DataStreamItem[];
  last_updated: string;
}

export interface AvailableStrategy {
  id: number;
  name: string;
  display_name: string;
  description: string;
  is_active: boolean;
  is_locked: boolean;
}

export interface AvailableStrategies {
  strategies: AvailableStrategy[];
  total: number;
}

async function fetchWithAuth<T>(url: string): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // 尝试获取Firebase token（如果用户已登录）
  // 如果Firebase未初始化或用户未登录，继续请求（不阻塞）
  const firebaseInitialized = await tryInitializeFirebase();
  
  if (firebaseInitialized) {
    try {
      const auth = await getAuthInstance();
      const user = auth.currentUser;
      
      if (user) {
        try {
          const token = await user.getIdToken(false);
          headers['Authorization'] = `Bearer ${token}`;
        } catch (tokenError) {
          // Token 获取失败，继续请求（未登录用户也可以访问）
          console.warn('[ExplorationAPI] Could not get Firebase token, proceeding without auth');
        }
      }
    } catch (authError) {
      // 获取auth实例失败，继续请求
      console.warn('[ExplorationAPI] Could not get auth instance, proceeding without auth');
    }
  }

  // 无论Firebase是否初始化成功，都继续请求
  const response = await fetch(url, {
    method: 'GET',
    headers,
    credentials: 'include',
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    console.error(`[ExplorationAPI] API error: ${response.status} ${errorText}`);
    throw new Error(`API error: ${response.status} ${errorText}`);
  }

  return response.json();
}

export const explorationApi = {
  /**
   * 获取Squad Decision Core数据（三个Agent的最新执行结果）
   */
  async getSquadDecisionCore(): Promise<SquadDecisionCore> {
    return fetchWithAuth<SquadDecisionCore>(`${API_BASE}/squad-decision-core`);
  },

  /**
   * 获取AI Commander的综合分析
   */
  async getCommanderAnalysis(strategyId?: number): Promise<CommanderAnalysis> {
    const url = strategyId 
      ? `${API_BASE}/commander-analysis?strategy_id=${strategyId}`
      : `${API_BASE}/commander-analysis`;
    return fetchWithAuth<CommanderAnalysis>(url);
  },

  /**
   * 获取当前活跃的指令
   */
  async getActiveDirective(strategyId?: number): Promise<ActiveDirective> {
    const url = strategyId
      ? `${API_BASE}/active-directive?strategy_id=${strategyId}`
      : `${API_BASE}/active-directive`;
    return fetchWithAuth<ActiveDirective>(url);
  },

  /**
   * 获取指令历史
   */
  async getDirectiveHistory(strategyId?: number, limit: number = 100): Promise<DirectiveHistory> {
    const params = new URLSearchParams();
    if (strategyId) params.append('strategy_id', strategyId.toString());
    params.append('limit', limit.toString());
    return fetchWithAuth<DirectiveHistory>(`${API_BASE}/directive-history?${params.toString()}`);
  },

  /**
   * 获取数据流
   */
  async getDataStream(): Promise<DataStream> {
    return fetchWithAuth<DataStream>(`${API_BASE}/data-stream`);
  },

  /**
   * 获取可用策略列表
   */
  async getAvailableStrategies(): Promise<AvailableStrategies> {
    return fetchWithAuth<AvailableStrategies>(`${API_BASE}/available-strategies`);
  },
};

