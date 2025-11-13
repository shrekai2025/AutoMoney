/**
 * Admin Strategies Component - 策略列表管理
 */

import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { Settings, Power, PowerOff } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { fetchAllStrategies, toggleStrategy, updateStrategyParams, type AdminStrategy } from "../../lib/adminApi";
import { AgentWeightConfigurator, type AgentWeights } from "../AgentWeightConfigurator";
import { ConsecutiveSignalConfigurator, type ConsecutiveSignalConfig } from "../ConsecutiveSignalConfigurator";
import { TradingThresholdsConfigurator, type TradingThresholds } from "../TradingThresholdsConfigurator";

export function AdminStrategies() {
  const [strategies, setStrategies] = useState<AdminStrategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggleLoading, setToggleLoading] = useState<Record<string, boolean>>({});

  // Settings modal state
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<AdminStrategy | null>(null);
  const [agentWeights, setAgentWeights] = useState<AgentWeights>({ macro: 40, onchain: 40, ta: 20 });
  const [consecutiveSignalConfig, setConsecutiveSignalConfig] = useState<ConsecutiveSignalConfig>({
    consecutiveSignalThreshold: 30,
    accelerationMultiplierMin: 1.1,
    accelerationMultiplierMax: 2.0,
  });
  const [tradingThresholds, setTradingThresholds] = useState<TradingThresholds>({
    fgCircuitBreakerThreshold: 20,
    fgPositionAdjustThreshold: 30,
    buyThreshold: 50,
    fullSellThreshold: 45,
  });
  const [settingsSaving, setSettingsSaving] = useState(false);

  useEffect(() => {
    loadStrategies();
  }, []);

  async function loadStrategies() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchAllStrategies();
      setStrategies(data.strategies);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load strategies';
      setError(errorMessage);
      console.error('Failed to load strategies:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggle(strategyId: string, currentStatus: boolean) {
    try {
      setToggleLoading(prev => ({ ...prev, [strategyId]: true }));
      const newStatus = !currentStatus;

      await toggleStrategy(strategyId, newStatus);

      setStrategies(prev =>
        prev.map(s =>
          s.id === strategyId ? { ...s, is_active: newStatus } : s
        )
      );
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to toggle strategy';
      alert(`Error: ${errorMessage}`);
      console.error('Failed to toggle strategy:', err);
    } finally {
      setToggleLoading(prev => ({ ...prev, [strategyId]: false }));
    }
  }

  function handleOpenSettings(strategy: AdminStrategy) {
    setSelectedStrategy(strategy);

    if (strategy.agent_weights) {
      setAgentWeights({
        macro: (strategy.agent_weights.macro || 0.4) * 100,
        onchain: (strategy.agent_weights.onchain || 0.4) * 100,
        ta: (strategy.agent_weights.ta || 0.2) * 100,
      });
    } else {
      setAgentWeights({ macro: 40, onchain: 40, ta: 20 });
    }

    if ((strategy as any).consecutive_signal_threshold !== undefined) {
      setConsecutiveSignalConfig({
        consecutiveSignalThreshold: (strategy as any).consecutive_signal_threshold || 30,
        accelerationMultiplierMin: (strategy as any).acceleration_multiplier_min || 1.1,
        accelerationMultiplierMax: (strategy as any).acceleration_multiplier_max || 2.0,
      });
    } else {
      setConsecutiveSignalConfig({
        consecutiveSignalThreshold: 30,
        accelerationMultiplierMin: 1.1,
        accelerationMultiplierMax: 2.0,
      });
    }

    if ((strategy as any).fg_circuit_breaker_threshold !== undefined) {
      setTradingThresholds({
        fgCircuitBreakerThreshold: (strategy as any).fg_circuit_breaker_threshold || 20,
        fgPositionAdjustThreshold: (strategy as any).fg_position_adjust_threshold || 30,
        buyThreshold: (strategy as any).buy_threshold || 50,
        fullSellThreshold: (strategy as any).full_sell_threshold || 45,
      });
    } else {
      setTradingThresholds({
        fgCircuitBreakerThreshold: 20,
        fgPositionAdjustThreshold: 30,
        buyThreshold: 50,
        fullSellThreshold: 45,
      });
    }

    setSettingsOpen(true);
  }

  async function handleSaveSettings() {
    if (!selectedStrategy) return;

    if (Math.abs(agentWeights.macro + agentWeights.onchain + agentWeights.ta - 100) > 0.01) {
      alert('Agent weights must sum to 100%');
      return;
    }

    if (consecutiveSignalConfig.accelerationMultiplierMin > consecutiveSignalConfig.accelerationMultiplierMax) {
      alert('Acceleration multiplier min must be ≤ max');
      return;
    }

    if (tradingThresholds.buyThreshold < 0 || tradingThresholds.buyThreshold > 100 ||
        tradingThresholds.fullSellThreshold < 0 || tradingThresholds.fullSellThreshold > 100) {
      alert('Conviction score thresholds must be between 0 and 100');
      return;
    }

    if (tradingThresholds.fullSellThreshold > tradingThresholds.buyThreshold) {
      alert('Full Sell threshold must be ≤ Buy threshold');
      return;
    }

    try {
      setSettingsSaving(true);

      console.log('[NEW API] Saving strategy instance params:', {
        strategyId: selectedStrategy.id,
        agentWeights: agentWeights,
        consecutiveSignalConfig: consecutiveSignalConfig,
        tradingThresholds: tradingThresholds,
      });

      // 使用完整API（保存所有参数）
      const result = await updateStrategyParams(
        selectedStrategy.id,
        {
          // Agent权重（转换为0-1范围）
          agent_weights: {
            macro: agentWeights.macro / 100,
            onchain: agentWeights.onchain / 100,
            ta: agentWeights.ta / 100,
          },
          // 连续信号配置
          consecutive_signal_threshold: consecutiveSignalConfig.consecutiveSignalThreshold,
          acceleration_multiplier_min: consecutiveSignalConfig.accelerationMultiplierMin,
          acceleration_multiplier_max: consecutiveSignalConfig.accelerationMultiplierMax,
          // 交易阈值
          fg_circuit_breaker_threshold: tradingThresholds.fgCircuitBreakerThreshold,
          fg_position_adjust_threshold: tradingThresholds.fgPositionAdjustThreshold,
          buy_threshold: tradingThresholds.buyThreshold,
          full_sell_threshold: tradingThresholds.fullSellThreshold,
          // 注意: partial_sell_threshold 已移除，部分减仓区间现在是 [full_sell_threshold, buy_threshold)
        }
      );

      console.log('[NEW API] Save result:', result);

      // 关闭弹窗
      setSettingsOpen(false);

      // 重新加载策略列表以获取最新数据
      await loadStrategies();

      alert('Strategy settings updated successfully!');
    } catch (err: any) {
      let errorMessage = 'Failed to update settings';

      if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string'
          ? err.response.data.detail
          : JSON.stringify(err.response.data.detail);
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.message) {
        errorMessage = err.message;
      }

      alert(`Error: ${errorMessage}`);
      console.error('Failed to update settings:', err);
    } finally {
      setSettingsSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p>Loading strategies...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="bg-slate-900/50 border border-red-500/50 rounded-xl max-w-md p-6 text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Button onClick={loadStrategies} variant="outline">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Strategy List */}
      <div className="bg-slate-900/50 rounded-xl border border-slate-800">
        <div className="p-4 border-b border-slate-800">
          <h2 className="text-lg font-semibold text-white">All Strategies</h2>
        </div>

        {strategies.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            No strategies found
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">User</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Total Value</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">P&L</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {strategies.map((strategy) => (
                  <tr key={strategy.id} className="hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-sm text-slate-400 font-mono">
                      {strategy.id.substring(0, 8)}...
                    </td>
                    <td className="px-4 py-3 text-sm text-white">
                      {strategy.portfolio_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {strategy.user_email}
                    </td>
                    <td className="px-4 py-3 text-sm text-white text-right">
                      ${strategy.total_value.toLocaleString()}
                    </td>
                    <td className={`px-4 py-3 text-sm text-right ${
                      strategy.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {strategy.total_pnl >= 0 ? '+' : ''}${strategy.total_pnl.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        strategy.is_active
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}>
                        {strategy.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <Button
                          onClick={() => handleOpenSettings(strategy)}
                          variant="ghost"
                          size="sm"
                          className="text-slate-400 hover:text-white"
                        >
                          <Settings className="w-4 h-4" />
                        </Button>
                        <Button
                          onClick={() => handleToggle(strategy.id, strategy.is_active)}
                          variant="ghost"
                          size="sm"
                          disabled={toggleLoading[strategy.id]}
                          className={strategy.is_active ? 'text-red-400 hover:text-red-300' : 'text-emerald-400 hover:text-emerald-300'}
                        >
                          {toggleLoading[strategy.id] ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
                          ) : strategy.is_active ? (
                            <PowerOff className="w-4 h-4" />
                          ) : (
                            <Power className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Settings Modal */}
      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-800">
          <DialogHeader>
            <DialogTitle className="text-white">Strategy Settings</DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedStrategy?.portfolio_name} - Configure strategy parameters
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="basic" className="w-full">
            <div className="overflow-x-auto -mx-4 px-4">
              <TabsList className="inline-flex w-auto bg-slate-800 border border-slate-700">
                <TabsTrigger
                  value="basic"
                  className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
                >
                  Basic
                </TabsTrigger>
                <TabsTrigger
                  value="agents"
                  className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
                >
                  Agents
                </TabsTrigger>
                <TabsTrigger
                  value="signals"
                  className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
                >
                  Signals
                </TabsTrigger>
                <TabsTrigger
                  value="thresholds"
                  className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
                >
                  Thresholds
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="basic" className="space-y-4 pt-4">
              <div className="space-y-2">
                <p className="text-sm text-slate-400">
                  ℹ️ Rebalance Period is now configured at the Strategy Template level.
                  Please use the "Strategy Templates" tab to modify the execution period.
                </p>
                <div className="mt-4 p-4 bg-slate-800/50 border border-slate-700 rounded-md">
                  <Label className="text-white">Current Rebalance Period (Read-only)</Label>
                  <p className="text-lg text-slate-300 mt-2">
                    {selectedStrategy?.rebalance_period_minutes || 10} minutes
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    This value is inherited from the strategy template and applies to all instances.
                  </p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="agents" className="pt-4">
              <AgentWeightConfigurator
                initialWeights={agentWeights}
                onChange={setAgentWeights}
              />
            </TabsContent>

            <TabsContent value="signals" className="pt-4">
              <ConsecutiveSignalConfigurator
                initialConfig={consecutiveSignalConfig}
                onChange={setConsecutiveSignalConfig}
              />
            </TabsContent>

            <TabsContent value="thresholds" className="pt-4">
              <TradingThresholdsConfigurator
                initialThresholds={tradingThresholds}
                onChange={setTradingThresholds}
              />
            </TabsContent>
          </Tabs>

          <DialogFooter>
            <Button
              onClick={() => setSettingsOpen(false)}
              variant="outline"
              className="bg-slate-800 border-slate-700 text-white"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={settingsSaving}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              {settingsSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
