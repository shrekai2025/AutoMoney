import React, { useState, useEffect } from 'react';
import { AlertTriangle, XCircle, AlertCircle, Info, RefreshCw, Search, X, CheckCircle, Bug } from 'lucide-react';
import apiClient from '../lib/api';

interface LogEntry {
  timestamp: string;
  level: string;
  component?: string;
  message: string;
  raw_line: string;
}

interface LogCategory {
  category: string;
  count: number;
  entries: LogEntry[];
}

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

interface DebugLogsData {
  log_file_path: string;
  total_lines: number;
  categories: LogCategory[];
  system_errors: SystemError[];
}

const DebugLogs: React.FC = () => {
  const [data, setData] = useState<DebugLogsData | null>(null);
  const [summary, setSummary] = useState<ErrorSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('system_errors');
  const [searchTerm, setSearchTerm] = useState('');
  const [lines, setLines] = useState(1000);
  const [selectedError, setSelectedError] = useState<SystemError | null>(null);
  const [filter, setFilter] = useState<{
    severity?: string;
    error_type?: string;
    unresolvedOnly: boolean;
  }>({ unresolvedOnly: true });
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const loadData = async () => {
      await fetchLogs();
      await fetchSummary();
      await fetchSystemErrors();
    };
    loadData();
    const interval = setInterval(() => {
      loadData();
    }, 30000); // 每30秒刷新
    return () => clearInterval(interval);
  }, [lines, filter]);

  const fetchLogs = async () => {
    try {
      const response = await apiClient.get(
        `/api/v1/admin/debug/logs?lines=${lines}`,
        { validateStatus: () => true } // 不抛出错误
      );
      
      if (response.status === 401) {
        setErrorMessage('权限不足，需要Admin权限');
        setLoading(false);
        return;
      }
      
      if (response.status === 200) {
        setData(response.data);
        setErrorMessage('');
      } else {
        setErrorMessage(`加载失败: ${response.status} ${response.statusText}`);
      }
    } catch (error: any) {
      console.error('Failed to fetch debug logs:', error);
      setErrorMessage(`加载失败: ${error.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await apiClient.get(
        `/api/v1/monitoring/errors/summary`,
        { validateStatus: () => true }
      );
      
      if (response.status === 200) {
        setSummary(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch error summary:', error);
    }
  };

  const fetchSystemErrors = async () => {
    try {
      const params = new URLSearchParams();
      if (filter.severity) params.append('severity', filter.severity);
      if (filter.error_type) params.append('error_type', filter.error_type);
      if (filter.unresolvedOnly) params.append('unresolved_only', 'true');
      params.append('limit', '200');

      const response = await apiClient.get(
        `/api/v1/monitoring/errors/recent?${params}`,
        { validateStatus: () => true }
      );
      
      if (response.status === 200) {
        const errors = response.data.errors.map((e: any) => ({
          ...e,
          severity: e.severity as 'critical' | 'error' | 'warning' | 'info',
        }));
        
        setData(prev => {
          if (!prev) {
            return {
              log_file_path: '',
              total_lines: 0,
              categories: [],
              system_errors: errors,
            };
          }
          return {
            ...prev,
            system_errors: errors,
          };
        });
      }
    } catch (error) {
      console.error('Failed to fetch system errors:', error);
    }
  };

  const resolveError = async (errorId: number) => {
    try {
      await apiClient.post(
        `/api/v1/monitoring/errors/${errorId}/resolve`,
        {}
      );
      fetchSystemErrors();
      fetchSummary();
      setSelectedError(null);
    } catch (error) {
      console.error('Failed to resolve error:', error);
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'ERROR':
      case 'CRITICAL':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'WARNING':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Info className="w-4 h-4 text-blue-500" />;
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
      <span className={`px-2 py-1 rounded-md text-xs font-medium border ${colors[severity as keyof typeof colors] || colors.info}`}>
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

  const filterEntries = (entries: LogEntry[]) => {
    if (!searchTerm) return entries;
    return entries.filter(e => 
      e.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.component?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.level.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/50 mx-auto mb-4 animate-pulse">
            <Bug className="w-8 h-8 text-white" />
          </div>
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-t-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-white text-lg font-medium">加载调试日志中...</p>
        </div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="p-6 space-y-6 min-h-screen flex items-center justify-center">
        <div className="bg-red-500/10 backdrop-blur-sm border border-red-500/30 rounded-2xl p-12 text-center max-w-md">
          <XCircle className="w-20 h-20 text-red-500 mx-auto mb-6" />
          <h3 className="text-2xl font-bold text-white mb-3">加载失败</h3>
          <p className="text-red-300 text-lg mb-6">{errorMessage}</p>
          <button
            onClick={() => { setErrorMessage(''); fetchLogs(); }}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 rounded-lg transition-all text-white font-semibold shadow-lg shadow-purple-500/30"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 space-y-6 min-h-screen flex items-center justify-center">
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-12 text-center max-w-md">
          <AlertCircle className="w-20 h-20 text-slate-500 mx-auto mb-6" />
          <h3 className="text-2xl font-bold text-white mb-3">无法加载数据</h3>
          <p className="text-slate-400 mb-6">日志数据加载失败，请重试</p>
          <button
            onClick={() => { fetchLogs(); fetchSummary(); fetchSystemErrors(); }}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 rounded-lg transition-all text-white font-semibold shadow-lg shadow-purple-500/30"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  const selectedCategoryData = data.categories.find(c => c.category === selectedCategory);
  const systemErrors = data.system_errors || [];

  return (
    <div className="p-6 space-y-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
            <Bug className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">Debug日志监控</h1>
            <p className="text-slate-400 text-sm mt-1">
              日志文件: <span className="text-slate-300">{data.log_file_path}</span> | 总行数: <span className="text-slate-300">{data.total_lines.toLocaleString()}</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <input
            type="number"
            value={lines}
            onChange={(e) => setLines(parseInt(e.target.value) || 1000)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white w-32 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="行数"
            min={100}
            max={10000}
          />
          <button
            onClick={() => { fetchLogs(); fetchSummary(); fetchSystemErrors(); }}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors text-white shadow-lg shadow-purple-500/30"
          >
            <RefreshCw className="w-4 h-4" />
            <span>刷新</span>
          </button>
        </div>
      </div>

      {/* Error Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4 hover:border-slate-600 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm font-medium">未解决错误</p>
                <p className="text-3xl font-bold text-white mt-2">{summary.unresolved_errors}</p>
              </div>
              <div className="w-12 h-12 bg-slate-700/50 rounded-lg flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-slate-400" />
              </div>
            </div>
          </div>

          <div className="bg-red-500/10 backdrop-blur-sm border border-red-500/30 rounded-xl p-4 hover:border-red-500/50 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-300 text-sm font-medium">严重错误</p>
                <p className="text-3xl font-bold text-red-400 mt-2">{summary.critical_count}</p>
              </div>
              <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                <XCircle className="w-6 h-6 text-red-500" />
              </div>
            </div>
          </div>

          <div className="bg-orange-500/10 backdrop-blur-sm border border-orange-500/30 rounded-xl p-4 hover:border-orange-500/50 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-300 text-sm font-medium">错误</p>
                <p className="text-3xl font-bold text-orange-400 mt-2">{summary.error_count}</p>
              </div>
              <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-orange-500" />
              </div>
            </div>
          </div>

          <div className="bg-yellow-500/10 backdrop-blur-sm border border-yellow-500/30 rounded-xl p-4 hover:border-yellow-500/50 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-300 text-sm font-medium">警告</p>
                <p className="text-3xl font-bold text-yellow-400 mt-2">{summary.warning_count}</p>
              </div>
              <div className="w-12 h-12 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-yellow-500" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Category Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedCategory('system_errors')}
          className={`px-4 py-2.5 rounded-lg font-medium transition-all whitespace-nowrap ${
            selectedCategory === 'system_errors'
              ? 'bg-gradient-to-r from-purple-600 to-purple-500 text-white shadow-lg shadow-purple-500/30'
              : 'bg-slate-800/50 text-slate-300 hover:bg-slate-700/50 border border-slate-700/50'
          }`}
        >
          <span className="flex items-center gap-2">
            🗄️ System Errors
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
              selectedCategory === 'system_errors'
                ? 'bg-white/20 text-white'
                : 'bg-slate-700/70 text-slate-300'
            }`}>
              {systemErrors.length}
            </span>
          </span>
        </button>
        {data.categories.map((category) => (
          <button
            key={category.category}
            onClick={() => setSelectedCategory(category.category)}
            className={`px-4 py-2.5 rounded-lg font-medium transition-all whitespace-nowrap ${
              selectedCategory === category.category
                ? 'bg-gradient-to-r from-purple-600 to-purple-500 text-white shadow-lg shadow-purple-500/30'
                : 'bg-slate-800/50 text-slate-300 hover:bg-slate-700/50 border border-slate-700/50'
            }`}
          >
            <span className="flex items-center gap-2">
              {category.category === 'errors' && '❌'}
              {category.category === 'warnings' && '⚠️'}
              {category.category === 'info' && 'ℹ️'}
              {category.category.charAt(0).toUpperCase() + category.category.slice(1)}
              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                selectedCategory === category.category
                  ? 'bg-white/20 text-white'
                  : 'bg-slate-700/70 text-slate-300'
              }`}>
                {category.count}
              </span>
            </span>
          </button>
        ))}
      </div>

      {/* Filters - Only show for System Errors */}
      {selectedCategory === 'system_errors' && (
        <div className="flex items-center gap-4 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4">
          <span className="text-slate-300 font-medium">筛选:</span>
          <select
            value={filter.severity || ''}
            onChange={(e) => setFilter({ ...filter, severity: e.target.value || undefined })}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 [&>option]:bg-gray-800 [&>option]:text-white"
          >
            <option value="">全部严重程度</option>
            <option value="critical">严重</option>
            <option value="error">错误</option>
            <option value="warning">警告</option>
            <option value="info">信息</option>
          </select>

          <select
            value={filter.error_type || ''}
            onChange={(e) => setFilter({ ...filter, error_type: e.target.value || undefined })}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 [&>option]:bg-gray-800 [&>option]:text-white"
          >
            <option value="">全部错误类型</option>
            <option value="data_collection">数据采集</option>
            <option value="agent_execution">Agent执行</option>
            <option value="strategy_execution">策略执行</option>
            <option value="trading">交易</option>
            <option value="system">系统</option>
          </select>
          
          <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
            <input
              type="checkbox"
              checked={filter.unresolvedOnly}
              onChange={(e) => setFilter({ ...filter, unresolvedOnly: e.target.checked })}
              className="w-4 h-4 rounded accent-purple-600"
            />
            <span className="text-gray-300">只显示未解决</span>
          </label>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="搜索日志..."
          className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg pl-10 pr-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
        />
      </div>

      {/* Content */}
      {selectedCategory === 'system_errors' ? (
        <div className="space-y-3">
          {systemErrors.length === 0 ? (
            <div className="bg-green-500/10 backdrop-blur-sm border border-green-500/30 rounded-xl p-8 text-center">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <p className="text-green-300 text-lg">没有错误 - 系统运行正常! 🎉</p>
            </div>
          ) : (
            systemErrors.map((error) => (
              <div
                key={error.id}
                className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-5 hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/10 transition-all cursor-pointer"
                onClick={() => setSelectedError(error)}
              >
                <div className="flex items-start gap-4">
                  {getSeverityIcon(error.severity)}

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-3">
                      {getSeverityBadge(error.severity)}
                      <span className="text-slate-400 text-sm font-medium">{error.component}</span>
                      {error.occurrence_count > 1 && (
                        <span className="bg-purple-500/20 text-purple-300 px-2.5 py-1 rounded-md text-xs font-semibold border border-purple-500/30">
                          重复 {error.occurrence_count}次
                        </span>
                      )}
                    </div>

                    <p className="text-white font-semibold mb-2 text-base">{error.error_message}</p>

                    <div className="flex items-center gap-4 text-sm text-slate-400">
                      <span>类型: <span className="text-slate-300">{error.error_type}</span></span>
                      <span>分类: <span className="text-slate-300">{error.error_category}</span></span>
                      <span className="text-slate-500">{formatTime(error.last_occurred_at)}</span>
                      {error.strategy_name && <span>策略: <span className="text-slate-300">{error.strategy_name}</span></span>}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ) : selectedCategoryData ? (
        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
          {filterEntries(selectedCategoryData.entries).length === 0 ? (
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-8 text-center">
              <p className="text-slate-400 text-base">
                {searchTerm ? '没有匹配的日志' : '没有日志记录'}
              </p>
            </div>
          ) : (
            filterEntries(selectedCategoryData.entries).map((entry, index) => (
              <div
                key={index}
                className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-lg p-4 hover:border-purple-500/50 hover:shadow-md hover:shadow-purple-500/10 transition-all"
              >
                <div className="flex items-start gap-3">
                  {getLevelIcon(entry.level)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-slate-500 text-xs font-mono">{entry.timestamp}</span>
                      {entry.component && (
                        <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-md text-xs font-medium border border-blue-500/30">
                          {entry.component}
                        </span>
                      )}
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-md ${
                        entry.level === 'ERROR' || entry.level === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                        entry.level === 'WARNING' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' :
                        'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      }`}>
                        {entry.level}
                      </span>
                    </div>
                    <p className="text-white text-sm font-mono break-words leading-relaxed">{entry.message}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ) : null}

      {/* Error Detail Modal */}
      {selectedError && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50" onClick={() => setSelectedError(null)}>
          <div className="bg-slate-900 border border-slate-700/50 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="sticky top-0 bg-gradient-to-r from-slate-900 via-purple-900/20 to-slate-900 border-b border-slate-700/50 p-6 flex items-center justify-between backdrop-blur-xl">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">错误详情</h2>
              <button
                onClick={() => setSelectedError(null)}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors group"
              >
                <X className="w-6 h-6 text-slate-400 group-hover:text-white transition-colors" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="flex items-center gap-3">
                {getSeverityIcon(selectedError.severity)}
                {getSeverityBadge(selectedError.severity)}
                {selectedError.occurrence_count > 1 && (
                  <span className="bg-purple-500/20 text-purple-300 px-3 py-1.5 rounded-lg font-semibold border border-purple-500/30">
                    重复 {selectedError.occurrence_count}次
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
                <div>
                  <span className="text-slate-400 text-sm">组件:</span>
                  <span className="text-white ml-2 font-medium">{selectedError.component}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-sm">错误类型:</span>
                  <span className="text-white ml-2 font-medium">{selectedError.error_type}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-sm">错误分类:</span>
                  <span className="text-white ml-2 font-medium">{selectedError.error_category}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-sm">首次发生:</span>
                  <span className="text-white ml-2 font-medium">{formatTime(selectedError.first_occurred_at)}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-sm">最近发生:</span>
                  <span className="text-white ml-2 font-medium">{formatTime(selectedError.last_occurred_at)}</span>
                </div>
                {selectedError.strategy_name && (
                  <div>
                    <span className="text-slate-400 text-sm">策略:</span>
                    <span className="text-white ml-2 font-medium">{selectedError.strategy_name}</span>
                  </div>
                )}
              </div>

              <div>
                <p className="text-slate-300 font-semibold mb-3">错误信息:</p>
                <pre className="bg-slate-800/50 border border-red-500/30 rounded-lg p-4 text-red-300 text-sm overflow-auto font-mono">
                  {selectedError.error_message}
                </pre>
              </div>

              {selectedError.error_details && (
                <div>
                  <p className="text-slate-300 font-semibold mb-3">详细堆栈:</p>
                  <pre className="bg-slate-800/50 border border-slate-700/30 rounded-lg p-4 text-slate-300 text-xs overflow-auto max-h-64 font-mono">
                    {selectedError.error_details}
                  </pre>
                </div>
              )}

              {selectedError.context && Object.keys(selectedError.context).length > 0 && (
                <div>
                  <p className="text-slate-300 font-semibold mb-3">上下文:</p>
                  <pre className="bg-slate-800/50 border border-slate-700/30 rounded-lg p-4 text-slate-300 text-xs overflow-auto font-mono">
                    {JSON.stringify(selectedError.context, null, 2)}
                  </pre>
                </div>
              )}

              {!selectedError.is_resolved && (
                <button
                  onClick={() => resolveError(selectedError.id)}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white py-3 rounded-lg transition-all font-semibold shadow-lg shadow-green-500/30"
                >
                  ✓ 标记为已解决
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugLogs;

