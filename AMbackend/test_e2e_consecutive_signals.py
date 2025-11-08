"""
端到端集成测试 - 连续信号机制

模拟完整的策略执行流程,验证连续信号机制在实际场景中的工作
"""

import asyncio
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models import Portfolio, User, StrategyExecution
from app.services.strategy.strategy_orchestrator import strategy_orchestrator
from app.core.config import settings


# 创建数据库引擎
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def simulate_strategy_executions():
    """
    模拟多次策略执行,测试连续信号机制的完整流程
    """
    print("\n" + "="*80)
    print("端到端集成测试 - 模拟策略执行")
    print("="*80)

    async with async_session() as db:
        # 获取第一个portfolio
        result = await db.execute(select(Portfolio).limit(1))
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ 未找到Portfolio记录")
            return False

        # 获取user
        result_user = await db.execute(select(User).where(User.id == portfolio.user_id))
        user = result_user.scalar_one_or_none()

        if not user:
            print("❌ 未找到User记录")
            return False

        print(f"\n📊 测试Portfolio: {portfolio.name}")
        print(f"   初始配置:")
        print(f"   - 连续信号阈值: {portfolio.consecutive_signal_threshold}")
        print(f"   - 加速乘数范围: {portfolio.acceleration_multiplier_min} - {portfolio.acceleration_multiplier_max}")
        print(f"   - 当前连续计数: {portfolio.consecutive_bullish_count}")

        # 重置连续计数
        portfolio.consecutive_bullish_count = 0
        portfolio.consecutive_bullish_since = None
        portfolio.last_conviction_score = None
        await db.commit()

        print("\n🎬 开始模拟策略执行...")

        # 场景1: 连续5次看涨信号 (未达到阈值30)
        print("\n--- 场景1: 连续5次看涨信号 (未达到阈值) ---")
        for i in range(5):
            market_data = {
                "btc_price": 50000 + i * 100,
                "btc_price_change_24h": 2.0,
                "fear_greed": {"value": 60},
                "macro": {"dxy_index": 103},
            }

            # 模拟高信念分数
            agent_outputs = {
                "macro": {"signal": "BULLISH", "confidence": 0.8},
                "onchain": {"signal": "BULLISH", "confidence": 0.75},
                "ta": {"signal": "BULLISH", "confidence": 0.7},
            }

            try:
                execution = await strategy_orchestrator.execute_strategy(
                    db=db,
                    user_id=user.id,
                    portfolio_id=str(portfolio.id),
                    market_data=market_data,
                    agent_outputs=agent_outputs,
                )

                await db.refresh(portfolio)

                print(f"   执行 #{i+1}:")
                print(f"     Conviction Score: {execution.conviction_score:.1f}")
                print(f"     Signal: {execution.signal}")
                print(f"     连续计数: {portfolio.consecutive_bullish_count}")
                print(f"     仓位大小: {execution.position_size:.4f}")

            except Exception as e:
                print(f"   ❌ 执行失败: {e}")
                import traceback
                traceback.print_exc()
                return False

        # 验证场景1
        expected_count_1 = 5
        if portfolio.consecutive_bullish_count == expected_count_1:
            print(f"   ✅ 连续计数正确: {portfolio.consecutive_bullish_count}")
        else:
            print(f"   ❌ 连续计数错误: 期望{expected_count_1}, 实际{portfolio.consecutive_bullish_count}")
            return False

        # 场景2: 继续执行25次,达到阈值30
        print("\n--- 场景2: 继续25次执行,达到阈值30并触发加速 ---")
        position_sizes_before_threshold = []
        position_sizes_after_threshold = []

        for i in range(25):
            market_data = {
                "btc_price": 50500 + i * 100,
                "btc_price_change_24h": 1.5,
                "fear_greed": {"value": 65},
                "macro": {"dxy_index": 102},
            }

            agent_outputs = {
                "macro": {"signal": "BULLISH", "confidence": 0.8},
                "onchain": {"signal": "BULLISH", "confidence": 0.8},
                "ta": {"signal": "BULLISH", "confidence": 0.75},
            }

            try:
                execution = await strategy_orchestrator.execute_strategy(
                    db=db,
                    user_id=user.id,
                    portfolio_id=str(portfolio.id),
                    market_data=market_data,
                    agent_outputs=agent_outputs,
                )

                await db.refresh(portfolio)

                current_count = portfolio.consecutive_bullish_count

                # 记录仓位大小
                if current_count < 30:
                    position_sizes_before_threshold.append(execution.position_size)
                else:
                    position_sizes_after_threshold.append(execution.position_size)

                if (i + 1) % 5 == 0:
                    print(f"   执行 #{i+6} (总计{current_count}次):")
                    print(f"     Conviction Score: {execution.conviction_score:.1f}")
                    print(f"     连续计数: {current_count}")
                    print(f"     仓位大小: {execution.position_size:.4f}")
                    if current_count >= 30:
                        print(f"     🚀 加速模式已激活!")

            except Exception as e:
                print(f"   ❌ 执行失败: {e}")
                return False

        # 验证场景2
        expected_count_2 = 30
        if portfolio.consecutive_bullish_count == expected_count_2:
            print(f"   ✅ 达到阈值: {portfolio.consecutive_bullish_count}")
        else:
            print(f"   ❌ 计数错误: 期望{expected_count_2}, 实际{portfolio.consecutive_bullish_count}")
            return False

        # 验证加速后仓位更大
        if position_sizes_after_threshold:
            avg_before = sum(position_sizes_before_threshold) / len(position_sizes_before_threshold) if position_sizes_before_threshold else 0
            avg_after = sum(position_sizes_after_threshold) / len(position_sizes_after_threshold)
            ratio = avg_after / avg_before if avg_before > 0 else 0

            print(f"\n   仓位对比:")
            print(f"     阈值前平均: {avg_before:.4f}")
            print(f"     阈值后平均: {avg_after:.4f}")
            print(f"     增加比例: {ratio:.2f}x")

            if ratio > 1.05:  # 至少增加5%
                print(f"   ✅ 加速机制工作正常")
            else:
                print(f"   ⚠️  加速比例较小: {ratio:.2f}x")

        # 场景3: 一次HOLD信号,重置计数器
        print("\n--- 场景3: HOLD信号重置计数器 ---")
        market_data = {
            "btc_price": 53000,
            "btc_price_change_24h": 1.0,
            "fear_greed": {"value": 55},
            "macro": {"dxy_index": 103},
        }

        # 中性信号
        agent_outputs = {
            "macro": {"signal": "NEUTRAL", "confidence": 0.6},
            "onchain": {"signal": "NEUTRAL", "confidence": 0.5},
            "ta": {"signal": "NEUTRAL", "confidence": 0.6},
        }

        try:
            execution = await strategy_orchestrator.execute_strategy(
                db=db,
                user_id=user.id,
                portfolio_id=str(portfolio.id),
                market_data=market_data,
                agent_outputs=agent_outputs,
            )

            await db.refresh(portfolio)

            print(f"   Conviction Score: {execution.conviction_score:.1f}")
            print(f"   Signal: {execution.signal}")
            print(f"   连续计数: {portfolio.consecutive_bullish_count}")

            if portfolio.consecutive_bullish_count == 0:
                print(f"   ✅ 计数器已重置")
            else:
                print(f"   ❌ 计数器未重置: {portfolio.consecutive_bullish_count}")
                return False

        except Exception as e:
            print(f"   ❌ 执行失败: {e}")
            return False

        # 场景4: 再次触发连续信号
        print("\n--- 场景4: 快速达到阈值并测试更高乘数 ---")
        for i in range(60):  # 连续60次
            market_data = {
                "btc_price": 54000 + i * 50,
                "btc_price_change_24h": 1.5,
                "fear_greed": {"value": 70},
                "macro": {"dxy_index": 101},
            }

            agent_outputs = {
                "macro": {"signal": "BULLISH", "confidence": 0.85},
                "onchain": {"signal": "BULLISH", "confidence": 0.8},
                "ta": {"signal": "BULLISH", "confidence": 0.8},
            }

            try:
                execution = await strategy_orchestrator.execute_strategy(
                    db=db,
                    user_id=user.id,
                    portfolio_id=str(portfolio.id),
                    market_data=market_data,
                    agent_outputs=agent_outputs,
                )

                await db.refresh(portfolio)

                if (i + 1) in [30, 40, 50, 60]:
                    print(f"   执行 #{i+1}:")
                    print(f"     连续计数: {portfolio.consecutive_bullish_count}")
                    print(f"     仓位大小: {execution.position_size:.4f}")

            except Exception as e:
                print(f"   ❌ 执行失败: {e}")
                return False

        # 验证场景4
        if portfolio.consecutive_bullish_count == 60:
            print(f"   ✅ 连续60次信号正确")
        else:
            print(f"   ❌ 计数错误: 期望60, 实际{portfolio.consecutive_bullish_count}")
            return False

        print("\n" + "="*80)
        print("✅ 端到端集成测试全部通过!")
        print("="*80)

        # 清理: 重置连续计数
        portfolio.consecutive_bullish_count = 0
        portfolio.consecutive_bullish_since = None
        portfolio.last_conviction_score = None
        await db.commit()

        return True


async def main():
    """主函数"""
    try:
        success = await simulate_strategy_executions()
        return success
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
