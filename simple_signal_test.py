"""简单信号生成测试"""

import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.decision.signal_generator import signal_generator

# 模拟市场数据
market_data = {
    "btc_price_change_24h": 0.0,
    "fear_greed": {"value": 20},
    "macro": {"dxy_index": 103},
}

# 模拟Portfolio状态（使用当前配置）
portfolio_state = {
    "consecutive_bullish_count": 0,
    "last_conviction_score": 39.31,
    "consecutive_signal_threshold": 30,
    "acceleration_multiplier_min": 1.1,
    "acceleration_multiplier_max": 2.0,
    "fg_circuit_breaker_threshold": 5,  # 当前配置
    "fg_position_adjust_threshold": 20,
    "buy_threshold": 50.0,
    "partial_sell_threshold": 50.0,
    "full_sell_threshold": 40.0,
}

print("=" * 100)
print("📊 信号生成测试")
print("=" * 100)
print()

print("输入:")
print(f"  Conviction Score: 39.31")
print(f"  Fear & Greed: 20")
print(f"  熔断阈值: 5")
print(f"  全部清仓阈值: 40")
print()

result = signal_generator.generate_signal(
    conviction_score=39.31,
    market_data=market_data,
    current_position=0.05,
    portfolio_state=portfolio_state,
)

print("输出:")
print(f"  Signal: {result.signal.value}")
print(f"  Should Execute: {result.should_execute}")
print(f"  Reasons: {result.reasons}")
print()

if result.signal.value == "SELL":
    print("✅ 正确: Conviction(39.31) < 全部清仓阈值(40) → SELL")
elif result.signal.value == "HOLD":
    print("❌ 错误: 应该是SELL，但返回了HOLD")
    print()
    print("检查熔断:")
    print(f"  F&G({market_data['fear_greed']['value']}) < 熔断阈值({portfolio_state['fg_circuit_breaker_threshold']})? {market_data['fear_greed']['value'] < portfolio_state['fg_circuit_breaker_threshold']}")

print()
print("=" * 100)
