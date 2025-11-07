"""Test ConvictionCalculator and SignalGenerator

测试信念分数计算器和交易信号生成器
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.decision.conviction_calculator import (
    ConvictionCalculator,
    ConvictionInput,
)
from app.services.decision.signal_generator import (
    SignalGenerator,
    TradeSignal,
    RiskLevel,
)


def test_conviction_calculator_bullish():
    """测试看多场景"""
    print("=" * 80)
    print("🧪 Test 1: ConvictionCalculator - 看多场景")
    print("=" * 80)

    calculator = ConvictionCalculator()

    input_data = ConvictionInput(
        macro_output={"signal": "BULLISH", "confidence": 0.8},
        ta_output={"signal": "BULLISH", "confidence": 0.7},
        onchain_output={"signal": "BULLISH", "confidence": 0.75},
        market_data={
            "fear_greed": {"value": 60},
            "btc_price_change_24h": 3.5,
            "macro": {"dxy_index": 102},
        }
    )

    result = calculator.calculate(input_data)

    print(f"\n📊 输入:")
    print(f"  Macro: BULLISH (confidence: 0.8)")
    print(f"  TA: BULLISH (confidence: 0.7)")
    print(f"  OnChain: BULLISH (confidence: 0.75)")
    print(f"  Fear & Greed: 60")
    print(f"  BTC 24h变化: +3.5%")

    print(f"\n📈 结果:")
    print(f"  最终信念分数: {result.score:.2f}/100")
    print(f"  原始加权分数: {result.raw_weighted_score:.2f}")
    print(f"  Macro贡献: {result.macro_contribution:.2f}")
    print(f"  TA贡献: {result.ta_contribution:.2f}")
    print(f"  OnChain贡献: {result.onchain_contribution:.2f}")
    print(f"  风险调整因子: {result.risk_adjustment:.2f}")
    print(f"  置信度调整因子: {result.confidence_adjustment:.2f}")

    # 所有Agent看多 + 中等风险 -> 高信念分数
    assert result.score > 70, f"❌ 期望信念分数 > 70, 实际: {result.score:.2f}"
    assert result.score <= 100, f"❌ 信念分数应 <= 100, 实际: {result.score:.2f}"

    print(f"\n✅ 断言通过: 信念分数在合理范围 (70-100)")
    print()


def test_conviction_calculator_bearish():
    """测试看空场景"""
    print("=" * 80)
    print("🧪 Test 2: ConvictionCalculator - 看空场景")
    print("=" * 80)

    calculator = ConvictionCalculator()

    input_data = ConvictionInput(
        macro_output={"signal": "BEARISH", "confidence": 0.75},
        ta_output={"signal": "BEARISH", "confidence": 0.8},
        onchain_output={"signal": "BEARISH", "confidence": 0.7},
        market_data={
            "fear_greed": {"value": 25},  # 恐惧
            "btc_price_change_24h": -8.0,  # 大跌
            "macro": {"dxy_index": 112},  # 美元强
        }
    )

    result = calculator.calculate(input_data)

    print(f"\n📊 输入:")
    print(f"  Macro: BEARISH (confidence: 0.75)")
    print(f"  TA: BEARISH (confidence: 0.8)")
    print(f"  OnChain: BEARISH (confidence: 0.7)")
    print(f"  Fear & Greed: 25 (恐惧)")
    print(f"  BTC 24h变化: -8.0%")
    print(f"  DXY: 112 (美元强)")

    print(f"\n📉 结果:")
    print(f"  最终信念分数: {result.score:.2f}/100")
    print(f"  风险调整因子: {result.risk_adjustment:.2f}")

    # 所有Agent看空 + 高风险 -> 低信念分数
    assert result.score < 30, f"❌ 期望信念分数 < 30, 实际: {result.score:.2f}"
    assert result.score >= 0, f"❌ 信念分数应 >= 0, 实际: {result.score:.2f}"

    print(f"\n✅ 断言通过: 信念分数在合理范围 (0-30)")
    print()


def test_signal_generator_strong_buy():
    """测试强烈买入信号"""
    print("=" * 80)
    print("🧪 Test 3: SignalGenerator - 强烈买入信号")
    print("=" * 80)

    generator = SignalGenerator()

    result = generator.generate_signal(
        conviction_score=85.0,
        market_data={
            "fear_greed": {"value": 55},
            "btc_price_change_24h": 2.5,
            "macro": {"dxy_index": 103},
        },
        current_position=0.0,
    )

    print(f"\n📊 输入:")
    print(f"  信念分数: 85.0/100")
    print(f"  当前仓位: 0%")
    print(f"  Fear & Greed: 55")
    print(f"  BTC 24h变化: +2.5%")

    print(f"\n📈 结果:")
    print(f"  交易信号: {result.signal}")
    print(f"  信号强度: {result.signal_strength:.2f}")
    print(f"  建议仓位: {result.position_size*100:.2f}%")
    print(f"  风险等级: {result.risk_level}")
    print(f"  应该执行: {result.should_execute}")
    print(f"  决策原因: {result.reasons}")
    print(f"  风险警告: {result.warnings if result.warnings else '无'}")

    assert result.signal == TradeSignal.BUY, f"❌ 期望信号BUY, 实际: {result.signal}"
    assert result.should_execute == True, "❌ 应该执行交易"
    assert result.position_size > 0, "❌ 仓位大小应 > 0"

    print(f"\n✅ 断言通过: 生成正确的买入信号")
    print()


def test_signal_generator_circuit_breaker():
    """测试熔断机制"""
    print("=" * 80)
    print("🧪 Test 4: SignalGenerator - 熔断机制")
    print("=" * 80)

    generator = SignalGenerator()

    result = generator.generate_signal(
        conviction_score=85.0,  # 高信念分数
        market_data={
            "fear_greed": {"value": 15},  # 但极度恐惧
            "btc_price_change_24h": 2.5,
            "macro": {"dxy_index": 103},
        },
        current_position=0.0,
    )

    print(f"\n📊 输入:")
    print(f"  信念分数: 85.0/100 (高)")
    print(f"  Fear & Greed: 15 (极度恐惧)")

    print(f"\n⚠️  结果:")
    print(f"  交易信号: {result.signal}")
    print(f"  应该执行: {result.should_execute}")
    print(f"  决策原因: {result.reasons}")
    print(f"  风险警告: {result.warnings}")

    # 熔断触发,应该HOLD
    assert result.signal == TradeSignal.HOLD, f"❌ 期望信号HOLD, 实际: {result.signal}"
    assert result.should_execute == False, "❌ 不应该执行交易"
    assert len(result.warnings) > 0, "❌ 应该有风险警告"

    print(f"\n✅ 断言通过: 熔断机制正常工作")
    print()


def test_signal_generator_hold():
    """测试持币观望信号"""
    print("=" * 80)
    print("🧪 Test 5: SignalGenerator - 持币观望")
    print("=" * 80)

    generator = SignalGenerator()

    result = generator.generate_signal(
        conviction_score=52.0,  # 中性
        market_data={
            "fear_greed": {"value": 50},
            "btc_price_change_24h": 1.5,
            "macro": {"dxy_index": 103},
        },
        current_position=0.3,
    )

    print(f"\n📊 输入:")
    print(f"  信念分数: 52.0/100 (中性)")
    print(f"  当前仓位: 30%")

    print(f"\n⚪ 结果:")
    print(f"  交易信号: {result.signal}")
    print(f"  应该执行: {result.should_execute}")
    print(f"  决策原因: {result.reasons}")

    assert result.signal == TradeSignal.HOLD, f"❌ 期望信号HOLD, 实际: {result.signal}"
    assert result.should_execute == False, "❌ 不应该执行交易"

    print(f"\n✅ 断言通过: 中性信号生成HOLD")
    print()


if __name__ == "__main__":
    try:
        test_conviction_calculator_bullish()
        test_conviction_calculator_bearish()
        test_signal_generator_strong_buy()
        test_signal_generator_circuit_breaker()
        test_signal_generator_hold()

        print("=" * 80)
        print("🎉 所有测试通过!")
        print("=" * 80)
        print("\n📋 测试总结:")
        print("  ✅ ConvictionCalculator 看多场景正常")
        print("  ✅ ConvictionCalculator 看空场景正常")
        print("  ✅ SignalGenerator 强烈买入信号正常")
        print("  ✅ SignalGenerator 熔断机制正常")
        print("  ✅ SignalGenerator 持币观望信号正常")
        print()

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
