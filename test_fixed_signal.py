"""测试修复后的信号生成"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

# 强制重新加载模块
import importlib
from app.services.decision import signal_generator as sg_module
importlib.reload(sg_module)
from app.services.decision.signal_generator import signal_generator

print("=" * 100)
print("🧪 测试修复后的信号生成")
print("=" * 100)
print()

# 模拟市场数据
market_data = {
    "btc_price_change_24h": 0.0,
    "fear_greed": {"value": 20},  # 恐惧
    "macro": {"dxy_index": 103.0},
}

# 测试Conviction Score = 51.3
conviction_score = 51.3
current_position = 0.05

portfolio_state = {
    "consecutive_bullish_count": 0,
    "last_conviction_score": 50.0,
    "consecutive_signal_threshold": 30,
    "acceleration_multiplier_min": 1.1,
    "acceleration_multiplier_max": 2.0,
}

signal_result = signal_generator.generate_signal(
    conviction_score=conviction_score,
    market_data=market_data,
    current_position=current_position,
    portfolio_state=portfolio_state,
)

print(f"📊 测试结果 (Conviction Score = {conviction_score}):")
print(f"   信号: {signal_result.signal.value}")
print(f"   信号强度: {signal_result.signal_strength:.4f}")
print(f"   仓位大小: {signal_result.position_size:.6f} ({signal_result.position_size * 100:.4f}%)")
print(f"   风险等级: {signal_result.risk_level.value}")
print(f"   应该执行: {signal_result.should_execute}")
print()

if signal_result.should_execute:
    print("✅ 修复成功！现在会执行买入")
else:
    print("❌ 修复失败！still should_execute = False")
    print(f"   原因: {signal_result.reasons}")

print()
print("=" * 100)
