import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Shield, Users, TrendingUp, TrendingDown, AlertCircle, Lock, Settings } from "lucide-react";
import styles from './AdminPanel.module.css';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { fetchAllStrategies, toggleStrategy } from "../lib/adminApi";
import { updateStrategySettings } from "../lib/marketplaceApi";
import { AgentWeightConfigurator, type AgentWeights } from "./AgentWeightConfigurator";
import { ConsecutiveSignalConfigurator, type ConsecutiveSignalConfig } from "./ConsecutiveSignalConfigurator";
import { TradingThresholdsConfigurator, type TradingThresholds } from "./TradingThresholdsConfigurator";
import type { AdminStrategy } from "../lib/adminApi";

export function AdminPanel() {
  const [strategies, setStrategies] = useState<AdminStrategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggleLoading, setToggleLoading] = useState<Record<string, boolean>>({});

  // Settings modal state
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<AdminStrategy | null>(null);
  const [rebalancePeriod, setRebalancePeriod] = useState<string>("");
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
    partialSellThreshold: 50,
    fullSellThreshold: 45,
  });
  const [settingsSaving, setSettingsSaving] = useState(false);

  // Load all strategies
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

      // Update local state
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
    // Get current rebalance_period_minutes from strategy, default to 10 if not set
    const currentPeriod = strategy.rebalance_period_minutes || 10;
    setRebalancePeriod(currentPeriod.toString());

    // Parse agent_weights from strategy (if exists), convert from 0-1 to 0-100 percentage
    if (strategy.agent_weights) {
      setAgentWeights({
        macro: (strategy.agent_weights.macro || 0.4) * 100,
        onchain: (strategy.agent_weights.onchain || 0.4) * 100,
        ta: (strategy.agent_weights.ta || 0.2) * 100,
      });
    } else {
      // Use default weights
      setAgentWeights({ macro: 40, onchain: 40, ta: 20 });
    }

    // Parse consecutive signal config from strategy (if exists)
    if ((strategy as any).consecutive_signal_threshold !== undefined) {
      setConsecutiveSignalConfig({
        consecutiveSignalThreshold: (strategy as any).consecutive_signal_threshold || 30,
        accelerationMultiplierMin: (strategy as any).acceleration_multiplier_min || 1.1,
        accelerationMultiplierMax: (strategy as any).acceleration_multiplier_max || 2.0,
      });
    } else {
      // Use default config
      setConsecutiveSignalConfig({
        consecutiveSignalThreshold: 30,
        accelerationMultiplierMin: 1.1,
        accelerationMultiplierMax: 2.0,
      });
    }

    // Parse trading thresholds from strategy (if exists)
    if ((strategy as any).fg_circuit_breaker_threshold !== undefined) {
      setTradingThresholds({
        fgCircuitBreakerThreshold: (strategy as any).fg_circuit_breaker_threshold || 20,
        fgPositionAdjustThreshold: (strategy as any).fg_position_adjust_threshold || 30,
        buyThreshold: (strategy as any).buy_threshold || 50,
        partialSellThreshold: (strategy as any).partial_sell_threshold || 50,
        fullSellThreshold: (strategy as any).full_sell_threshold || 45,
      });
    } else {
      // Use default thresholds
      setTradingThresholds({
        fgCircuitBreakerThreshold: 20,
        fgPositionAdjustThreshold: 30,
        buyThreshold: 50,
        partialSellThreshold: 50,
        fullSellThreshold: 45,
      });
    }

    setSettingsOpen(true);
  }

  async function handleSaveSettings() {
    if (!selectedStrategy) return;

    const periodMinutes = parseInt(rebalancePeriod, 10);
    if (isNaN(periodMinutes) || periodMinutes < 1 || periodMinutes > 1440) {
      alert('Please enter a valid rebalance period between 1 and 1440 minutes');
      return;
    }

    // Validate agent weights total
    const totalWeight = agentWeights.macro + agentWeights.onchain + agentWeights.ta;
    if (Math.abs(totalWeight - 100) > 0.1) {
      alert('Agent weights must sum to 100%');
      return;
    }

    // Validate consecutive signal config
    if (
      consecutiveSignalConfig.consecutiveSignalThreshold < 1 ||
      consecutiveSignalConfig.consecutiveSignalThreshold > 1000
    ) {
      alert('Consecutive signal threshold must be between 1 and 1000');
      return;
    }

    if (
      consecutiveSignalConfig.accelerationMultiplierMin < 1.0 ||
      consecutiveSignalConfig.accelerationMultiplierMin > consecutiveSignalConfig.accelerationMultiplierMax ||
      consecutiveSignalConfig.accelerationMultiplierMax > 5.0
    ) {
      alert('Invalid multiplier range. Min must be ≥1.0, Max must be ≤5.0, and Min ≤ Max');
      return;
    }

    // Validate trading thresholds
    if (
      tradingThresholds.fgCircuitBreakerThreshold < 0 ||
      tradingThresholds.fgCircuitBreakerThreshold > 100 ||
      tradingThresholds.fgPositionAdjustThreshold < 0 ||
      tradingThresholds.fgPositionAdjustThreshold > 100
    ) {
      alert('Fear & Greed thresholds must be between 0 and 100');
      return;
    }

    if (
      tradingThresholds.buyThreshold < 0 ||
      tradingThresholds.buyThreshold > 100 ||
      tradingThresholds.partialSellThreshold < 0 ||
      tradingThresholds.partialSellThreshold > 100 ||
      tradingThresholds.fullSellThreshold < 0 ||
      tradingThresholds.fullSellThreshold > 100
    ) {
      alert('Conviction score thresholds must be between 0 and 100');
      return;
    }

    // Validate threshold logic: fullSell <= partialSell <= buy
    if (tradingThresholds.fullSellThreshold > tradingThresholds.partialSellThreshold) {
      alert('Full Sell threshold must be ≤ Partial Sell threshold');
      return;
    }

    try {
      setSettingsSaving(true);
      await updateStrategySettings(selectedStrategy.id, {
        rebalancePeriodMinutes: periodMinutes,
        agentWeights: agentWeights,
        consecutiveSignalConfig: consecutiveSignalConfig,
        tradingThresholds: tradingThresholds,
      });

      // Update local state - convert weights back to 0-1 range for storage
      setStrategies(prev =>
        prev.map(s =>
          s.id === selectedStrategy.id
            ? {
                ...s,
                rebalance_period_minutes: periodMinutes,
                agent_weights: {
                  macro: agentWeights.macro / 100,
                  onchain: agentWeights.onchain / 100,
                  ta: agentWeights.ta / 100,
                },
                consecutive_signal_threshold: consecutiveSignalConfig.consecutiveSignalThreshold,
                acceleration_multiplier_min: consecutiveSignalConfig.accelerationMultiplierMin,
                acceleration_multiplier_max: consecutiveSignalConfig.accelerationMultiplierMax,
                fg_circuit_breaker_threshold: tradingThresholds.fgCircuitBreakerThreshold,
                fg_position_adjust_threshold: tradingThresholds.fgPositionAdjustThreshold,
                buy_threshold: tradingThresholds.buyThreshold,
                partial_sell_threshold: tradingThresholds.partialSellThreshold,
                full_sell_threshold: tradingThresholds.fullSellThreshold,
              } as AdminStrategy
            : s
        )
      );

      setSettingsOpen(false);
      alert('Strategy settings updated successfully!');
    } catch (err: any) {
      let errorMessage = 'Failed to update settings';
      
      // 尝试从多个来源提取错误信息
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
      console.error('Error details:', {
        response: err.response,
        message: err.message,
        data: err.response?.data
      });
    } finally {
      setSettingsSaving(false);
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p>Loading admin panel...</p>
        </div>
      </div>
    );
  }

  // Error state (403 Forbidden means not admin)
  if (error) {
    const isPermissionError = error.includes('403') || error.toLowerCase().includes('admin');

    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <div style={{
          background: 'rgba(15, 23, 42, 0.5)',
          border: '1px solid rgba(239, 68, 68, 0.5)',
          borderRadius: '12px',
          maxWidth: '448px',
          padding: '24px',
          textAlign: 'center'
        }}>
          <Lock style={{ width: '64px', height: '64px', color: '#f87171', margin: '0 auto 16px' }} />
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: 'white', marginBottom: '8px' }}>
            {isPermissionError ? 'Access Denied' : 'Error'}
          </h2>
          <p style={{ color: '#94a3b8', marginBottom: '16px' }}>
            {isPermissionError
              ? 'You do not have administrator privileges to access this page.'
              : error}
          </p>
          <Button
            onClick={loadStrategies}
            className="bg-purple-600 hover:bg-purple-700"
          >
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  // Statistics
  const totalStrategies = strategies.length;
  const activeStrategies = strategies.filter(s => s.is_active).length;
  const totalValue = strategies.reduce((sum, s) => sum + s.total_value, 0);
  const totalPnL = strategies.reduce((sum, s) => sum + s.total_pnl, 0);

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.headerTitle}>
            <Shield className="w-6 h-6 text-purple-400" />
            Admin Panel
          </h1>
          <p className={styles.headerSubtitle}>
            Manage all strategies across all users
          </p>
        </div>
        <Button
          onClick={loadStrategies}
          variant="outline"
          className="bg-slate-800 border-slate-700 hover:bg-slate-700 text-white"
        >
          Refresh
        </Button>
      </div>

      {/* Statistics Cards */}
      <div className={styles.statsContainer}>
        <div className={styles.statCard}>
          <div className={styles.statContent}>
            <Users className={`${styles.statIcon} text-purple-400`} />
            <div>
              <p className={styles.statLabel}>Total Strategies</p>
              <p className={`${styles.statValue} text-white`}>{totalStrategies}</p>
            </div>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statContent}>
            <TrendingUp className={`${styles.statIcon} text-emerald-400`} />
            <div>
              <p className={styles.statLabel}>Active</p>
              <p className={`${styles.statValue} text-emerald-400`}>{activeStrategies}</p>
            </div>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statContent}>
            <TrendingUp className={`${styles.statIcon} text-blue-400`} />
            <div>
              <p className={styles.statLabel}>Total Value</p>
              <p className={`${styles.statValue} text-white`}>
                ${totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </p>
            </div>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statContent}>
            {totalPnL >= 0 ? (
              <TrendingUp className={`${styles.statIcon} text-emerald-400`} />
            ) : (
              <TrendingDown className={`${styles.statIcon} text-red-400`} />
            )}
            <div>
              <p className={styles.statLabel}>Total P&L</p>
              <p className={`${styles.statValue} ${totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Strategy List */}
      <div className={styles.tableCard}>
        <div className={styles.tableHeader}>
          <h2 className={styles.tableTitle}>All Strategies</h2>
        </div>
        {strategies.length === 0 ? (
          <div className={styles.emptyState}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '16px',
              background: 'rgba(30, 41, 59, 0.5)',
              border: '1px solid #334155',
              borderRadius: '8px'
            }}>
              <AlertCircle style={{ width: '16px', height: '16px', color: '#94a3b8' }} />
              <span style={{ color: '#94a3b8', fontSize: '14px' }}>
                No strategies found in the system.
              </span>
            </div>
          </div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Strategy Name</th>
                  <th>User ID</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th className={styles.alignRight}>Total Value</th>
                  <th className={styles.alignRight}>P&L</th>
                  <th className={styles.alignRight}>P&L %</th>
                  <th className={styles.alignCenter}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {strategies.map((strategy) => (
                  <tr key={strategy.id}>
                    <td className={styles.strategyName}>
                      {strategy.name}
                    </td>
                    <td className={styles.userId}>
                      {strategy.user_id}
                    </td>
                    <td>
                      <span className={`${styles.badge} ${styles.badgePurple}`}>
                        {strategy.strategy_name}
                      </span>
                    </td>
                    <td>
                      <span className={`${styles.badge} ${strategy.is_active ? styles.badgeGreen : styles.badgeGray}`}>
                        {strategy.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className={styles.alignRight} style={{ color: 'white' }}>
                      ${strategy.total_value.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}
                    </td>
                    <td className={`${styles.alignRight} ${strategy.total_pnl >= 0 ? styles.valuePositive : styles.valueNegative}`}>
                      {strategy.total_pnl >= 0 ? '+' : ''}${strategy.total_pnl.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}
                    </td>
                    <td className={`${styles.alignRight} ${strategy.total_pnl_percent >= 0 ? styles.valuePositive : styles.valueNegative}`}>
                      {strategy.total_pnl_percent >= 0 ? '+' : ''}{strategy.total_pnl_percent.toFixed(2)}%
                    </td>
                    <td className={styles.alignCenter}>
                      <div className={styles.actions}>
                        <button
                          onClick={() => handleOpenSettings(strategy)}
                          className={`${styles.actionButton} ${styles.buttonSettings}`}
                        >
                          <Settings className={styles.buttonIcon} />
                          Settings
                        </button>
                        <button
                          onClick={() => handleToggle(strategy.id, strategy.is_active)}
                          disabled={toggleLoading[strategy.id]}
                          className={`${styles.actionButton} ${strategy.is_active ? styles.buttonDeactivate : styles.buttonActivate}`}
                        >
                          {toggleLoading[strategy.id] ? (
                            <>
                              <div className={styles.spinner} />
                              Updating...
                            </>
                          ) : (
                            strategy.is_active ? 'Deactivate' : 'Activate'
                          )}
                        </button>
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
        <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle>Strategy Settings</DialogTitle>
            <DialogDescription className="text-slate-400">
              Configure strategy execution parameters for {selectedStrategy?.name}
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="period" className="w-full">
            <TabsList className="flex flex-wrap w-full bg-slate-800 gap-1">
              <TabsTrigger value="period" className="flex-1 min-w-[80px] text-xs text-slate-300 data-[state=active]:text-slate-900 data-[state=active]:bg-white">Period</TabsTrigger>
              <TabsTrigger value="weights" className="flex-1 min-w-[80px] text-xs text-slate-300 data-[state=active]:text-slate-900 data-[state=active]:bg-white">Weights</TabsTrigger>
              <TabsTrigger value="consecutive" className="flex-1 min-w-[80px] text-xs text-slate-300 data-[state=active]:text-slate-900 data-[state=active]:bg-white">Combo</TabsTrigger>
              <TabsTrigger value="thresholds" className="flex-1 min-w-[80px] text-xs text-slate-300 data-[state=active]:text-slate-900 data-[state=active]:bg-white">Thresholds</TabsTrigger>
            </TabsList>

            <TabsContent value="period" className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="rebalance-period" className="text-sm font-medium text-slate-200">
                  Rebalance Period (minutes)
                </Label>
                <Input
                  id="rebalance-period"
                  type="number"
                  min="1"
                  max="1440"
                  value={rebalancePeriod}
                  onChange={(e) => setRebalancePeriod(e.target.value)}
                  className="bg-slate-800 border-slate-600 text-white"
                  placeholder="Enter period in minutes (1-1440)"
                />
                <p className="text-xs text-slate-400">
                  Allowed range: 1 minute to 1440 minutes (24 hours)
                </p>
              </div>
            </TabsContent>

            <TabsContent value="weights" className="py-4">
              <AgentWeightConfigurator
                initialWeights={agentWeights}
                onChange={setAgentWeights}
                disabled={settingsSaving}
              />
            </TabsContent>

            <TabsContent value="consecutive" className="py-4">
              <ConsecutiveSignalConfigurator
                initialConfig={consecutiveSignalConfig}
                onChange={setConsecutiveSignalConfig}
                disabled={settingsSaving}
              />
            </TabsContent>

            <TabsContent value="thresholds" className="py-4">
              <TradingThresholdsConfigurator
                initialThresholds={tradingThresholds}
                onChange={setTradingThresholds}
                disabled={settingsSaving}
              />
            </TabsContent>
          </Tabs>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsOpen(false)}
              className="bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
              disabled={settingsSaving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={settingsSaving}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              {settingsSaving ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Saving...
                </span>
              ) : (
                'Save Changes'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
