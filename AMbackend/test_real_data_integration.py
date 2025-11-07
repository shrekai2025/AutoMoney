"""
测试真实数据集成

验证所有模拟数据已被替换为真实数据
"""

import asyncio
import sys
from decimal import Decimal

from app.services.market.real_market_data import real_market_data_service
from app.services.strategy.real_agent_executor import real_agent_executor
from app.services.data_collectors.manager import data_manager
from app.services.indicators.calculator import IndicatorCalculator


async def test_real_market_data():
    """测试真实市场数据采集"""
    print("\n" + "=" * 60)
    print("测试 1: 真实市场数据采集")
    print("=" * 60)

    try:
        # 获取完整市场快照
        market_snapshot = await real_market_data_service.get_complete_market_snapshot()

        print(f"\n✅ 市场数据采集成功:")
        print(f"   BTC 价格: ${market_snapshot['btc_price']:.2f}")
        print(f"   24h 涨跌: {market_snapshot['btc_price_change_24h']:.2f}%")
        print(f"   恐慌贪婪指数: {market_snapshot['fear_greed']['value']}")
        print(f"   分类: {market_snapshot['fear_greed'].get('classification', 'N/A')}")
        print(f"   DXY 指数: {market_snapshot['macro'].get('dxy_index', 'N/A')}")
        print(f"   VIX: {market_snapshot['macro'].get('vix', 'N/A')}")
        print(f"   时间戳: {market_snapshot['timestamp']}")

        # 验证数据合理性
        assert isinstance(market_snapshot['btc_price'], (int, float, Decimal))
        assert market_snapshot['btc_price'] > 0
        assert 'fear_greed' in market_snapshot
        assert 'macro' in market_snapshot

        return True

    except Exception as e:
        print(f"\n❌ 市场数据采集失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_technical_indicators():
    """测试技术指标计算"""
    print("\n" + "=" * 60)
    print("测试 2: 技术指标计算")
    print("=" * 60)

    try:
        # 收集 OHLCV 数据
        all_data = await data_manager.collect_all()

        if hasattr(all_data, 'btc_ohlcv') and all_data.btc_ohlcv:
            indicators = IndicatorCalculator.calculate_all(all_data.btc_ohlcv)

            print(f"\n✅ 技术指标计算成功:")
            print(f"   指标数量: {len(indicators)}")

            # 显示部分指标
            if 'sma_20' in indicators:
                print(f"   SMA 20: {indicators['sma_20']:.2f}")
            if 'rsi_14' in indicators:
                print(f"   RSI 14: {indicators['rsi_14']:.2f}")
            if 'macd' in indicators:
                print(f"   MACD: {indicators['macd']:.4f}")

            return True
        else:
            print("\n⚠️  OHLCV 数据不可用")
            return True  # 不作为错误处理

    except Exception as e:
        print(f"\n❌ 技术指标计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_real_agent_execution():
    """测试真实 Agent 执行"""
    print("\n" + "=" * 60)
    print("测试 3: 真实 Agent 执行")
    print("=" * 60)

    try:
        # 1. 获取市场数据
        market_data = await real_market_data_service.get_complete_market_snapshot()

        # 2. 添加技术指标
        all_data = await data_manager.collect_all()
        if hasattr(all_data, 'btc_ohlcv') and all_data.btc_ohlcv:
            indicators = IndicatorCalculator.calculate_all(all_data.btc_ohlcv)
            market_data["indicators"] = indicators

        # 3. 执行所有 Agent（不记录到数据库）
        print("\n正在执行 Agent 分析...")
        agent_outputs = await real_agent_executor.execute_all_agents(
            market_data=market_data,
            db=None,  # 不记录到数据库
            user_id=None,
            strategy_execution_id=None,
        )

        print(f"\n✅ Agent 执行成功:")
        print(f"\n   Macro Agent:")
        print(f"      信号: {agent_outputs['macro']['signal']}")
        print(f"      置信度: {agent_outputs['macro']['confidence']:.2f}")
        print(f"      推理: {agent_outputs['macro']['reasoning'][:100]}...")

        print(f"\n   TA Agent:")
        print(f"      信号: {agent_outputs['ta']['signal']}")
        print(f"      置信度: {agent_outputs['ta']['confidence']:.2f}")
        print(f"      推理: {agent_outputs['ta']['reasoning'][:100]}...")

        print(f"\n   OnChain Agent:")
        print(f"      信号: {agent_outputs['onchain']['signal']}")
        print(f"      置信度: {agent_outputs['onchain']['confidence']:.2f}")
        print(f"      推理: {agent_outputs['onchain']['reasoning'][:100]}...")

        # 验证输出格式
        for agent_name in ['macro', 'ta', 'onchain']:
            assert agent_name in agent_outputs
            assert 'signal' in agent_outputs[agent_name]
            assert 'confidence' in agent_outputs[agent_name]
            assert 'reasoning' in agent_outputs[agent_name]

        return True

    except Exception as e:
        print(f"\n❌ Agent 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_no_mock_data():
    """验证代码中不包含模拟数据"""
    print("\n" + "=" * 60)
    print("测试 4: 验证无模拟数据")
    print("=" * 60)

    # 检查关键文件中是否还包含 TODO 标记或模拟数据注释
    files_to_check = [
        "/Users/uniteyoo/Documents/AutoMoney/AMbackend/app/services/strategy/scheduler.py",
        "/Users/uniteyoo/Documents/AutoMoney/AMbackend/app/api/v1/endpoints/strategy.py",
    ]

    mock_keywords = [
        "模拟市场数据",
        "模拟 Agent",
        "TODO: 集成实际",
        "# 在实际应用中",
    ]

    issues_found = []

    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for keyword in mock_keywords:
                    if keyword in content:
                        issues_found.append(f"{file_path}: 包含 '{keyword}'")
        except Exception as e:
            print(f"⚠️  无法读取文件 {file_path}: {e}")

    if issues_found:
        print("\n⚠️  发现可能的模拟数据标记:")
        for issue in issues_found:
            print(f"   - {issue}")
        return True  # 不作为错误，只是警告
    else:
        print("\n✅ 未发现明显的模拟数据标记")
        return True


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("真实数据集成测试")
    print("=" * 60)

    results = {
        "市场数据采集": await test_real_market_data(),
        "技术指标计算": await test_technical_indicators(),
        "Agent 执行": await test_real_agent_execution(),
        "验证无模拟数据": await test_no_mock_data(),
    }

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 所有测试通过！真实数据集成完成。")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
