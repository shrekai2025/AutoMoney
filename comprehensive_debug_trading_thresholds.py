"""全面Debug交易阈值功能"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.services.decision.signal_generator import signal_generator
from app.services.strategy.marketplace_service import marketplace_service

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def comprehensive_debug():
    """全面Debug交易阈值功能"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 120)
    print("🔍 全面Debug交易阈值功能")
    print("=" * 120)
    print()

    all_tests_passed = True

    async with AsyncSessionLocal() as db:
        # 获取Portfolio
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ Portfolio不存在")
            return

        print(f"📊 Portfolio信息: {portfolio.name} (ID: {portfolio_id})")
        print()

        # ========================================
        # 测试1: 数据库字段检查
        # ========================================
        print("=" * 120)
        print("🧪 测试1: 数据库字段完整性检查")
        print("=" * 120)
        print()

        required_fields = [
            "fg_circuit_breaker_threshold",
            "fg_position_adjust_threshold",
            "buy_threshold",
            "partial_sell_threshold",
            "full_sell_threshold"
        ]

        fields_ok = True
        for field in required_fields:
            if not hasattr(portfolio, field):
                print(f"   ❌ 缺少字段: {field}")
                fields_ok = False
            else:
                value = getattr(portfolio, field)
                print(f"   ✅ {field}: {value}")

        if fields_ok:
            print("\n✅ 测试1通过: 所有数据库字段存在")
        else:
            print("\n❌ 测试1失败: 缺少必需字段")
            all_tests_passed = False

        print()

        # ========================================
        # 测试2: 默认值验证
        # ========================================
        print("=" * 120)
        print("🧪 测试2: 默认值验证")
        print("=" * 120)
        print()

        # 恢复默认值
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=20,
            fg_position_adjust_threshold=30,
            buy_threshold=50,
            partial_sell_threshold=50,
            full_sell_threshold=45,
        )
        await db.refresh(portfolio)

        expected_defaults = {
            "fg_circuit_breaker_threshold": 20,
            "fg_position_adjust_threshold": 30,
            "buy_threshold": 50.0,
            "partial_sell_threshold": 50.0,
            "full_sell_threshold": 45.0,
        }

        defaults_ok = True
        for field, expected_value in expected_defaults.items():
            actual_value = getattr(portfolio, field)
            if actual_value == expected_value:
                print(f"   ✅ {field}: {actual_value} (期望: {expected_value})")
            else:
                print(f"   ❌ {field}: {actual_value} (期望: {expected_value})")
                defaults_ok = False

        if defaults_ok:
            print("\n✅ 测试2通过: 默认值正确")
        else:
            print("\n❌ 测试2失败: 默认值不正确")
            all_tests_passed = False

        print()

        # ========================================
        # 测试3: API更新功能
        # ========================================
        print("=" * 120)
        print("🧪 测试3: API更新功能")
        print("=" * 120)
        print()

        test_values = {
            "fg_circuit_breaker_threshold": 15,
            "fg_position_adjust_threshold": 25,
            "buy_threshold": 55,
            "partial_sell_threshold": 52,
            "full_sell_threshold": 40,
        }

        print("   更新阈值为测试值...")
        result = await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            **test_values
        )
        await db.refresh(portfolio)

        api_ok = True
        for field, expected_value in test_values.items():
            actual_value = getattr(portfolio, field)
            if actual_value == expected_value:
                print(f"   ✅ {field}: {actual_value}")
            else:
                print(f"   ❌ {field}: {actual_value} (期望: {expected_value})")
                api_ok = False

        if api_ok:
            print("\n✅ 测试3通过: API更新功能正常")
        else:
            print("\n❌ 测试3失败: API更新失败")
            all_tests_passed = False

        print()

        # ========================================
        # 测试4: 信号生成器 - 买入阈值
        # ========================================
        print("=" * 120)
        print("🧪 测试4: 信号生成器 - 买入阈值逻辑")
        print("=" * 120)
        print()

        # 恢复默认值用于测试
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            buy_threshold=50,
            partial_sell_threshold=50,
            full_sell_threshold=45,
        )
        await db.refresh(portfolio)

        market_data = {
            "btc_price_change_24h": 2.0,
            "fear_greed": {"value": 50},
            "macro": {"dxy_index": 100},
        }

        portfolio_state = {
            "consecutive_bullish_count": 0,
            "last_conviction_score": 50.0,
            "consecutive_signal_threshold": 30,
            "acceleration_multiplier_min": 1.1,
            "acceleration_multiplier_max": 2.0,
            "fg_circuit_breaker_threshold": portfolio.fg_circuit_breaker_threshold,
            "fg_position_adjust_threshold": portfolio.fg_position_adjust_threshold,
            "buy_threshold": portfolio.buy_threshold,
            "partial_sell_threshold": portfolio.partial_sell_threshold,
            "full_sell_threshold": portfolio.full_sell_threshold,
        }

        test_cases = [
            (44, "SELL", "全部清仓"),  # < 45
            (45, "SELL", "部分减仓边界"),  # = 45
            (47, "SELL", "部分减仓"),  # 45 < x < 50
            (50, "BUY", "买入边界"),  # = 50
            (55, "BUY", "买入"),  # > 50
        ]

        buy_threshold_ok = True
        for conviction, expected_signal, description in test_cases:
            result = signal_generator.generate_signal(
                conviction_score=conviction,
                market_data=market_data,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )

            if result.signal.value == expected_signal:
                print(f"   ✅ Score={conviction}: {result.signal.value} ({description})")
            else:
                print(f"   ❌ Score={conviction}: {result.signal.value} (期望: {expected_signal}, {description})")
                buy_threshold_ok = False

        if buy_threshold_ok:
            print("\n✅ 测试4通过: 买入阈值逻辑正确")
        else:
            print("\n❌ 测试4失败: 买入阈值逻辑有误")
            all_tests_passed = False

        print()

        # ========================================
        # 测试5: 自定义买入阈值
        # ========================================
        print("=" * 120)
        print("🧪 测试5: 自定义买入阈值 (buy_threshold=60)")
        print("=" * 120)
        print()

        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            buy_threshold=60,
            partial_sell_threshold=55,
            full_sell_threshold=50,
        )
        await db.refresh(portfolio)

        portfolio_state["buy_threshold"] = 60
        portfolio_state["partial_sell_threshold"] = 55
        portfolio_state["full_sell_threshold"] = 50

        custom_test_cases = [
            (49, "SELL", "全部清仓"),  # < 50
            (50, "SELL", "部分减仓边界"),  # = 50
            (52, "SELL", "部分减仓"),  # 50 < x < 55
            (55, "SELL", "部分减仓上界"),  # = 55
            (59, "SELL", "接近买入阈值"),  # 55 < x < 60
            (60, "BUY", "买入边界"),  # = 60
            (65, "BUY", "买入"),  # > 60
        ]

        custom_threshold_ok = True
        for conviction, expected_signal, description in custom_test_cases:
            result = signal_generator.generate_signal(
                conviction_score=conviction,
                market_data=market_data,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )

            if result.signal.value == expected_signal:
                print(f"   ✅ Score={conviction}: {result.signal.value} ({description})")
            else:
                print(f"   ❌ Score={conviction}: {result.signal.value} (期望: {expected_signal}, {description})")
                custom_threshold_ok = False

        if custom_threshold_ok:
            print("\n✅ 测试5通过: 自定义买入阈值正确")
        else:
            print("\n❌ 测试5失败: 自定义买入阈值有误")
            all_tests_passed = False

        print()

        # ========================================
        # 测试6: Fear & Greed 熔断机制
        # ========================================
        print("=" * 120)
        print("🧪 测试6: Fear & Greed 熔断机制")
        print("=" * 120)
        print()

        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=20,
            buy_threshold=50,
        )
        await db.refresh(portfolio)

        portfolio_state["fg_circuit_breaker_threshold"] = 20
        portfolio_state["buy_threshold"] = 50

        circuit_breaker_tests = [
            (15, 70, "HOLD", "熔断触发"),  # FG < 20
            (20, 70, "BUY", "熔断边界(不触发)"),  # FG = 20
            (25, 70, "BUY", "正常交易"),  # FG > 20
        ]

        circuit_ok = True
        for fg_value, conviction, expected_signal, description in circuit_breaker_tests:
            market_data_test = {
                "btc_price_change_24h": 2.0,
                "fear_greed": {"value": fg_value},
                "macro": {"dxy_index": 100},
            }

            result = signal_generator.generate_signal(
                conviction_score=conviction,
                market_data=market_data_test,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )

            if result.signal.value == expected_signal:
                print(f"   ✅ FG={fg_value}, Score={conviction}: {result.signal.value} ({description})")
            else:
                print(f"   ❌ FG={fg_value}, Score={conviction}: {result.signal.value} (期望: {expected_signal}, {description})")
                circuit_ok = False

        if circuit_ok:
            print("\n✅ 测试6通过: Fear & Greed熔断机制正确")
        else:
            print("\n❌ 测试6失败: Fear & Greed熔断机制有误")
            all_tests_passed = False

        print()

        # ========================================
        # 测试7: 自定义熔断阈值
        # ========================================
        print("=" * 120)
        print("🧪 测试7: 自定义熔断阈值 (fg_circuit_breaker=25)")
        print("=" * 120)
        print()

        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=25,
        )
        await db.refresh(portfolio)

        portfolio_state["fg_circuit_breaker_threshold"] = 25

        custom_circuit_tests = [
            (20, 70, "HOLD", "熔断触发"),  # FG < 25
            (25, 70, "BUY", "熔断边界(不触发)"),  # FG = 25
            (30, 70, "BUY", "正常交易"),  # FG > 25
        ]

        custom_circuit_ok = True
        for fg_value, conviction, expected_signal, description in custom_circuit_tests:
            market_data_test = {
                "btc_price_change_24h": 2.0,
                "fear_greed": {"value": fg_value},
                "macro": {"dxy_index": 100},
            }

            result = signal_generator.generate_signal(
                conviction_score=conviction,
                market_data=market_data_test,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )

            if result.signal.value == expected_signal:
                print(f"   ✅ FG={fg_value}, Score={conviction}: {result.signal.value} ({description})")
            else:
                print(f"   ❌ FG={fg_value}, Score={conviction}: {result.signal.value} (期望: {expected_signal}, {description})")
                custom_circuit_ok = False

        if custom_circuit_ok:
            print("\n✅ 测试7通过: 自定义熔断阈值正确")
        else:
            print("\n❌ 测试7失败: 自定义熔断阈值有误")
            all_tests_passed = False

        print()

        # ========================================
        # 测试8: Fear & Greed 仓位调整
        # ========================================
        print("=" * 120)
        print("🧪 测试8: Fear & Greed 仓位调整机制")
        print("=" * 120)
        print()

        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=20,
            fg_position_adjust_threshold=30,
            buy_threshold=50,
        )
        await db.refresh(portfolio)

        portfolio_state["fg_circuit_breaker_threshold"] = 20
        portfolio_state["fg_position_adjust_threshold"] = 30
        portfolio_state["buy_threshold"] = 50

        # 测试仓位调整
        market_data_high_fg = {
            "btc_price_change_24h": 2.0,
            "fear_greed": {"value": 50},  # > 30，不调整
            "macro": {"dxy_index": 100},
        }

        market_data_low_fg = {
            "btc_price_change_24h": 2.0,
            "fear_greed": {"value": 25},  # < 30，调整
            "macro": {"dxy_index": 100},
        }

        result_high_fg = signal_generator.generate_signal(
            conviction_score=51,
            market_data=market_data_high_fg,
            current_position=0.5,
            portfolio_state=portfolio_state,
        )

        result_low_fg = signal_generator.generate_signal(
            conviction_score=51,
            market_data=market_data_low_fg,
            current_position=0.5,
            portfolio_state=portfolio_state,
        )

        position_adjust_ok = True

        # 高FG应该有更大的仓位
        if result_high_fg.position_size > result_low_fg.position_size:
            print(f"   ✅ FG=50 仓位: {result_high_fg.position_size:.6f}")
            print(f"   ✅ FG=25 仓位: {result_low_fg.position_size:.6f}")
            print(f"   ✅ 仓位调整生效 (FG低时减少了 {((result_high_fg.position_size - result_low_fg.position_size) / result_high_fg.position_size * 100):.1f}%)")
        else:
            print(f"   ❌ FG=50 仓位: {result_high_fg.position_size:.6f}")
            print(f"   ❌ FG=25 仓位: {result_low_fg.position_size:.6f}")
            print(f"   ❌ 仓位调整未生效")
            position_adjust_ok = False

        # 验证最小仓位保护
        if result_low_fg.position_size >= 0.002:  # MIN_POSITION_SIZE
            print(f"   ✅ 最小仓位保护生效: {result_low_fg.position_size:.6f} >= 0.002")
        else:
            print(f"   ❌ 最小仓位保护失效: {result_low_fg.position_size:.6f} < 0.002")
            position_adjust_ok = False

        if position_adjust_ok:
            print("\n✅ 测试8通过: Fear & Greed仓位调整正确")
        else:
            print("\n❌ 测试8失败: Fear & Greed仓位调整有误")
            all_tests_passed = False

        print()

        # ========================================
        # 测试9: 边界条件测试
        # ========================================
        print("=" * 120)
        print("🧪 测试9: 边界条件测试")
        print("=" * 120)
        print()

        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=20,
            fg_position_adjust_threshold=30,
            buy_threshold=50,
            partial_sell_threshold=50,
            full_sell_threshold=45,
        )
        await db.refresh(portfolio)

        portfolio_state["fg_circuit_breaker_threshold"] = 20
        portfolio_state["fg_position_adjust_threshold"] = 30
        portfolio_state["buy_threshold"] = 50
        portfolio_state["partial_sell_threshold"] = 50
        portfolio_state["full_sell_threshold"] = 45

        boundary_tests = [
            # (conviction, expected_signal, description)
            (0, "SELL", "最小值"),
            (44.9, "SELL", "接近full_sell_threshold下界"),
            (45.0, "SELL", "full_sell_threshold边界"),
            (45.1, "SELL", "刚超过full_sell_threshold"),
            (49.9, "SELL", "接近buy_threshold下界"),
            (50.0, "BUY", "buy_threshold边界"),
            (50.1, "BUY", "刚超过buy_threshold"),
            (100, "BUY", "最大值"),
        ]

        boundary_ok = True
        for conviction, expected_signal, description in boundary_tests:
            result = signal_generator.generate_signal(
                conviction_score=conviction,
                market_data=market_data,
                current_position=0.5,
                portfolio_state=portfolio_state,
            )

            if result.signal.value == expected_signal:
                print(f"   ✅ Score={conviction}: {result.signal.value} ({description})")
            else:
                print(f"   ❌ Score={conviction}: {result.signal.value} (期望: {expected_signal}, {description})")
                boundary_ok = False

        if boundary_ok:
            print("\n✅ 测试9通过: 边界条件处理正确")
        else:
            print("\n❌ 测试9失败: 边界条件处理有误")
            all_tests_passed = False

        print()

        # ========================================
        # 测试10: 阈值逻辑关系验证
        # ========================================
        print("=" * 120)
        print("🧪 测试10: 阈值逻辑关系验证 (full_sell <= partial_sell)")
        print("=" * 120)
        print()

        # 测试正常关系: 45 <= 50
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            full_sell_threshold=45,
            partial_sell_threshold=50,
        )
        await db.refresh(portfolio)

        logic_ok = True
        if portfolio.full_sell_threshold <= portfolio.partial_sell_threshold:
            print(f"   ✅ 阈值关系正确: full_sell({portfolio.full_sell_threshold}) <= partial_sell({portfolio.partial_sell_threshold})")
        else:
            print(f"   ❌ 阈值关系错误: full_sell({portfolio.full_sell_threshold}) > partial_sell({portfolio.partial_sell_threshold})")
            logic_ok = False

        # 测试相等情况: 45 = 45
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            full_sell_threshold=45,
            partial_sell_threshold=45,
        )
        await db.refresh(portfolio)

        if portfolio.full_sell_threshold == portfolio.partial_sell_threshold:
            print(f"   ✅ 阈值可以相等: full_sell({portfolio.full_sell_threshold}) = partial_sell({portfolio.partial_sell_threshold})")
        else:
            print(f"   ❌ 阈值相等时异常")
            logic_ok = False

        if logic_ok:
            print("\n✅ 测试10通过: 阈值逻辑关系验证正确")
        else:
            print("\n❌ 测试10失败: 阈值逻辑关系验证有误")
            all_tests_passed = False

        print()

        # ========================================
        # 恢复默认值
        # ========================================
        print("🔄 恢复默认值...")
        await marketplace_service.update_strategy_settings(
            db=db,
            portfolio_id=portfolio_id,
            user_id=portfolio.user_id,
            fg_circuit_breaker_threshold=20,
            fg_position_adjust_threshold=30,
            buy_threshold=50,
            partial_sell_threshold=50,
            full_sell_threshold=45,
        )
        print("✅ 已恢复默认值")
        print()

        # ========================================
        # 总结
        # ========================================
        print("=" * 120)
        if all_tests_passed:
            print("🎉 所有测试通过！交易阈值功能完全正常！")
        else:
            print("⚠️  部分测试失败，请检查上述错误信息")
        print("=" * 120)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(comprehensive_debug())
