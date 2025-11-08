"""
连续信号机制全面测试脚本

测试以下功能:
1. 数据库字段是否正确添加
2. SignalGenerator的连续信号逻辑
3. StrategyOrchestrator的连续信号更新
4. 完整的端到端流程
"""

import asyncio
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# 导入模型和服务
from app.models import Portfolio, User
from app.services.decision.signal_generator import SignalGenerator, TradeSignal
from app.services.decision.conviction_calculator import ConvictionCalculator, ConvictionInput
from app.core.config import settings


# 创建数据库引擎
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def test_database_fields():
    """测试1: 验证数据库字段是否正确添加"""
    print("\n" + "="*80)
    print("测试1: 验证Portfolio模型的连续信号字段")
    print("="*80)

    async with async_session() as db:
        # 查询第一个portfolio
        result = await db.execute(select(Portfolio).limit(1))
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ 未找到Portfolio记录,无法测试")
            return False

        # 检查字段是否存在
        required_fields = [
            'consecutive_bullish_count',
            'consecutive_bullish_since',
            'last_conviction_score',
            'consecutive_signal_threshold',
            'acceleration_multiplier_min',
            'acceleration_multiplier_max',
        ]

        all_exist = True
        for field in required_fields:
            if hasattr(portfolio, field):
                value = getattr(portfolio, field)
                print(f"✅ {field}: {value}")
            else:
                print(f"❌ 字段不存在: {field}")
                all_exist = False

        # 检查默认值
        if portfolio.consecutive_signal_threshold == 30:
            print("✅ consecutive_signal_threshold默认值正确 (30)")
        else:
            print(f"⚠️  consecutive_signal_threshold默认值错误: {portfolio.consecutive_signal_threshold}")

        if portfolio.acceleration_multiplier_min == 1.1:
            print("✅ acceleration_multiplier_min默认值正确 (1.1)")
        else:
            print(f"⚠️  acceleration_multiplier_min默认值错误: {portfolio.acceleration_multiplier_min}")

        if portfolio.acceleration_multiplier_max == 2.0:
            print("✅ acceleration_multiplier_max默认值正确 (2.0)")
        else:
            print(f"⚠️  acceleration_multiplier_max默认值错误: {portfolio.acceleration_multiplier_max}")

        return all_exist


async def test_signal_generator():
    """测试2: 验证SignalGenerator的连续信号逻辑"""
    print("\n" + "="*80)
    print("测试2: SignalGenerator连续信号计算")
    print("="*80)

    signal_gen = SignalGenerator()
    market_data = {
        "btc_price": 50000,
        "btc_price_change_24h": 2.5,
        "fear_greed": {"value": 55},
        "macro": {"dxy_index": 103},
    }

    test_cases = [
        # (conviction_score, consecutive_count, threshold, expected_multiplier)
        (75, 0, 30, 1.0, "未达到阈值"),
        (75, 29, 30, 1.0, "阈值前一次"),
        (75, 30, 30, 1.1, "刚达到阈值"),
        (75, 50, 30, 1.28, "连续50次"),
        (75, 130, 30, 2.0, "达到最大值"),
        (65, 50, 30, 1.0, "HOLD信号不加速"),
        (35, 50, 30, 1.0, "SELL信号不加速"),
    ]

    all_passed = True
    for conviction, count, threshold, expected_mult, description in test_cases:
        portfolio_state = {
            "consecutive_bullish_count": count,
            "consecutive_signal_threshold": threshold,
            "acceleration_multiplier_min": 1.1,
            "acceleration_multiplier_max": 2.0,
        }

        result = signal_gen.generate_signal(
            conviction_score=conviction,
            market_data=market_data,
            current_position=0.3,
            portfolio_state=portfolio_state,
        )

        # 验证乘数
        if abs(result.position_multiplier - expected_mult) < 0.01:
            print(f"✅ {description}: conviction={conviction}, count={count} → multiplier={result.position_multiplier:.2f}")
        else:
            print(f"❌ {description}: 期望multiplier={expected_mult:.2f}, 实际={result.position_multiplier:.2f}")
            all_passed = False

        # 验证加速标志
        is_accelerated_expected = (conviction >= 70 and count >= threshold)
        if result.is_accelerated == is_accelerated_expected:
            print(f"   加速标志正确: {result.is_accelerated}")
        else:
            print(f"   ❌ 加速标志错误: 期望={is_accelerated_expected}, 实际={result.is_accelerated}")
            all_passed = False

    return all_passed


async def test_threshold_adjustments():
    """测试3: 验证信号阈值调整"""
    print("\n" + "="*80)
    print("测试3: 信号阈值调整 (30→40, 新增20)")
    print("="*80)

    signal_gen = SignalGenerator()

    # 验证常量
    print(f"DEFENSIVE_SELL_THRESHOLD: {signal_gen.DEFENSIVE_SELL_THRESHOLD} (期望: 20)")
    print(f"SELL_THRESHOLD: {signal_gen.SELL_THRESHOLD} (期望: 40)")
    print(f"STRONG_HOLD_THRESHOLD: {signal_gen.STRONG_HOLD_THRESHOLD} (期望: 70)")

    threshold_correct = (
        signal_gen.DEFENSIVE_SELL_THRESHOLD == 20 and
        signal_gen.SELL_THRESHOLD == 40 and
        signal_gen.STRONG_HOLD_THRESHOLD == 70
    )

    if threshold_correct:
        print("✅ 所有阈值正确")
    else:
        print("❌ 阈值设置错误")

    # 测试不同分数的信号
    market_data = {
        "btc_price": 50000,
        "btc_price_change_24h": 2.5,
        "fear_greed": {"value": 55},
        "macro": {"dxy_index": 103},
    }

    test_scores = [
        (15, TradeSignal.SELL, "防御性减仓"),
        (25, TradeSignal.SELL, "清仓"),
        (42, TradeSignal.HOLD, "持币观望-偏空"),
        (75, TradeSignal.BUY, "强烈看多"),
    ]

    all_correct = True
    for score, expected_signal, description in test_scores:
        result = signal_gen.generate_signal(score, market_data, 0.3)
        if result.signal == expected_signal:
            print(f"✅ Score {score} → {result.signal.value} ({description})")
        else:
            print(f"❌ Score {score}: 期望{expected_signal.value}, 实际{result.signal.value}")
            all_correct = False

    return threshold_correct and all_correct


async def test_position_multiplier_calculation():
    """测试4: 验证仓位乘数计算公式"""
    print("\n" + "="*80)
    print("测试4: 仓位乘数计算公式验证")
    print("="*80)

    signal_gen = SignalGenerator()

    # 测试不同的配置
    test_configs = [
        # (threshold, min, max, count, expected)
        (30, 1.1, 2.0, 30, 1.1),      # 刚达到阈值
        (30, 1.1, 2.0, 40, 1.19),     # +10次
        (30, 1.1, 2.0, 80, 1.55),     # +50次
        (30, 1.1, 2.0, 130, 2.0),     # +100次(达到max)
        (30, 1.1, 2.0, 200, 2.0),     # 超过100次(仍为max)
        (20, 1.2, 3.0, 20, 1.2),      # 不同配置1
        (50, 1.05, 1.5, 60, 1.095),   # 不同配置2: extra=10, increment=0.0045, 1.05+(10*0.0045)=1.095
    ]

    all_passed = True
    for threshold, min_mult, max_mult, count, expected in test_configs:
        actual = signal_gen._calculate_acceleration_multiplier(
            count, threshold, min_mult, max_mult
        )

        if abs(actual - expected) < 0.01:
            print(f"✅ threshold={threshold}, count={count}: {actual:.2f} (期望: {expected:.2f})")
        else:
            print(f"❌ threshold={threshold}, count={count}: 实际{actual:.2f}, 期望{expected:.2f}")
            all_passed = False

    return all_passed


async def test_position_size_with_multiplier():
    """测试5: 验证仓位计算应用乘数"""
    print("\n" + "="*80)
    print("测试5: 仓位计算应用乘数")
    print("="*80)

    signal_gen = SignalGenerator()
    market_data = {
        "btc_price": 50000,
        "btc_price_change_24h": 2.5,
        "fear_greed": {"value": 55},
        "macro": {"dxy_index": 103},
    }

    # 测试: 基础仓位 * 乘数
    portfolio_state_no_accel = {
        "consecutive_bullish_count": 0,
        "consecutive_signal_threshold": 30,
        "acceleration_multiplier_min": 1.1,
        "acceleration_multiplier_max": 2.0,
    }

    portfolio_state_with_accel = {
        "consecutive_bullish_count": 50,  # 触发加速
        "consecutive_signal_threshold": 30,
        "acceleration_multiplier_min": 1.1,
        "acceleration_multiplier_max": 2.0,
    }

    result_no_accel = signal_gen.generate_signal(
        conviction_score=75,
        market_data=market_data,
        current_position=0.2,
        portfolio_state=portfolio_state_no_accel,
    )

    result_with_accel = signal_gen.generate_signal(
        conviction_score=75,
        market_data=market_data,
        current_position=0.2,
        portfolio_state=portfolio_state_with_accel,
    )

    print(f"无加速 (count=0): position_size={result_no_accel.position_size:.4f}, multiplier={result_no_accel.position_multiplier:.2f}")
    print(f"有加速 (count=50): position_size={result_with_accel.position_size:.4f}, multiplier={result_with_accel.position_multiplier:.2f}")

    # 验证加速后的仓位更大
    expected_multiplier = 1.28  # count=50时的乘数
    ratio = result_with_accel.position_size / result_no_accel.position_size

    if abs(ratio - expected_multiplier) < 0.1:
        print(f"✅ 仓位乘数应用正确: 比例={ratio:.2f}, 期望约={expected_multiplier:.2f}")
        return True
    else:
        print(f"❌ 仓位乘数应用错误: 比例={ratio:.2f}, 期望约={expected_multiplier:.2f}")
        return False


async def test_defensive_sell():
    """测试6: 验证防御性减仓(20阈值)"""
    print("\n" + "="*80)
    print("测试6: 防御性减仓机制")
    print("="*80)

    signal_gen = SignalGenerator()
    market_data = {
        "btc_price": 50000,
        "btc_price_change_24h": 2.5,
        "fear_greed": {"value": 55},
        "macro": {"dxy_index": 103},
    }

    # 测试防御性减仓 (score < 20)
    result_defensive = signal_gen.generate_signal(15, market_data, 0.8)

    # 测试普通清仓 (20 <= score < 40)
    result_normal_sell = signal_gen.generate_signal(25, market_data, 0.8)

    print(f"Score 15: signal={result_defensive.signal.value}, position_size={result_defensive.position_size:.3f}")
    print(f"Score 25: signal={result_normal_sell.signal.value}, position_size={result_normal_sell.position_size:.3f}")

    defensive_correct = (
        result_defensive.signal == TradeSignal.SELL and
        abs(result_defensive.position_size - 0.01) < 0.001  # 1%
    )

    normal_correct = (
        result_normal_sell.signal == TradeSignal.SELL and
        abs(result_normal_sell.position_size - 1.0) < 0.001  # 100%
    )

    if defensive_correct:
        print("✅ 防御性减仓正确: 卖出1%")
    else:
        print(f"❌ 防御性减仓错误: position_size={result_defensive.position_size}")

    if normal_correct:
        print("✅ 普通清仓正确: 卖出100%")
    else:
        print(f"❌ 普通清仓错误: position_size={result_normal_sell.position_size}")

    return defensive_correct and normal_correct


async def test_counter_update_logic():
    """测试7: 验证计数器更新逻辑"""
    print("\n" + "="*80)
    print("测试7: 连续信号计数器更新逻辑")
    print("="*80)

    async with async_session() as db:
        # 获取或创建测试portfolio
        result = await db.execute(select(Portfolio).limit(1))
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ 未找到Portfolio记录")
            return False

        # 导入StrategyOrchestrator
        from app.services.strategy.strategy_orchestrator import StrategyOrchestrator
        orchestrator = StrategyOrchestrator()

        # 保存初始状态
        initial_count = portfolio.consecutive_bullish_count or 0
        print(f"初始连续计数: {initial_count}")

        # 测试1: BUY信号应该增加计数器
        await orchestrator._update_consecutive_signals(
            portfolio=portfolio,
            conviction_score=75.0,
            signal=TradeSignal.BUY,
        )

        count_after_buy = portfolio.consecutive_bullish_count
        print(f"BUY信号后: {count_after_buy} (期望: {initial_count + 1})")

        buy_correct = (count_after_buy == initial_count + 1)

        # 测试2: HOLD信号应该重置计数器
        await orchestrator._update_consecutive_signals(
            portfolio=portfolio,
            conviction_score=55.0,
            signal=TradeSignal.HOLD,
        )

        count_after_hold = portfolio.consecutive_bullish_count
        print(f"HOLD信号后: {count_after_hold} (期望: 0)")

        hold_correct = (count_after_hold == 0)

        # 测试3: 连续多次BUY
        for i in range(5):
            await orchestrator._update_consecutive_signals(
                portfolio=portfolio,
                conviction_score=75.0,
                signal=TradeSignal.BUY,
            )

        count_after_5_buys = portfolio.consecutive_bullish_count
        print(f"5次BUY信号后: {count_after_5_buys} (期望: 5)")

        multiple_correct = (count_after_5_buys == 5)

        # 测试4: SELL信号应该重置
        await orchestrator._update_consecutive_signals(
            portfolio=portfolio,
            conviction_score=25.0,
            signal=TradeSignal.SELL,
        )

        count_after_sell = portfolio.consecutive_bullish_count
        print(f"SELL信号后: {count_after_sell} (期望: 0)")

        sell_correct = (count_after_sell == 0)

        # 恢复初始状态
        portfolio.consecutive_bullish_count = initial_count

        all_correct = buy_correct and hold_correct and multiple_correct and sell_correct

        if all_correct:
            print("✅ 所有计数器更新逻辑正确")
        else:
            print("❌ 部分计数器更新逻辑错误")

        return all_correct


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("连续信号机制全面测试")
    print("="*80)

    results = {}

    try:
        results['数据库字段'] = await test_database_fields()
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
        results['数据库字段'] = False

    try:
        results['SignalGenerator逻辑'] = await test_signal_generator()
    except Exception as e:
        print(f"❌ 测试2失败: {e}")
        results['SignalGenerator逻辑'] = False

    try:
        results['信号阈值'] = await test_threshold_adjustments()
    except Exception as e:
        print(f"❌ 测试3失败: {e}")
        results['信号阈值'] = False

    try:
        results['乘数计算'] = await test_position_multiplier_calculation()
    except Exception as e:
        print(f"❌ 测试4失败: {e}")
        results['乘数计算'] = False

    try:
        results['仓位应用'] = await test_position_size_with_multiplier()
    except Exception as e:
        print(f"❌ 测试5失败: {e}")
        results['仓位应用'] = False

    try:
        results['防御性减仓'] = await test_defensive_sell()
    except Exception as e:
        print(f"❌ 测试6失败: {e}")
        results['防御性减仓'] = False

    try:
        results['计数器更新'] = await test_counter_update_logic()
    except Exception as e:
        print(f"❌ 测试7失败: {e}")
        results['计数器更新'] = False

    # 汇总结果
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(results.values())
    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过! 连续信号机制工作正常!")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败,需要修复")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
