/**
 * Admin API Config Component - API配置管理
 */

import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { RefreshCw, CheckCircle, XCircle, Key, PlayCircle, AlertTriangle } from "lucide-react";
import { fetchAllAPIs, type APIConfig } from "../../lib/registryApi";

interface APITestResult {
  api_name: string;
  status: string;
  duration_seconds: number;
  data: any;
  error: {
    type: string;
    message: string;
  } | null;
}

interface APITestResponse {
  timestamp: string;
  summary: {
    total: number;
    success: number;
    failed: number;
    success_rate: string;
  };
  results: APITestResult[];
}

export function AdminAPIConfig() {
  const [apis, setApis] = useState<APIConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);
  const [testResults, setTestResults] = useState<APITestResponse | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    loadAPIs();
  }, [activeOnly]);

  async function loadAPIs() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchAllAPIs(activeOnly);
      setApis(data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load API configs';
      setError(errorMessage);
      console.error('Failed to load API configs:', err);
    } finally {
      setLoading(false);
    }
  }

  async function testAllAPIs() {
    try {
      setTesting(true);
      const response = await fetch('/api/v1/api-test/test-all-apis');
      const data = await response.json();
      setTestResults(data);
    } catch (err: any) {
      console.error('Failed to test APIs:', err);
      setTestResults({
        timestamp: new Date().toISOString(),
        summary: {
          total: 0,
          success: 0,
          failed: 0,
          success_rate: '0%',
        },
        results: [],
      });
    } finally {
      setTesting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p>Loading API configurations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="bg-slate-900/50 border border-red-500/50 rounded-xl max-w-md p-6 text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Button onClick={loadAPIs} variant="outline">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">API Configuration</h2>
          <p className="text-sm text-slate-400 mt-1">
            External API keys and configurations
          </p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-400">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              className="rounded border-slate-700 bg-slate-800"
            />
            Active only
          </label>
          <Button
            onClick={testAllAPIs}
            disabled={testing}
            variant="outline"
            size="sm"
            className="bg-blue-900/30 border-blue-700 hover:bg-blue-800/50 text-blue-300"
          >
            {testing ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <PlayCircle className="w-4 h-4 mr-2" />
                Test All APIs
              </>
            )}
          </Button>
          <Button
            onClick={loadAPIs}
            variant="outline"
            size="sm"
            className="bg-slate-800 border-slate-700 hover:bg-slate-700 text-white"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Test Results */}
      {testResults && (
        <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">API Test Results</h3>
              <p className="text-sm text-slate-400 mt-1">
                Tested at {new Date(testResults.timestamp).toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-6 bg-slate-800/50 px-6 py-3 rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">{testResults.summary.total}</div>
                <div className="text-xs text-slate-400">Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-400">{testResults.summary.success}</div>
                <div className="text-xs text-slate-400">Success</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">{testResults.summary.failed}</div>
                <div className="text-xs text-slate-400">Failed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{testResults.summary.success_rate}</div>
                <div className="text-xs text-slate-400">Success Rate</div>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {testResults.results.map((result, idx) => (
              <div
                key={idx}
                className={`border rounded-lg p-4 ${
                  result.status === 'success'
                    ? 'border-emerald-500/30 bg-emerald-500/5'
                    : 'border-red-500/30 bg-red-500/5'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {result.status === 'success' ? (
                      <CheckCircle className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400" />
                    )}
                    <div>
                      <h4 className="text-lg font-semibold text-white">{result.api_name}</h4>
                      <div className="flex items-center gap-4 mt-1">
                        <span className={`text-sm font-medium ${
                          result.status === 'success' ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          {result.status.toUpperCase()}
                        </span>
                        <span className="text-sm text-slate-400">
                          {result.duration_seconds}s
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {result.error && (
                  <div className="mt-3 p-3 bg-red-900/20 border border-red-500/30 rounded">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5" />
                      <div>
                        <div className="text-sm font-medium text-red-400">{result.error.type}</div>
                        <div className="text-sm text-red-300 mt-1">{result.error.message}</div>
                      </div>
                    </div>
                  </div>
                )}

                {result.data && (
                  <details className="mt-3">
                    <summary className="cursor-pointer text-sm text-blue-400 hover:text-blue-300">
                      View Response Data
                    </summary>
                    <pre className="mt-2 p-3 bg-slate-950 rounded text-xs text-slate-300 overflow-x-auto">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* API List */}
      <div className="bg-slate-900/50 rounded-xl border border-slate-800">
        {apis.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            No API configurations found
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {apis.map((api) => (
              <div key={api.id} className="p-6 hover:bg-slate-800/30 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">
                        {api.display_name}
                      </h3>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${
                        api.is_active
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}>
                        {api.is_active ? (
                          <><CheckCircle className="w-3 h-3" /> Active</>
                        ) : (
                          <><XCircle className="w-3 h-3" /> Inactive</>
                        )}
                      </span>
                    </div>

                    <p className="text-sm text-slate-400 mb-3">
                      {api.description || 'No description available'}
                    </p>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">API Name:</span>
                        <span className="ml-2 text-white font-mono">{api.api_name}</span>
                      </div>
                      {api.base_url && (
                        <div>
                          <span className="text-slate-500">Base URL:</span>
                          <span className="ml-2 text-white font-mono text-xs">{api.base_url}</span>
                        </div>
                      )}
                      {api.api_key_masked && (
                        <div className="flex items-center gap-2">
                          <Key className="w-4 h-4 text-slate-500" />
                          <span className="text-slate-500">API Key:</span>
                          <span className="ml-2 text-white font-mono">{api.api_key_masked}</span>
                        </div>
                      )}
                      {api.rate_limit && (
                        <div>
                          <span className="text-slate-500">Rate Limit:</span>
                          <span className="ml-2 text-white">{api.rate_limit} req/min</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
