import React, { useState, useEffect } from 'react';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Alert, AlertDescription } from './ui/alert';
import { Info } from 'lucide-react';

export interface ConsecutiveSignalConfig {
  consecutiveSignalThreshold: number;
  accelerationMultiplierMin: number;
  accelerationMultiplierMax: number;
}

interface ConsecutiveSignalConfiguratorProps {
  initialConfig?: ConsecutiveSignalConfig;
  onChange: (config: ConsecutiveSignalConfig) => void;
  disabled?: boolean;
}

const DEFAULT_CONFIG: ConsecutiveSignalConfig = {
  consecutiveSignalThreshold: 30,
  accelerationMultiplierMin: 1.1,
  accelerationMultiplierMax: 2.0,
};

export const ConsecutiveSignalConfigurator: React.FC<ConsecutiveSignalConfiguratorProps> = ({
  initialConfig,
  onChange,
  disabled = false,
}) => {
  const [config, setConfig] = useState<ConsecutiveSignalConfig>(
    initialConfig || DEFAULT_CONFIG
  );

  useEffect(() => {
    if (initialConfig) {
      setConfig(initialConfig);
    }
  }, [initialConfig]);

  const handleChange = (field: keyof ConsecutiveSignalConfig, value: string) => {
    const numValue = parseFloat(value);

    if (isNaN(numValue)) return;

    const newConfig = { ...config, [field]: numValue };
    setConfig(newConfig);
    onChange(newConfig);
  };

  // 验证配置有效性
  const isValid =
    config.consecutiveSignalThreshold >= 1 &&
    config.consecutiveSignalThreshold <= 1000 &&
    config.accelerationMultiplierMin >= 1.0 &&
    config.accelerationMultiplierMin <= config.accelerationMultiplierMax &&
    config.accelerationMultiplierMax <= 5.0;

  return (
    <div className="space-y-6">
      {/* 说明 */}
      <Alert className="bg-slate-800/50 border-slate-700">
        <Info className="h-4 w-4 text-blue-400" />
        <AlertDescription className="text-slate-300 text-sm">
          连续信号机制：当策略连续产生看涨信号(Conviction Score ≥ 70)达到设定次数时，触发仓位加速积累，提高每次买入的资金比例。
        </AlertDescription>
      </Alert>

      {/* 配置输入 */}
      <div className="space-y-4">
        {/* 连续信号阈值 */}
        <div className="space-y-2">
          <Label htmlFor="consecutive-threshold" className="text-sm font-medium text-slate-200">
            连续信号阈值 (次数)
          </Label>
          <Input
            id="consecutive-threshold"
            type="number"
            min="1"
            max="1000"
            step="1"
            value={config.consecutiveSignalThreshold}
            onChange={(e) => handleChange('consecutiveSignalThreshold', e.target.value)}
            disabled={disabled}
            className="bg-slate-800 border-slate-600 text-white"
          />
          <p className="text-xs text-slate-400">
            达到此次数后触发加速积累机制 (建议: 20-50次)
          </p>
        </div>

        {/* 最小乘数 */}
        <div className="space-y-2">
          <Label htmlFor="multiplier-min" className="text-sm font-medium text-slate-200">
            加速乘数 - 最小值
          </Label>
          <Input
            id="multiplier-min"
            type="number"
            min="1.0"
            max="5.0"
            step="0.1"
            value={config.accelerationMultiplierMin}
            onChange={(e) => handleChange('accelerationMultiplierMin', e.target.value)}
            disabled={disabled}
            className="bg-slate-800 border-slate-600 text-white"
          />
          <p className="text-xs text-slate-400">
            刚达到阈值时的仓位乘数 (建议: 1.1-1.5)
          </p>
        </div>

        {/* 最大乘数 */}
        <div className="space-y-2">
          <Label htmlFor="multiplier-max" className="text-sm font-medium text-slate-200">
            加速乘数 - 最大值
          </Label>
          <Input
            id="multiplier-max"
            type="number"
            min="1.0"
            max="5.0"
            step="0.1"
            value={config.accelerationMultiplierMax}
            onChange={(e) => handleChange('accelerationMultiplierMax', e.target.value)}
            disabled={disabled}
            className="bg-slate-800 border-slate-600 text-white"
          />
          <p className="text-xs text-slate-400">
            连续信号持续时的最大乘数 (建议: 1.5-3.0)
          </p>
        </div>

        {/* 当前配置预览 */}
        <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700 space-y-2">
          <Label className="text-sm font-medium text-slate-200">配置预览</Label>
          <div className="text-xs text-slate-300 space-y-1">
            <p>
              • 连续 <span className="text-emerald-400 font-semibold">{config.consecutiveSignalThreshold}</span> 次看涨信号后触发加速
            </p>
            <p>
              • 仓位乘数范围: <span className="text-emerald-400 font-semibold">{config.accelerationMultiplierMin}x</span> ~ <span className="text-emerald-400 font-semibold">{config.accelerationMultiplierMax}x</span>
            </p>
            <p>
              • 示例: 基础仓位0.5%，达到阈值后为 <span className="text-emerald-400 font-semibold">{(0.5 * config.accelerationMultiplierMin).toFixed(2)}%</span>，持续后最高 <span className="text-emerald-400 font-semibold">{(0.5 * config.accelerationMultiplierMax).toFixed(2)}%</span>
            </p>
          </div>
        </div>

        {/* 验证提示 */}
        {!isValid && (
          <Alert className="bg-red-900/20 border-red-500/50">
            <AlertDescription className="text-red-400 text-sm">
              ⚠️ 配置无效：请确保阈值在1-1000之间，乘数最小值≥1.0，最大值≥最小值且≤5.0
            </AlertDescription>
          </Alert>
        )}
      </div>

      {/* 使用说明 */}
      <div className="text-xs text-slate-400 space-y-1 pt-4 border-t border-slate-700">
        <p className="font-medium text-slate-300">使用说明:</p>
        <p>• 连续信号在每次策略执行时更新，任何非看涨信号会重置计数器</p>
        <p>• 乘数在达到阈值后开始从最小值逐渐增长，最多100次内达到最大值</p>
        <p>• 建议保守设置，避免过度积累风险</p>
      </div>
    </div>
  );
};
