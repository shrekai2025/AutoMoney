import { Label } from "./ui/label";
import { Input } from "./ui/input";

export interface TradingThresholds {
  fgCircuitBreakerThreshold: number;
  fgPositionAdjustThreshold: number;
  buyThreshold: number;
  fullSellThreshold: number;
  // 注意: partial_sell_threshold 已移除，部分减仓区间现在是 [fullSellThreshold, buyThreshold)
}

interface TradingThresholdsConfiguratorProps {
  initialThresholds: TradingThresholds;
  onChange: (thresholds: TradingThresholds) => void;
  disabled?: boolean;
}

export function TradingThresholdsConfigurator({
  initialThresholds,
  onChange,
  disabled = false,
}: TradingThresholdsConfiguratorProps) {
  const handleChange = (field: keyof TradingThresholds, value: number) => {
    onChange({
      ...initialThresholds,
      [field]: value,
    });
  };

  return (
    <div className="space-y-6">
      {/* Fear & Greed Thresholds */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 border-b border-slate-700 pb-2">
          Fear & Greed Index Thresholds
        </h3>

        <div className="space-y-2">
          <Label htmlFor="fg-circuit-breaker" className="text-sm font-medium text-slate-200">
            Circuit Breaker Threshold (0-100)
          </Label>
          <Input
            id="fg-circuit-breaker"
            type="number"
            min="0"
            max="100"
            step="1"
            value={initialThresholds.fgCircuitBreakerThreshold}
            onChange={(e) => handleChange('fgCircuitBreakerThreshold', parseFloat(e.target.value))}
            className="bg-slate-800 border-slate-600 text-white"
            disabled={disabled}
          />
          <p className="text-xs text-slate-400">
            When F&G Index &lt; this value, trading will be completely halted (熔断). Default: 20
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="fg-position-adjust" className="text-sm font-medium text-slate-200">
            Position Adjustment Threshold (0-100)
          </Label>
          <Input
            id="fg-position-adjust"
            type="number"
            min="0"
            max="100"
            step="1"
            value={initialThresholds.fgPositionAdjustThreshold}
            onChange={(e) => handleChange('fgPositionAdjustThreshold', parseFloat(e.target.value))}
            className="bg-slate-800 border-slate-600 text-white"
            disabled={disabled}
          />
          <p className="text-xs text-slate-400">
            When F&G Index &lt; this value, position size will be reduced by 20%. Default: 30
          </p>
        </div>
      </div>

      {/* Conviction Score Thresholds */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 border-b border-slate-700 pb-2">
          Conviction Score Thresholds
        </h3>

        <div className="space-y-2">
          <Label htmlFor="buy-threshold" className="text-sm font-medium text-slate-200">
            Buy Threshold (0-100)
          </Label>
          <Input
            id="buy-threshold"
            type="number"
            min="0"
            max="100"
            step="0.1"
            value={initialThresholds.buyThreshold}
            onChange={(e) => handleChange('buyThreshold', parseFloat(e.target.value))}
            className="bg-slate-800 border-slate-600 text-white"
            disabled={disabled}
          />
          <p className="text-xs text-slate-400">
            When Conviction Score ≥ this value, BUY signal is generated. Default: 50
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="full-sell-threshold" className="text-sm font-medium text-slate-200">
            Full Sell Threshold (0-100)
          </Label>
          <Input
            id="full-sell-threshold"
            type="number"
            min="0"
            max="100"
            step="0.1"
            value={initialThresholds.fullSellThreshold}
            onChange={(e) => handleChange('fullSellThreshold', parseFloat(e.target.value))}
            className="bg-slate-800 border-slate-600 text-white"
            disabled={disabled}
          />
          <p className="text-xs text-slate-400">
            When Conviction Score &lt; this value, full liquidation (清仓 100%). Default: 45
          </p>
        </div>
      </div>

      {/* Visual Guide */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 space-y-2">
        <h4 className="text-xs font-semibold text-slate-300 mb-2">Trading Logic Summary</h4>
        <div className="text-xs text-slate-400 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-red-400">●</span>
            <span>Score &lt; {initialThresholds.fullSellThreshold}: Full Sell (100%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-yellow-400">●</span>
            <span>{initialThresholds.fullSellThreshold} ≤ Score &lt; {initialThresholds.buyThreshold}: Partial Sell (0-50%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-green-400">●</span>
            <span>Score ≥ {initialThresholds.buyThreshold}: Buy (0.2%-0.5%)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
