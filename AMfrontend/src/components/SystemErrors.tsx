import React, { useState, useEffect } from 'react';
import { AlertTriangle, XCircle, AlertCircle, Info, CheckCircle, X, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface SystemError {
  id: number;
  error_type: string;
  error_category: string;
  severity: 'critical' | 'error' | 'warning' | 'info';
  component: string;
  error_message: string;
  error_details?: string;
  context?: any;
  occurrence_count: number;
  first_occurred_at: string;
  last_occurred_at: string;
  is_resolved: boolean;
  strategy_name?: string;
  portfolio_id?: string;
}

interface ErrorSummary {
  total_errors: number;
  unresolved_errors: number;
  critical_count: number;
  error_count: number;
  warning_count: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
}

const SystemErrors: React.FC = () => {
  const [errors, setErrors] = useState<SystemError[]>([]);
  const [summary, setSummary] = useState<ErrorSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedError, setSelectedError] = useState<SystemError | null>(null);
  const [filter, setFilter] = useState<{
    severity?: string;
    unresolvedOnly: boolean;
  }>({ unresolvedOnly: true });

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchErrors();
    fetchSummary();
    const interval = setInterval(() => {
      fetchErrors();
      fetchSummary();
    }, 30000); // 每30秒刷新
    return () => clearInterval(interval);
  }, [filter]);

  const fetchErrors = async () => {
    try {
      const token = localStorage.getItem('idToken');
      const params = new URLSearchParams();
      if (filter.severity) params.append('severity', filter.severity);
      if (filter.unresolvedOnly) params.append('unresolved_only', 'true');
      params.append('limit', '50');

      const response = await axios.get(
        `${API_BASE}/api/v1/monitoring/errors/recent?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setErrors(response.data.errors);
    } catch (error) {
      console.error('Failed to fetch errors:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const token = localStorage.getItem('idToken');
      const response = await axios.get(
        `${API_BASE}/api/v1/monitoring/errors/summary`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch error summary:', error);
    }
  };

  const resolveError = async (errorId: number) => {
    try {
      const token = localStorage.getItem('idToken');
      await axios.post(
        `${API_BASE}/api/v1/monitoring/errors/${errorId}/resolve`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchErrors();
      fetchSummary();
      setSelectedError(null);
    } catch (error) {
      console.error('Failed to resolve error:', error);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-orange-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      critical: 'bg-red-500/20 text-red-300 border-red-500/50',
      error: 'bg-orange-500/20 text-orange-300 border-orange-500/50',
      warning: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
      info: 'bg-blue-500/20 text-blue-300 border-blue-500/50',
    };
    return (
      <span className={`px-2 py-1 rounded-md text-xs font-medium border ${colors[severity as keyof typeof colors]}`}>
        {severity.toUpperCase()}
      </span>
    );
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}小时前`;
    return date.toLocaleString('zh-CN');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gradient-to-br from-gray-900 via-purple-900/10 to-gray-900 min-h-screen">
      {/* Header with Summary */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">系统错误监控</h1>
        <button
          onClick={() => { fetchErrors(); fetchSummary(); }}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>

      {/* Error Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">未解决错误</p>
                <p className="text-2xl font-bold text-white mt-1">{summary.unresolved_errors}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-gray-500" />
            </div>
          </div>
          
          <div className="bg-red-500/10 backdrop-blur-sm border border-red-500/30 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-300 text-sm">严重错误</p>
                <p className="text-2xl font-bold text-red-400 mt-1">{summary.critical_count}</p>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </div>
          
          <div className="bg-orange-500/10 backdrop-blur-sm border border-orange-500/30 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-300 text-sm">错误</p>
                <p className="text-2xl font-bold text-orange-400 mt-1">{summary.error_count}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-orange-500" />
            </div>
          </div>
          
          <div className="bg-yellow-500/10 backdrop-blur-sm border border-yellow-500/30 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-300 text-sm">警告</p>
                <p className="text-2xl font-bold text-yellow-400 mt-1">{summary.warning_count}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-4">
        <span className="text-gray-400">筛选:</span>
        <select
          value={filter.severity || ''}
          onChange={(e) => setFilter({ ...filter, severity: e.target.value || undefined })}
          className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
        >
          <option value="">全部严重程度</option>
          <option value="critical">严重</option>
          <option value="error">错误</option>
          <option value="warning">警告</option>
          <option value="info">信息</option>
        </select>
        
        <label className="flex items-center gap-2 text-gray-300">
          <input
            type="checkbox"
            checked={filter.unresolvedOnly}
            onChange={(e) => setFilter({ ...filter, unresolvedOnly: e.target.checked })}
            className="w-4 h-4 rounded"
          />
          只显示未解决
        </label>
      </div>

      {/* Error List */}
      <div className="space-y-3">
        {errors.length === 0 ? (
          <div className="bg-green-500/10 backdrop-blur-sm border border-green-500/30 rounded-xl p-8 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <p className="text-green-300 text-lg">没有错误 - 系统运行正常! 🎉</p>
          </div>
        ) : (
          errors.map((error) => (
            <div
              key={error.id}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-4 hover:border-purple-500/50 transition-colors cursor-pointer"
              onClick={() => setSelectedError(error)}
            >
              <div className="flex items-start gap-4">
                {getSeverityIcon(error.severity)}
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    {getSeverityBadge(error.severity)}
                    <span className="text-gray-400 text-sm">{error.component}</span>
                    {error.occurrence_count > 1 && (
                      <span className="bg-purple-500/20 text-purple-300 px-2 py-1 rounded text-xs">
                        重复 {error.occurrence_count}次
                      </span>
                    )}
                  </div>
                  
                  <p className="text-white font-medium mb-1">{error.error_message}</p>
                  
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>类型: {error.error_type}</span>
                    <span>分类: {error.error_category}</span>
                    <span>{formatTime(error.last_occurred_at)}</span>
                    {error.strategy_name && <span>策略: {error.strategy_name}</span>}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Error Detail Modal */}
      {selectedError && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-auto">
            <div className="sticky top-0 bg-gray-900 border-b border-gray-700 p-6 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white">错误详情</h2>
              <button
                onClick={() => setSelectedError(null)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="flex items-center gap-3">
                {getSeverityIcon(selectedError.severity)}
                {getSeverityBadge(selectedError.severity)}
                {selectedError.occurrence_count > 1 && (
                  <span className="bg-purple-500/20 text-purple-300 px-3 py-1 rounded-lg">
                    重复 {selectedError.occurrence_count}次
                  </span>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">组件:</span>
                  <span className="text-white ml-2">{selectedError.component}</span>
                </div>
                <div>
                  <span className="text-gray-400">错误类型:</span>
                  <span className="text-white ml-2">{selectedError.error_type}</span>
                </div>
                <div>
                  <span className="text-gray-400">错误分类:</span>
                  <span className="text-white ml-2">{selectedError.error_category}</span>
                </div>
                <div>
                  <span className="text-gray-400">首次发生:</span>
                  <span className="text-white ml-2">{formatTime(selectedError.first_occurred_at)}</span>
                </div>
                <div>
                  <span className="text-gray-400">最近发生:</span>
                  <span className="text-white ml-2">{formatTime(selectedError.last_occurred_at)}</span>
                </div>
                {selectedError.strategy_name && (
                  <div>
                    <span className="text-gray-400">策略:</span>
                    <span className="text-white ml-2">{selectedError.strategy_name}</span>
                  </div>
                )}
              </div>
              
              <div>
                <p className="text-gray-400 mb-2">错误信息:</p>
                <pre className="bg-gray-800 rounded-lg p-4 text-red-300 text-sm overflow-auto">
                  {selectedError.error_message}
                </pre>
              </div>
              
              {selectedError.error_details && (
                <div>
                  <p className="text-gray-400 mb-2">详细堆栈:</p>
                  <pre className="bg-gray-800 rounded-lg p-4 text-gray-300 text-xs overflow-auto max-h-64">
                    {selectedError.error_details}
                  </pre>
                </div>
              )}
              
              {selectedError.context && Object.keys(selectedError.context).length > 0 && (
                <div>
                  <p className="text-gray-400 mb-2">上下文:</p>
                  <pre className="bg-gray-800 rounded-lg p-4 text-gray-300 text-xs overflow-auto">
                    {JSON.stringify(selectedError.context, null, 2)}
                  </pre>
                </div>
              )}
              
              {!selectedError.is_resolved && (
                <button
                  onClick={() => resolveError(selectedError.id)}
                  className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg transition-colors font-medium"
                >
                  标记为已解决
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemErrors;

