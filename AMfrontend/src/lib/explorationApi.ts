/**
 * Exploration API - Mind Hub页面数据获取
 */

import { getAuth } from 'firebase/auth';
import { initializeFirebase } from './firebase';

const API_BASE = '/api/v1/exploration';

// Firebase 初始化状态
let firebaseInitialized = false;
let firebaseInitPromise: Promise<void> | null = null;

/**
 * 确保 Firebase 已初始化
 */
async function ensureFirebaseInitialized(): Promise<void> {
  if (firebaseInitialized) {
    return;
  }

  if (firebaseInitPromise) {
    return firebaseInitPromise;
  }

  firebaseInitPromise = (async () => {
    try {
      await initializeFirebase();
      firebaseInitialized = true;
    } catch (error) {
      console.error('Firebase initialization failed:', error);
      firebaseInitPromise = null;
      throw error;
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
  try {
    // 确保 Firebase 已初始化
    await ensureFirebaseInitialized();

    const auth = getAuth();
    const user = auth.currentUser;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // 获取并添加 Firebase token
    if (user) {
      try {
        const token = await user.getIdToken(false);
        headers['Authorization'] = `Bearer ${token}`;
      } catch (tokenError) {
        console.error('Error getting Firebase token:', tokenError);
        // Token 获取失败，继续请求（后端会返回401）
      }
    }

  const response = await fetch(url, {
      method: 'GET',
      headers,
    credentials: 'include',
  });
  
  if (!response.ok) {
      // 如果是401，尝试刷新token并重试
      if (response.status === 401 && user) {
        try {
          const newToken = await user.getIdToken(true); // 强制刷新
          headers['Authorization'] = `Bearer ${newToken}`;
          
          const retryResponse = await fetch(url, {
            method: 'GET',
            headers,
            credentials: 'include',
          });
          
          if (!retryResponse.ok) {
            throw new Error(`API error: ${retryResponse.statusText}`);
          }
          
          return retryResponse.json();
        } catch (refreshError) {
          console.error('Failed to refresh token:', refreshError);
          throw new Error(`API error: ${response.statusText}`);
        }
      }
      
    throw new Error(`API error: ${response.statusText}`);
  }
  
  return response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
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

