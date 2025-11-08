"""
测试脚本：验证 conviction_score = 24 时的信号生成逻辑
"""

import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.decision.signal_generator import signal_generator, TradeSignal

def test_signal_with_conviction_24():
    """测试 conviction_score = 24 的情况"""

    # 模拟市场数据
    market_data = {
        "btc_price": 70000,
        "btc_price_change_24h": 2.5,
        "fear_greed": {"value": 50},
        "dxy": 105,
        "volatility_30d": 45,
    }

    # 测试不同的持仓情况
    test_cases = [
        {"current_position": 0.0, "description": "空仓"},
        {"current_position": 0.005, "description": "极少持仓 (0.5%)"},
        {"current_position": 0.5, "description": "半仓 (50%)"},
        {"current_position": 1.0, "description": "满仓 (100%)"},
    ]

    print("=" * 80)
    print("测试 conviction_score = 24 时的信号生成逻辑")
    print("=" * 80)
    print()

    for case in test_cases:
        current_position = case["current_position"]
        description = case["description"]

        print(f"\n📊 测试场景: {description} (current_position = {current_position})")
        print("-" * 80)

        # 生成信号
        result = signal_generator.generate_signal(
            conviction_score=24.0,
            market_data=market_data,
            current_position=current_position,
            portfolio_state={}
        )

        print(f"  信念分数: 24.0")
        print(f"  信号类型: {result.signal.value}")
        print(f"  信号强度: {result.signal_strength:.4f}")
        print(f"  仓位大小: {result.position_size:.4f} ({result.position_size * 100:.2f}%)")
        print(f"  是否执行: {result.should_execute}")
        print(f"  风险等级: {result.risk_level.value}")
        print(f"  原因:")
        for reason in result.reasons:
            print(f"    - {reason}")
        if result.warnings:
            print(f"  警告:")
            for warning in result.warnings:
                print(f"    - {warning}")

        # 关键判断
        if result.signal == TradeSignal.SELL:
            if result.should_execute:
                if result.position_size == 0.01:
                    print(f"\n  ✅ 结果: 触发【防御性减仓】- 将卖出 1% BTC")
                elif result.position_size == 1.0:
                    print(f"\n  ✅ 结果: 触发【完全清仓】- 将卖出 100% BTC")
                else:
                    print(f"\n  ⚠️  结果: 触发【卖出】- 将卖出 {result.position_size * 100:.2f}% BTC")
            else:
                print(f"\n  ⏸️  结果: 信号为SELL但【不执行】(should_execute=False)")
                print(f"      可能原因: 当前持仓 {current_position * 100:.2f}% < 1%，几乎没有持仓可卖")
        elif result.signal == TradeSignal.HOLD:
            print(f"\n  ⚪ 结果: 【持币观望】")
        else:
            print(f"\n  📈 结果: 【买入信号】")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_signal_with_conviction_24()
