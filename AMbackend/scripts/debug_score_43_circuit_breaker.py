"""调试Score 43 - 验证熔断器触发"""
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.decision.signal_generator import SignalGenerator

signal_gen = SignalGenerator()

print("=" * 60)
print("Score 43 实际情况重现")
print("=" * 60)

conviction_score = 43.142625
market_data = {
    "btc_price": 102112.48,
    "btc_price_change_24h": -0.992,
    "fear_greed": {"value": 15, "classification": "Extreme Fear"},  # ⚠️ 关键!
    "macro": {"dxy_index": 105}
}
current_position = 0.479  # 持仓47.9%
portfolio_state = {
    "buy_threshold": 51.0,
    "partial_sell_threshold": 51.0,
    "full_sell_threshold": 40.0,
    "fg_circuit_breaker_threshold": 20,  # ⚠️ 熔断阈值20
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
print(f"Fear & Greed: {market_data['fear_greed']['value']} (熔断阈值: {portfolio_state['fg_circuit_breaker_threshold']})")
print(f"Current Position: {current_position * 100:.1f}%")
print(f"\n结果:")
print(f"  Signal: {result.signal.value}")
print(f"  Signal Strength: {result.signal_strength:.4f}")
print(f"  Position Size: {result.position_size:.4f}")
print(f"  Should Execute: {result.should_execute}")
print(f"  Risk Level: {result.risk_level.value}")
print(f"  Reasons: {result.reasons}")
print(f"  Warnings: {result.warnings}")

print("\n" + "=" * 60)
print("结论:")
print("=" * 60)
if result.signal.value == "HOLD":
    print("✅ 熔断器触发! Fear & Greed = 15 < 20")
    print("   系统正确地暂停了交易，返回HOLD信号")
else:
    print("❌ 预期应该触发熔断器，但没有")
