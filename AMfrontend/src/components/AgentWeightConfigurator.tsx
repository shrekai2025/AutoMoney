import React, { useState, useEffect } from 'react';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Button } from './ui/button';

export interface AgentWeights {
  macro: number;
  onchain: number;
  ta: number;
}

interface AgentWeightConfiguratorProps {
  initialWeights?: AgentWeights;
  onChange: (weights: AgentWeights) => void;
  disabled?: boolean;
}

// 预设配置
const PRESETS = {
  bullMarketEarly: {
    name: '牛市初期',
    description: '看重链上数据和技术指标，宏观环境相对稳定',
    weights: { macro: 30, onchain: 50, ta: 20 },
  },
  bullMarketLate: {
    name: '牛市末期',
    description: '关注宏观风险和技术面过热信号',
    weights: { macro: 50, onchain: 20, ta: 30 },
  },
  bearMarket: {
    name: '熊市期间',
    description: '重视宏观经济和链上底部信号',
    weights: { macro: 45, onchain: 35, ta: 20 },
  },
};

const DEFAULT_WEIGHTS: AgentWeights = { macro: 40, onchain: 40, ta: 20 };

export const AgentWeightConfigurator: React.FC<AgentWeightConfiguratorProps> = ({
  initialWeights,
  onChange,
  disabled = false,
}) => {
  const [weights, setWeights] = useState<AgentWeights>(
    initialWeights || DEFAULT_WEIGHTS
  );
  const [editingField, setEditingField] = useState<string | null>(null);

  useEffect(() => {
    if (initialWeights) {
      setWeights(initialWeights);
    }
  }, [initialWeights]);

  // 计算总权重
  const totalWeight = weights.macro + weights.onchain + weights.ta;

  // 计算哪个字段应该自动调整
  const getAutoAdjustField = (): keyof AgentWeights | null => {
    const fields: (keyof AgentWeights)[] = ['macro', 'onchain', 'ta'];
    const emptyFields = fields.filter(
      (field) => weights[field] === 0 || !weights[field]
    );

    // 如果只有一个字段为空，自动调整该字段
    if (emptyFields.length === 1) {
      return emptyFields[0];
    }

    return null;
  };

  const handleWeightChange = (field: keyof AgentWeights, value: string) => {
    const numValue = parseFloat(value) || 0;

    // 限制在0-100之间
    const clampedValue = Math.max(0, Math.min(100, numValue));

    const newWeights = { ...weights, [field]: clampedValue };

    // 检查是否有需要自动调整的字段
    const autoField = getAutoAdjustField();
    if (autoField && autoField !== field) {
      // 计算其他字段的总和
      const otherFields = (['macro', 'onchain', 'ta'] as const).filter(
        (f) => f !== autoField
      );
      const otherSum = otherFields.reduce(
        (sum, f) => sum + newWeights[f],
        0
      );

      // 自动计算剩余值
      newWeights[autoField] = Math.max(0, 100 - otherSum);
    }

    setWeights(newWeights);
    onChange(newWeights);
  };

  const handlePresetClick = (preset: typeof PRESETS[keyof typeof PRESETS]) => {
    const newWeights = preset.weights;
    setWeights(newWeights);
    onChange(newWeights);
  };

  const autoField = getAutoAdjustField();

  // 验证权重总和
  const isValid = Math.abs(totalWeight - 100) < 0.1;

  return (
    <div className="space-y-6">
      {/* 预设按钮 */}
      <div className="space-y-2">
        <Label className="text-sm font-medium text-slate-200">快捷预设</Label>
        <div className="grid grid-cols-3 gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handlePresetClick(PRESETS.bullMarketEarly)}
            disabled={disabled}
            className="flex flex-col h-auto py-2 px-3 bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white"
          >
            <span className="font-medium">{PRESETS.bullMarketEarly.name}</span>
            <span className="text-xs text-slate-400 mt-1">
              {PRESETS.bullMarketEarly.weights.macro}/{PRESETS.bullMarketEarly.weights.onchain}/{PRESETS.bullMarketEarly.weights.ta}
            </span>
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handlePresetClick(PRESETS.bullMarketLate)}
            disabled={disabled}
            className="flex flex-col h-auto py-2 px-3 bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white"
          >
            <span className="font-medium">{PRESETS.bullMarketLate.name}</span>
            <span className="text-xs text-slate-400 mt-1">
              {PRESETS.bullMarketLate.weights.macro}/{PRESETS.bullMarketLate.weights.onchain}/{PRESETS.bullMarketLate.weights.ta}
            </span>
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handlePresetClick(PRESETS.bearMarket)}
            disabled={disabled}
            className="flex flex-col h-auto py-2 px-3 bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white"
          >
            <span className="font-medium">{PRESETS.bearMarket.name}</span>
            <span className="text-xs text-slate-400 mt-1">
              {PRESETS.bearMarket.weights.macro}/{PRESETS.bearMarket.weights.onchain}/{PRESETS.bearMarket.weights.ta}
            </span>
          </Button>
        </div>
      </div>

      {/* 权重输入 */}
      <div className="space-y-4">
        <Label className="text-sm font-medium text-slate-200">Agent权重配置</Label>

        {/* MacroAgent */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="weight-macro" className="text-sm text-slate-200">
              MacroAgent (宏观分析)
            </Label>
            <span className="text-sm text-slate-400">
              {autoField === 'macro' && '(自动计算)'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Input
              id="weight-macro"
              type="number"
              min="0"
              max="100"
              step="1"
              value={weights.macro}
              onChange={(e) => handleWeightChange('macro', e.target.value)}
              onFocus={() => setEditingField('macro')}
              onBlur={() => setEditingField(null)}
              disabled={disabled || autoField === 'macro'}
              className="flex-1"
              style={{ backgroundColor: '#1e293b', borderColor: '#475569', color: '#ffffff' }}
            />
            <span className="text-sm w-6 text-slate-300">%</span>
          </div>
        </div>

        {/* OnChainAgent */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="weight-onchain" className="text-sm text-slate-200">
              OnChainAgent (链上分析)
            </Label>
            <span className="text-sm text-slate-400">
              {autoField === 'onchain' && '(自动计算)'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Input
              id="weight-onchain"
              type="number"
              min="0"
              max="100"
              step="1"
              value={weights.onchain}
              onChange={(e) => handleWeightChange('onchain', e.target.value)}
              onFocus={() => setEditingField('onchain')}
              onBlur={() => setEditingField(null)}
              disabled={disabled || autoField === 'onchain'}
              className="flex-1"
              style={{ backgroundColor: '#1e293b', borderColor: '#475569', color: '#ffffff' }}
            />
            <span className="text-sm w-6 text-slate-300">%</span>
          </div>
        </div>

        {/* TAAgent */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="weight-ta" className="text-sm text-slate-200">
              TAAgent (技术分析)
            </Label>
            <span className="text-sm text-slate-400">
              {autoField === 'ta' && '(自动计算)'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Input
              id="weight-ta"
              type="number"
              min="0"
              max="100"
              step="1"
              value={weights.ta}
              onChange={(e) => handleWeightChange('ta', e.target.value)}
              onFocus={() => setEditingField('ta')}
              onBlur={() => setEditingField(null)}
              disabled={disabled || autoField === 'ta'}
              className="flex-1"
              style={{ backgroundColor: '#1e293b', borderColor: '#475569', color: '#ffffff' }}
            />
            <span className="text-sm w-6 text-slate-300">%</span>
          </div>
        </div>

        {/* 总计显示 */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-700">
          <Label className="text-sm font-medium text-slate-200">总计</Label>
          <div
            className={`text-sm font-medium ${
              isValid ? 'text-emerald-400' : 'text-red-600'
            }`}
          >
            {totalWeight.toFixed(0)}%
            {!isValid && ' (必须等于100%)'}
          </div>
        </div>
      </div>

      {/* 说明文字 */}
      <div className="text-xs text-slate-400 space-y-1">
        <p>• 所有Agent权重之和必须为100%</p>
        <p>• 当只有一个输入框未填时，该框会自动计算剩余权重</p>
        <p>• 使用预设按钮可快速应用常见市场环境配置</p>
      </div>
    </div>
  );
};
