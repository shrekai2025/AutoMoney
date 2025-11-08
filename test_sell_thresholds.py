"""
测试脚本：验证不同 conviction_score 下的减仓逻辑
"""

import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.decision.signal_generator import signal_generator, TradeSignal

def test_different_scores():
    """测试不同信念分数下的减仓逻辑"""

    # 模拟市场数据
    market_data = {
        "btc_price": 70000,
        "btc_price_change_24h": 2.5,
        "fear_greed": {"value": 50},
        "dxy": 105,
        "volatility_30d": 45,
    }

    # 测试不同的信念分数
    test_scores = [5, 10, 15, 19, 20, 24, 30, 39, 40, 50, 60, 70, 80]

    # 固定持仓为 50% (确保有持仓可以卖出)
    current_position = 0.5

    print("=" * 100)
    print("测试不同 conviction_score 下的信号生成逻辑 (持仓 = 50%)")
    print("=" * 100)
    print()

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

        execute_status = "✓ 执行" if result.should_execute else "✗ 不执行"

        print(f"Score: {score:3.0f} | {signal_emoji} {result.signal.value:4s} | "
              f"仓位: {result.position_size * 100:6.2f}% | "
              f"{execute_status:6s} | {result.reasons[0] if result.reasons else ''}")

    print()
    print("=" * 100)
    print("阈值说明:")
    print("  - conviction_score < 20: 防御性减仓 (卖出 1%)")
    print("  - 20 <= conviction_score < 40: 完全清仓 (卖出 100%)")
    print("  - 40 <= conviction_score < 70: 持币观望")
    print("  - conviction_score >= 70: 买入")
    print("=" * 100)

if __name__ == "__main__":
    test_different_scores()
