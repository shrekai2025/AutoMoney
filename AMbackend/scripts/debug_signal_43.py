"""调试Signal 43为什么变成HOLD"""
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.decision.signal_generator import SignalGenerator

# 模拟Score 43的情况
signal_gen = SignalGenerator()

# 场景1: 使用错误配置 (partial_sell_threshold = 51)
print("=" * 60)
print("场景1: 错误配置 (partial_sell_threshold = 51)")
print("=" * 60)

conviction_score = 43.14
market_data = {
    "btc_price": 102112.48,
    "btc_price_change_24h": 2.5,
    "fear_greed": {"value": 50},
    "macro": {"dxy_index": 105}
}
current_position = 0.479  # 持仓47.9%
portfolio_state = {
    "buy_threshold": 51.0,
    "partial_sell_threshold": 51.0,  # ❌ 错误配置
    "full_sell_threshold": 40.0,
    "fg_circuit_breaker_threshold": 20,
    "fg_position_adjust_threshold": 30,
    "consecutive_bullish_count": 0,
}

result = signal_gen.generate_signal(
    conviction_score=conviction_score,
    market_data=market_data,
    current_position=current_position,
    portfolio_state=portfolio_state
)

print(f"Conviction Score: {conviction_score}")
print(f"Current Position: {current_position * 100:.1f}%")
print(f"Config: buy_threshold={portfolio_state['buy_threshold']}, "
      f"partial_sell={portfolio_state['partial_sell_threshold']}, "
      f"full_sell={portfolio_state['full_sell_threshold']}")
print(f"\n结果:")
print(f"  Signal: {result.signal.value}")
print(f"  Signal Strength: {result.signal_strength:.4f}")
print(f"  Position Size: {result.position_size:.4f}")
print(f"  Should Execute: {result.should_execute}")
print(f"  Risk Level: {result.risk_level.value}")
print(f"  Reasons: {result.reasons}")
print(f"  Warnings: {result.warnings}")

# 场景2: 使用正确配置 (partial_sell_threshold = 40, 实际上应该用buy_threshold)
print("\n" + "=" * 60)
print("场景2: 修复后配置 (使用buy_threshold作为部分减仓上界)")
print("=" * 60)

portfolio_state_fixed = {
    "buy_threshold": 51.0,
    "full_sell_threshold": 40.0,
    "fg_circuit_breaker_threshold": 20,
    "fg_position_adjust_threshold": 30,
    "consecutive_bullish_count": 0,
}

result_fixed = signal_gen.generate_signal(
    conviction_score=conviction_score,
    market_data=market_data,
    current_position=current_position,
    portfolio_state=portfolio_state_fixed
)

print(f"Conviction Score: {conviction_score}")
print(f"Current Position: {current_position * 100:.1f}%")
print(f"Config: buy_threshold={portfolio_state_fixed['buy_threshold']}, "
      f"full_sell={portfolio_state_fixed['full_sell_threshold']}")
print(f"\n结果:")
print(f"  Signal: {result_fixed.signal.value}")
print(f"  Signal Strength: {result_fixed.signal_strength:.4f}")
print(f"  Position Size: {result_fixed.position_size:.4f} ({result_fixed.position_size * 100:.1f}% of holdings)")
print(f"  Should Execute: {result_fixed.should_execute}")
print(f"  Risk Level: {result_fixed.risk_level.value}")
print(f"  Reasons: {result_fixed.reasons}")
print(f"  Warnings: {result_fixed.warnings}")

# 计算实际卖出比例
if result_fixed.signal.value == "SELL" and current_position > 0:
    sell_percentage = (result_fixed.position_size / current_position) * 100
    print(f"\n  实际卖出比例: {sell_percentage:.1f}% of current position")
