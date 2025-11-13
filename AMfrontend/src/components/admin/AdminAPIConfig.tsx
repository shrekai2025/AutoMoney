/**
 * Admin API Config Component - API配置管理
 */

import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { RefreshCw, CheckCircle, XCircle, Key } from "lucide-react";
import { fetchAllAPIs, type APIConfig } from "../../lib/registryApi";

export function AdminAPIConfig() {
  const [apis, setApis] = useState<APIConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);

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
