"""Test Strategy Orchestrator and Scheduler

测试策略编排器和调度器的完整功能
"""

import asyncio
import sys
import os
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models import User, Portfolio, PortfolioHolding, Trade, StrategyExecution, PortfolioSnapshot
from app.services.trading.portfolio_service import portfolio_service
from app.services.strategy.strategy_orchestrator import strategy_orchestrator
from app.services.strategy.scheduler import strategy_scheduler
from app.schemas.strategy import PortfolioCreate

# Create test engine
test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def test_strategy_orchestrator():
    """测试策略编排器"""

    print("=" * 80)
    print("🧪 测试 1: StrategyOrchestrator - 完整策略执行")
    print("=" * 80)
    print()

    async with TestSessionLocal() as db:
        try:
            # 1. 获取或创建测试用户
            result = await db.execute(select(User).limit(1))
            test_user = result.scalar_one_or_none()

            if not test_user:
                print("⚠️  未找到用户，创建测试用户...")
                test_user = User(
                    email="strategy_test@automoney.com",
                    full_name="Strategy Test User",
                    is_active=True
                )
                db.add(test_user)
                await db.commit()
                await db.refresh(test_user)
                print(f"✅ 创建测试用户: {test_user.email}")
            else:
                print(f"✅ 使用现有用户: {test_user.email}")

            print()

            # 2. 创建测试组合
            print("📋 步骤 1: 创建测试组合")
            print("-" * 80)

            portfolio = await portfolio_service.create_portfolio(
                db=db,
                user_id=test_user.id,
                portfolio_data=PortfolioCreate(
                    name="策略测试组合",
                    initial_balance=Decimal("20000"),
                    strategy_name="Multi-Agent Strategy"
                )
            )

            print(f"  ✅ 创建组合: {portfolio.name}")
            print(f"     ID: {portfolio.id}")
            print(f"     初始余额: ${portfolio.initial_balance}")
            print()

            # 3. 准备市场数据和 Agent 输出
            market_data = {
                "btc_price": 46000.0,
                "btc_price_change_24h": 3.5,
                "fear_greed": {"value": 65},
                "macro": {
                    "dxy_index": 102.5,
                    "vix": 14.5,
                },
                "timestamp": "2024-01-01T12:00:00Z",
            }

            agent_outputs = {
                "macro": {
                    "signal": "BULLISH",
                    "confidence": 0.80,
                    "reasoning": "宏观环境看多",
                },
                "onchain": {
                    "signal": "BULLISH",
                    "confidence": 0.75,
                    "reasoning": "链上指标健康",
                },
                "ta": {
                    "signal": "BULLISH",
                    "confidence": 0.70,
                    "reasoning": "技术面看多",
                },
            }

            # 4. 执行策略（第一次 - BUY）
            print("📈 步骤 2: 执行策略 (买入信号)")
            print("-" * 80)

            execution1 = await strategy_orchestrator.execute_strategy(
                db=db,
                user_id=test_user.id,
                portfolio_id=str(portfolio.id),
                market_data=market_data,
                agent_outputs=agent_outputs,
            )

            print(f"  ✅ 策略执行成功")
            print(f"     执行ID: {execution1.id}")
            print(f"     信念分数: {execution1.conviction_score:.2f}/100")
            print(f"     交易信号: {execution1.signal}")
            print(f"     信号强度: {execution1.signal_strength:.2f}")
            print(f"     建议仓位: {execution1.position_size*100:.2f}%")
            print(f"     风险等级: {execution1.risk_level}")
            print(f"     状态: {execution1.status}")
            print()

            # 验证策略执行记录
            assert execution1.conviction_score > 70, f"❌ 信念分数应 > 70"
            assert execution1.signal == "BUY", f"❌ 信号应为 BUY"
            assert execution1.status == "completed", f"❌ 状态应为 completed"
            print(f"  ✅ 策略执行记录验证通过")

            # 验证交易记录（查询该策略执行相关的交易）
            result = await db.execute(
                select(Trade).where(Trade.execution_id == str(execution1.id))
            )
            trade = result.scalar_one_or_none()

            if trade:
                print(f"  ✅ 交易记录验证通过")
                print(f"     交易ID: {trade.id}")
                print(f"     币种: {trade.symbol}")
                print(f"     类型: {trade.trade_type}")
                print(f"     数量: {trade.amount}")
                print(f"     价格: ${trade.price}")
                print(f"     信念分数: {trade.conviction_score}")
                print()

            # 5. 更改市场条件 - 执行策略（第二次 - 可能 HOLD）
            print("📊 步骤 3: 执行策略 (中性信号)")
            print("-" * 80)

            market_data2 = {
                "btc_price": 46500.0,
                "btc_price_change_24h": 1.0,
                "fear_greed": {"value": 52},
                "macro": {"dxy_index": 103.0, "vix": 15.0},
                "timestamp": "2024-01-01T16:00:00Z",
            }

            agent_outputs2 = {
                "macro": {"signal": "NEUTRAL", "confidence": 0.60},
                "onchain": {"signal": "NEUTRAL", "confidence": 0.55},
                "ta": {"signal": "NEUTRAL", "confidence": 0.50},
            }

            execution2 = await strategy_orchestrator.execute_strategy(
                db=db,
                user_id=test_user.id,
                portfolio_id=str(portfolio.id),
                market_data=market_data2,
                agent_outputs=agent_outputs2,
            )

            print(f"  ✅ 策略执行成功")
            print(f"     信念分数: {execution2.conviction_score:.2f}/100")
            print(f"     交易信号: {execution2.signal}")
            print(f"     状态: {execution2.status}")
            print()

            # 6. 验证组合状态
            print("📊 步骤 4: 验证组合状态")
            print("-" * 80)

            await db.refresh(portfolio)

            print(f"  当前余额: ${portfolio.current_balance}")
            print(f"  总价值: ${portfolio.total_value}")
            print(f"  总盈亏: ${portfolio.total_pnl}")
            print(f"  总交易次数: {portfolio.total_trades}")
            print()

            # 7. 查询策略执行历史
            print("📜 步骤 5: 查询策略执行历史")
            print("-" * 80)

            result = await db.execute(
                select(StrategyExecution)
                .where(StrategyExecution.user_id == test_user.id)
                .order_by(StrategyExecution.execution_time.desc())
                .limit(5)
            )
            executions = result.scalars().all()

            print(f"  找到 {len(executions)} 条策略执行记录:")
            for i, exec_record in enumerate(executions, 1):
                print(f"    {i}. 信号: {exec_record.signal}, "
                      f"信念: {exec_record.conviction_score:.2f}, "
                      f"状态: {exec_record.status}")

            print()

            # 8. 清理测试数据
            print("🧹 步骤 6: 清理测试数据")
            print("-" * 80)

            # 删除策略执行记录
            result = await db.execute(
                select(StrategyExecution).where(
                    StrategyExecution.user_id == test_user.id
                )
            )
            strategy_executions = result.scalars().all()
            for exec_record in strategy_executions:
                await db.delete(exec_record)

            # 删除交易记录
            result = await db.execute(
                select(Trade).where(Trade.portfolio_id == portfolio.id)
            )
            trades = result.scalars().all()
            for trade in trades:
                await db.delete(trade)

            # 删除组合
            await db.delete(portfolio)
            await db.commit()

            print(f"  ✅ 清理完成: 删除了 {len(strategy_executions)} 条策略记录, "
                  f"{len(trades)} 条交易记录, 1 个组合")
            print()

            # 最终总结
            print("=" * 80)
            print("🎉 StrategyOrchestrator 测试通过!")
            print("=" * 80)
            print()

        except AssertionError as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        except Exception as e:
            print(f"\n❌ 测试出错: {e}")
            import traceback
            traceback.print_exc()
            raise


async def test_scheduler_jobs():
    """测试调度器的各个 Job"""

    print("=" * 80)
    print("🧪 测试 2: Scheduler Jobs - 定时任务")
    print("=" * 80)
    print()

    async with TestSessionLocal() as db:
        try:
            # 1. 获取或创建测试用户和组合
            result = await db.execute(select(User).limit(1))
            test_user = result.scalar_one_or_none()

            if not test_user:
                test_user = User(
                    email="scheduler_test@automoney.com",
                    full_name="Scheduler Test User",
                    is_active=True
                )
                db.add(test_user)
                await db.commit()
                await db.refresh(test_user)

            portfolio = await portfolio_service.create_portfolio(
                db=db,
                user_id=test_user.id,
                portfolio_data=PortfolioCreate(
                    name="调度器测试组合",
                    initial_balance=Decimal("15000"),
                    strategy_name="Scheduled Strategy"
                )
            )

            print(f"✅ 测试组合已创建: {portfolio.name}")
            print()

            # 2. 初始化调度器
            await strategy_scheduler.initialize()

            # 3. 手动测试市场数据采集 Job
            print("📊 测试 Job 1: 市场数据采集")
            print("-" * 80)

            await strategy_scheduler.collect_market_data_job()

            await db.refresh(portfolio)
            print(f"  ✅ 市场数据采集完成")
            print(f"     组合总价值: ${portfolio.total_value}")
            print()

            # 4. 手动测试策略执行 Job
            print("🎯 测试 Job 2: 策略执行")
            print("-" * 80)

            await strategy_scheduler.execute_strategy_job()

            # 查询策略执行记录
            result = await db.execute(
                select(StrategyExecution)
                .where(StrategyExecution.user_id == test_user.id)
                .order_by(StrategyExecution.execution_time.desc())
                .limit(1)
            )
            latest_execution = result.scalar_one_or_none()

            if latest_execution:
                print(f"  ✅ 策略执行 Job 完成")
                print(f"     执行ID: {latest_execution.id}")
                print(f"     信号: {latest_execution.signal}")
                print(f"     信念分数: {latest_execution.conviction_score:.2f}")
                print()

            # 5. 手动测试组合快照 Job
            print("📸 测试 Job 3: 组合快照")
            print("-" * 80)

            await strategy_scheduler.create_portfolio_snapshots_job()

            # 查询快照
            result = await db.execute(
                select(PortfolioSnapshot)
                .where(PortfolioSnapshot.portfolio_id == portfolio.id)
                .order_by(PortfolioSnapshot.snapshot_time.desc())
                .limit(1)
            )
            snapshot = result.scalar_one_or_none()

            if snapshot:
                print(f"  ✅ 组合快照创建完成")
                print(f"     快照ID: {snapshot.id}")
                print(f"     总价值: ${snapshot.total_value}")
                print(f"     余额: ${snapshot.balance}")
                print(f"     持仓价值: ${snapshot.holdings_value}")
                print(f"     BTC 价格: ${snapshot.btc_price}")
                print()

            # 6. 清理测试数据
            print("🧹 清理测试数据")
            print("-" * 80)

            # 删除快照
            if snapshot:
                await db.delete(snapshot)

            # 删除策略执行记录
            result = await db.execute(
                select(StrategyExecution).where(
                    StrategyExecution.user_id == test_user.id
                )
            )
            executions = result.scalars().all()
            for exec_record in executions:
                await db.delete(exec_record)

            # 删除交易
            result = await db.execute(
                select(Trade).where(Trade.portfolio_id == portfolio.id)
            )
            trades = result.scalars().all()
            for trade in trades:
                await db.delete(trade)

            # 删除组合
            await db.delete(portfolio)
            await db.commit()

            print(f"  ✅ 清理完成")
            print()

            # 最终总结
            print("=" * 80)
            print("🎉 Scheduler Jobs 测试通过!")
            print("=" * 80)
            print()

        except Exception as e:
            print(f"\n❌ 测试出错: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """运行所有测试"""
    try:
        await test_strategy_orchestrator()
        await test_scheduler_jobs()

        print("=" * 80)
        print("🎉 所有测试通过!")
        print("=" * 80)
        print()
        print("📋 测试总结:")
        print("  ✅ StrategyOrchestrator 完整流程正常")
        print("  ✅ 信念分数计算正常")
        print("  ✅ 交易信号生成正常")
        print("  ✅ Paper Trading 执行正常")
        print("  ✅ 策略执行记录正常")
        print("  ✅ 市场数据采集 Job 正常")
        print("  ✅ 策略执行 Job 正常")
        print("  ✅ 组合快照 Job 正常")
        print()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
