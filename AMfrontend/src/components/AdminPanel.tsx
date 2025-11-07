import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { Shield, Users, TrendingUp, TrendingDown, AlertCircle, Lock, Settings } from "lucide-react";
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
import { fetchAllStrategies, toggleStrategy } from "../lib/adminApi";
import { updateStrategySettings } from "../lib/marketplaceApi";
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
    setSettingsOpen(true);
  }

  async function handleSaveSettings() {
    if (!selectedStrategy) return;

    const periodMinutes = parseInt(rebalancePeriod, 10);
    if (isNaN(periodMinutes) || periodMinutes < 1 || periodMinutes > 1440) {
      alert('Please enter a valid rebalance period between 1 and 1440 minutes');
      return;
    }

    try {
      setSettingsSaving(true);
      await updateStrategySettings(selectedStrategy.id, periodMinutes);

      // Update local state
      setStrategies(prev =>
        prev.map(s =>
          s.id === selectedStrategy.id
            ? { ...s, rebalance_period_minutes: periodMinutes } as AdminStrategy
            : s
        )
      );

      setSettingsOpen(false);
      alert('Strategy settings updated successfully!');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to update settings';
      alert(`Error: ${errorMessage}`);
      console.error('Failed to update settings:', err);
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
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="bg-slate-900/50 border-red-500/50 max-w-md">
          <CardContent className="p-6 text-center">
            <Lock className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">
              {isPermissionError ? 'Access Denied' : 'Error'}
            </h2>
            <p className="text-slate-400 mb-4">
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
          </CardContent>
        </Card>
      </div>
    );
  }

  // Statistics
  const totalStrategies = strategies.length;
  const activeStrategies = strategies.filter(s => s.is_active).length;
  const totalValue = strategies.reduce((sum, s) => sum + s.total_value, 0);
  const totalPnL = strategies.reduce((sum, s) => sum + s.total_pnl, 0);

  return (
    <div className="space-y-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-purple-400" />
            Admin Panel
          </h1>
          <p className="text-slate-400 text-sm mt-1">
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <Card className="bg-slate-900/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 mb-1">Total Strategies</p>
                <p className="text-2xl font-bold text-white">{totalStrategies}</p>
              </div>
              <Users className="w-8 h-8 text-purple-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 mb-1">Active Strategies</p>
                <p className="text-2xl font-bold text-emerald-400">{activeStrategies}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 mb-1">Total Value</p>
                <p className="text-2xl font-bold text-white">
                  ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 mb-1">Total P&L</p>
                <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
              {totalPnL >= 0 ? (
                <TrendingUp className="w-8 h-8 text-emerald-400" />
              ) : (
                <TrendingDown className="w-8 h-8 text-red-400" />
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Strategy List */}
      <Card className="bg-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="text-white text-lg">All Strategies</CardTitle>
        </CardHeader>
        <CardContent>
          {strategies.length === 0 ? (
            <Alert className="bg-slate-800/50 border-slate-700">
              <AlertCircle className="h-4 w-4 text-slate-400" />
              <AlertDescription className="text-slate-400">
                No strategies found in the system.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700 hover:bg-slate-800/50">
                    <TableHead className="text-slate-400">Strategy Name</TableHead>
                    <TableHead className="text-slate-400">User ID</TableHead>
                    <TableHead className="text-slate-400">Type</TableHead>
                    <TableHead className="text-slate-400">Status</TableHead>
                    <TableHead className="text-slate-400 text-right">Total Value</TableHead>
                    <TableHead className="text-slate-400 text-right">P&L</TableHead>
                    <TableHead className="text-slate-400 text-right">P&L %</TableHead>
                    <TableHead className="text-slate-400 text-center">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {strategies.map((strategy) => (
                    <TableRow
                      key={strategy.id}
                      className="border-slate-700 hover:bg-slate-800/30"
                    >
                      <TableCell className="text-white font-medium">
                        {strategy.name}
                      </TableCell>
                      <TableCell className="text-slate-300">
                        {strategy.user_id}
                      </TableCell>
                      <TableCell>
                        <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50">
                          {strategy.strategy_name}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            strategy.is_active
                              ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/50"
                              : "bg-slate-500/20 text-slate-400 border-slate-500/50"
                          }
                        >
                          {strategy.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-white">
                        ${strategy.total_value.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        })}
                      </TableCell>
                      <TableCell
                        className={`text-right font-medium ${
                          strategy.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}
                      >
                        {strategy.total_pnl >= 0 ? '+' : ''}${strategy.total_pnl.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        })}
                      </TableCell>
                      <TableCell
                        className={`text-right font-medium ${
                          strategy.total_pnl_percent >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}
                      >
                        {strategy.total_pnl_percent >= 0 ? '+' : ''}{strategy.total_pnl_percent.toFixed(2)}%
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex gap-2 justify-center">
                          <Button
                            onClick={() => handleOpenSettings(strategy)}
                            size="sm"
                            variant="outline"
                            className="min-w-[90px] h-8 text-xs font-medium bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-slate-700"
                          >
                            <Settings className="w-3 h-3 mr-1" />
                            Settings
                          </Button>
                          <Button
                            onClick={() => handleToggle(strategy.id, strategy.is_active)}
                            disabled={toggleLoading[strategy.id]}
                            size="sm"
                            variant="outline"
                            className={`
                              min-w-[100px] h-8 text-xs font-medium
                              ${strategy.is_active
                                ? 'bg-emerald-600/20 border-emerald-500 text-emerald-400 hover:bg-emerald-600/30'
                                : 'bg-slate-700/50 border-slate-600 text-slate-400 hover:bg-slate-700'
                              }
                            `}
                          >
                            {toggleLoading[strategy.id] ? (
                              <span className="flex items-center gap-2">
                                <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                Updating...
                              </span>
                            ) : (
                              strategy.is_active ? 'Deactivate' : 'Activate'
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Settings Modal */}
      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>Strategy Settings</DialogTitle>
            <DialogDescription className="text-slate-400">
              Configure strategy execution parameters for {selectedStrategy?.name}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
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
          </div>

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
