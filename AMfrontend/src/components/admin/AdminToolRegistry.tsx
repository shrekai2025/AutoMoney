/**
 * Admin Tool Registry Component - Tool注册表管理
 */

import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { RefreshCw, CheckCircle, XCircle } from "lucide-react";
import { fetchAllTools, type ToolRegistry } from "../../lib/registryApi";

export function AdminToolRegistry() {
  const [tools, setTools] = useState<ToolRegistry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);

  useEffect(() => {
    loadTools();
  }, [activeOnly]);

  async function loadTools() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchAllTools(activeOnly);
      setTools(data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load tools';
      setError(errorMessage);
      console.error('Failed to load tools:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p>Loading tool registry...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="bg-slate-900/50 border border-red-500/50 rounded-xl max-w-md p-6 text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Button onClick={loadTools} variant="outline">
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
          <h2 className="text-2xl font-bold text-white">Tool Registry</h2>
          <p className="text-sm text-slate-400 mt-1">
            Registered tools available for agents
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
            onClick={loadTools}
            variant="outline"
            size="sm"
            className="bg-slate-800 border-slate-700 hover:bg-slate-700 text-white"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tool List */}
      <div className="bg-slate-900/50 rounded-xl border border-slate-800">
        {tools.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            No tools found
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {tools.map((tool) => (
              <div key={tool.id} className="p-6 hover:bg-slate-800/30 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">
                        {tool.display_name}
                      </h3>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${
                        tool.is_active
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}>
                        {tool.is_active ? (
                          <><CheckCircle className="w-3 h-3" /> Active</>
                        ) : (
                          <><XCircle className="w-3 h-3" /> Inactive</>
                        )}
                      </span>
                    </div>

                    <p className="text-sm text-slate-400 mb-3">
                      {tool.description || 'No description available'}
                    </p>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">Tool Name:</span>
                        <span className="ml-2 text-white font-mono">{tool.tool_name}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Module:</span>
                        <span className="ml-2 text-white font-mono text-xs">{tool.tool_module}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Function:</span>
                        <span className="ml-2 text-white font-mono">{tool.tool_function}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Required APIs:</span>
                        <span className="ml-2 text-white">
                          {tool.required_apis.length > 0 ? tool.required_apis.length : 'None'}
                        </span>
                      </div>
                    </div>

                    {tool.required_apis.length > 0 && (
                      <div className="mt-3">
                        <span className="text-xs text-slate-500">APIs: </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {tool.required_apis.map((api, idx) => (
                            <span
                              key={idx}
                              className="inline-block px-2 py-1 text-xs font-mono bg-slate-800 text-slate-300 rounded"
                            >
                              {api}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
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
