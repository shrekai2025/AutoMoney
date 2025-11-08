"""
测试脚本：验证新的下单阈值逻辑
新逻辑：
- >= 50: 买入
- 45-50: 部分减仓（动态，45时卖50%，50时卖0%）
- < 45: 全部清仓（卖100%）
"""

import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.decision.signal_generator import signal_generator, TradeSignal

def test_new_thresholds():
    """测试新的阈值逻辑"""

    # 模拟市场数据
    market_data = {
        "btc_price": 70000,
        "btc_price_change_24h": 2.5,
        "fear_greed": {"value": 50},
        "dxy": 105,
        "volatility_30d": 45,
    }

    # 测试不同的信念分数
    test_scores = [
        10, 20, 30, 40, 44, 45,      # 全部清仓区域
        46, 47, 48, 49, 49.5, 50,    # 部分减仓区域
        51, 55, 60, 70, 80, 90, 100  # 买入区域
    ]

    # 固定持仓为 50% (确保有持仓可以卖出)
    current_position = 0.5

    print("=" * 120)
    print("新下单阈值逻辑测试")
    print("=" * 120)
    print()
    print("📋 新逻辑说明:")
    print("  - conviction_score >= 50: 买入")
    print("  - 45 <= conviction_score < 50: 部分减仓（45时卖50%，线性递减到50时卖0%）")
    print("  - conviction_score < 45: 全部清仓（卖100%）")
    print()
    print("=" * 120)
    print(f"{'Score':>6} | {'信号':>6} | {'仓位大小':>10} | {'执行':>6} | {'说明'}")
    print("-" * 120)

    for score in test_scores:
        result = signal_generator.generate_signal(
            conviction_score=float(score),
            market_data=market_data,
            current_position=current_position,
            portfolio_state={}
        )

        # 格式化输出
        signal_emoji = {
            "SELL": "🔴",
            "HOLD": "⚪",
            "BUY": "✅"
        }.get(result.signal.value, "❓")

        execute_status = "✓ 是" if result.should_execute else "✗ 否"

        position_pct = result.position_size * 100

        # 根据分数范围添加说明
        if score >= 50:
            zone = "买入区"
        elif score >= 45:
            zone = "部分减仓区"
        else:
            zone = "全部清仓区"

        print(f"{score:>6.1f} | {signal_emoji} {result.signal.value:>4s} | {position_pct:>9.2f}% | {execute_status:>6s} | {zone} - {result.reasons[0] if result.reasons else ''}")

    print("=" * 120)
    print()
    print("✅ 测试完成")
    print()
    print("📊 关键测试点验证:")
    print()

    # 验证关键点
    key_tests = [
        (44, "< 45", "应该全部清仓(100%)"),
        (45, "= 45", "应该部分减仓(50%)"),
        (47.5, "= 47.5", "应该部分减仓(25%)"),
        (49.9, "≈ 50", "应该部分减仓(接近0%)"),
        (50, "= 50", "应该买入"),
        (70, "= 70", "应该买入"),
    ]

    for score, desc, expected in key_tests:
        result = signal_generator.generate_signal(
            conviction_score=float(score),
            market_data=market_data,
            current_position=current_position,
            portfolio_state={}
        )

        signal_emoji = "✅" if result.signal == TradeSignal.BUY else "🔴" if result.signal == TradeSignal.SELL else "⚪"
        position_pct = result.position_size * 100

        print(f"  Score {desc:>8}: {signal_emoji} {result.signal.value:>4s}, 仓位 {position_pct:6.2f}% - {expected}")

    print()
    print("=" * 120)

if __name__ == "__main__":
    test_new_thresholds()
