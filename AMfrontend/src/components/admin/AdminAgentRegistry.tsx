/**
 * Admin Agent Registry Component - Agent注册表管理
 */

import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { RefreshCw, CheckCircle, XCircle } from "lucide-react";
import { fetchAllAgents, type AgentRegistry } from "../../lib/registryApi";

export function AdminAgentRegistry() {
  const [agents, setAgents] = useState<AgentRegistry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);

  useEffect(() => {
    loadAgents();
  }, [activeOnly]);

  async function loadAgents() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchAllAgents(activeOnly);
      setAgents(data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load agents';
      setError(errorMessage);
      console.error('Failed to load agents:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p>Loading agent registry...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="bg-slate-900/50 border border-red-500/50 rounded-xl max-w-md p-6 text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Button onClick={loadAgents} variant="outline">
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
          <h2 className="text-2xl font-bold text-white">Agent Registry</h2>
          <p className="text-sm text-slate-400 mt-1">
            Registered business agents available for strategies
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
            onClick={loadAgents}
            variant="outline"
            size="sm"
            className="bg-slate-800 border-slate-700 hover:bg-slate-700 text-white"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Agent List */}
      <div className="bg-slate-900/50 rounded-xl border border-slate-800">
        {agents.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            No agents found
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {agents.map((agent) => (
              <div key={agent.id} className="p-6 hover:bg-slate-800/30 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">
                        {agent.display_name}
                      </h3>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${
                        agent.is_active
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}>
                        {agent.is_active ? (
                          <><CheckCircle className="w-3 h-3" /> Active</>
                        ) : (
                          <><XCircle className="w-3 h-3" /> Inactive</>
                        )}
                      </span>
                    </div>

                    <p className="text-sm text-slate-400 mb-3">
                      {agent.description || 'No description available'}
                    </p>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">Agent Name:</span>
                        <span className="ml-2 text-white font-mono">{agent.agent_name}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Module:</span>
                        <span className="ml-2 text-white font-mono text-xs">{agent.agent_module}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Class:</span>
                        <span className="ml-2 text-white font-mono">{agent.agent_class}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Available Tools:</span>
                        <span className="ml-2 text-white">
                          {agent.available_tools.length > 0 ? agent.available_tools.length : 'None'}
                        </span>
                      </div>
                    </div>

                    {agent.available_tools.length > 0 && (
                      <div className="mt-3">
                        <span className="text-xs text-slate-500">Tools: </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {agent.available_tools.map((tool, idx) => (
                            <span
                              key={idx}
                              className="inline-block px-2 py-1 text-xs font-mono bg-slate-800 text-slate-300 rounded"
                            >
                              {tool}
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
