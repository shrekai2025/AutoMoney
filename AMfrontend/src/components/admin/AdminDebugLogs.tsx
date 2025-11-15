import React, { useState, useEffect } from 'react';
import { AlertTriangle, XCircle, AlertCircle, Info, RefreshCw, Search, X, CheckCircle } from 'lucide-react';
import axios from 'axios';

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

const AdminDebugLogs: React.FC = () => {
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

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
      const token = localStorage.getItem('idToken');
      const response = await axios.get(
        `${API_BASE}/api/v1/admin/debug/logs?lines=${lines}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setData(response.data);
    } catch (error) {
      console.error('Failed to fetch debug logs:', error);
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

  const fetchSystemErrors = async () => {
    try {
      const token = localStorage.getItem('idToken');
      const params = new URLSearchParams();
      if (filter.severity) params.append('severity', filter.severity);
      if (filter.error_type) params.append('error_type', filter.error_type);
      if (filter.unresolvedOnly) params.append('unresolved_only', 'true');
      params.append('limit', '200');

      const response = await axios.get(
        `${API_BASE}/api/v1/monitoring/errors/recent?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // 更新data中的system_errors
      const errors = response.data.errors.map((e: any) => ({
        ...e,
        severity: e.severity as 'critical' | 'error' | 'warning' | 'info',
      }));
      
      setData(prev => {
        if (!prev) {
          // 如果data还没初始化，先初始化一个基本结构
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
    } catch (error) {
      console.error('Failed to fetch system errors:', error);
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
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-8 text-center">
        <p className="text-gray-400">无法加载日志数据</p>
      </div>
    );
  }

  const selectedCategoryData = data.categories.find(c => c.category === selectedCategory);
  const systemErrors = data.system_errors || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Debug日志监控</h2>
          <p className="text-gray-400 text-sm mt-1">
            日志文件: {data.log_file_path} | 总行数: {data.total_lines}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <input
            type="number"
            value={lines}
            onChange={(e) => setLines(parseInt(e.target.value) || 1000)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white w-32"
            placeholder="行数"
            min={100}
            max={10000}
          />
          <button
            onClick={() => { fetchLogs(); fetchSummary(); fetchSystemErrors(); }}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
        </div>
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

      {/* Category Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto">
        <button
          onClick={() => setSelectedCategory('system_errors')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
            selectedCategory === 'system_errors'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          🗄️ System Errors
          <span className="ml-2 bg-gray-700/50 px-2 py-0.5 rounded text-xs">
            {systemErrors.length}
          </span>
        </button>
        {data.categories.map((category) => (
          <button
            key={category.category}
            onClick={() => setSelectedCategory(category.category)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
              selectedCategory === category.category
                ? 'bg-purple-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {category.category === 'errors' && '❌'}
            {category.category === 'warnings' && '⚠️'}
            {category.category === 'info' && 'ℹ️'}
            {' '}
            {category.category.charAt(0).toUpperCase() + category.category.slice(1)}
            <span className="ml-2 bg-gray-700/50 px-2 py-0.5 rounded text-xs">
              {category.count}
            </span>
          </button>
        ))}
      </div>

      {/* Filters - Only show for System Errors */}
      {selectedCategory === 'system_errors' && (
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
          
          <select
            value={filter.error_type || ''}
            onChange={(e) => setFilter({ ...filter, error_type: e.target.value || undefined })}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          >
            <option value="">全部错误类型</option>
            <option value="data_collection">数据采集</option>
            <option value="agent_execution">Agent执行</option>
            <option value="strategy_execution">策略执行</option>
            <option value="trading">交易</option>
            <option value="system">系统</option>
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
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="搜索日志..."
          className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-500"
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
      ) : selectedCategoryData ? (
        <div className="space-y-2 max-h-[600px] overflow-y-auto">
          {filterEntries(selectedCategoryData.entries).length === 0 ? (
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-8 text-center">
              <p className="text-gray-400">
                {searchTerm ? '没有匹配的日志' : '没有日志记录'}
              </p>
            </div>
          ) : (
            filterEntries(selectedCategoryData.entries).map((entry, index) => (
              <div
                key={index}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-3 hover:border-purple-500/50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  {getLevelIcon(entry.level)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-gray-400 text-xs font-mono">{entry.timestamp}</span>
                      {entry.component && (
                        <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded text-xs">
                          {entry.component}
                        </span>
                      )}
                      <span className={`text-xs font-medium ${
                        entry.level === 'ERROR' || entry.level === 'CRITICAL' ? 'text-red-400' :
                        entry.level === 'WARNING' ? 'text-yellow-400' : 'text-blue-400'
                      }`}>
                        {entry.level}
                      </span>
                    </div>
                    <p className="text-white text-sm font-mono break-words">{entry.message}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ) : null}

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

export default AdminDebugLogs;
