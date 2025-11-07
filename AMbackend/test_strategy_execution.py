"""
测试策略执行和模拟交易系统

测试内容:
1. 创建Portfolio
2. 手动触发策略执行
3. 验证交易记录
4. 验证持仓更新
5. 验证盈亏计算
"""

import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, AsyncSessionLocal
from app.models import User, Portfolio, PortfolioHolding, Trade, StrategyExecution
from app.services.strategy.strategy_orchestrator import strategy_orchestrator
from app.services.market.real_market_data import real_market_data_service
from app.services.strategy.real_agent_executor import real_agent_executor
from app.services.indicators.calculator import IndicatorCalculator
from app.services.data_collectors.manager import data_manager


async def test_strategy_execution():
    """测试完整的策略执行流程"""

    print("=" * 60)
    print("策略执行和模拟交易系统测试")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            # 1. 获取测试用户
            print("\n[1] 获取测试用户...")
            result = await db.execute(
                select(User).where(User.email == "yeheai9906@gmail.com")
            )
            user = result.scalar_one_or_none()

            if not user:
                print("❌ 测试用户不存在")
                return

            print(f"✅ 用户: {user.email} (ID: {user.id})")

            # 2. 查找或创建Portfolio
            print("\n[2] 查找测试Portfolio...")
            result = await db.execute(
                select(Portfolio)
                .where(Portfolio.user_id == user.id)
                .where(Portfolio.is_active == True)
            )
            portfolio = result.scalars().first()

            if not portfolio:
                print("❌ 没有找到活跃的Portfolio")
                return

            print(f"✅ Portfolio: {portfolio.name}")
            print(f"   ID: {portfolio.id}")
            print(f"   策略: {portfolio.strategy_name}")
            print(f"   初始余额: ${portfolio.initial_balance:,.2f}")
            print(f"   当前价值: ${portfolio.total_value:,.2f}")
            print(f"   盈亏: ${portfolio.total_pnl:,.2f} ({portfolio.total_pnl_percent:.2f}%)")

            # 3. 获取真实市场数据
            print("\n[3] 获取市场数据...")
            try:
                market_data = await real_market_data_service.get_complete_market_snapshot()
                print(f"✅ BTC价格: ${market_data.get('btc_price', 0):,.2f}")
                print(f"   ETH价格: ${market_data.get('eth_price', 0):,.2f}")

                # 添加技术指标
                all_data = await data_manager.collect_all()
                if hasattr(all_data, 'btc_ohlcv') and all_data.btc_ohlcv:
                    indicators = IndicatorCalculator.calculate_all(all_data.btc_ohlcv)
                    market_data["indicators"] = indicators
                    print(f"   技术指标: EMA21=${indicators.get('ema_21', 0):,.2f}, RSI={indicators.get('rsi_14', 0):.2f}")

            except Exception as e:
                print(f"❌ 获取市场数据失败: {e}")
                return

            # 4. 执行真实Agent分析
            print("\n[4] 执行Agent分析...")
            try:
                agent_outputs = await real_agent_executor.execute_all_agents(
                    market_data=market_data,
                    db=db,
                    user_id=user.id,
                    strategy_execution_id=None,
                )

                print("✅ Agent分析完成:")
                for agent_name, output in agent_outputs.items():
                    if output and isinstance(output, dict):
                        signal = output.get('signal', 'N/A')
                        confidence = output.get('confidence', 0)
                        print(f"   {agent_name}: {signal} (置信度: {confidence:.2f})")

            except Exception as e:
                print(f"❌ Agent分析失败: {e}")
                import traceback
                traceback.print_exc()
                return

            # 5. 执行策略
            print("\n[5] 执行策略...")
            try:
                execution = await strategy_orchestrator.execute_strategy(
                    db=db,
                    user_id=user.id,
                    portfolio_id=str(portfolio.id),
                    market_data=market_data,
                    agent_outputs=agent_outputs,
                )

                print(f"✅ 策略执行完成:")
                print(f"   执行ID: {execution.id}")
                print(f"   状态: {execution.status}")
                print(f"   信号: {execution.signal}")
                print(f"   信念分数: {execution.conviction_score:.2f}")
                print(f"   执行时间: {execution.execution_time}")

            except Exception as e:
                print(f"❌ 策略执行失败: {e}")
                import traceback
                traceback.print_exc()
                return

            # 6. 查询交易记录
            print("\n[6] 查询交易记录...")
            result = await db.execute(
                select(Trade)
                .where(Trade.portfolio_id == portfolio.id)
                .order_by(Trade.executed_at.desc())
                .limit(5)
            )
            trades = result.scalars().all()

            if trades:
                print(f"✅ 最近{len(trades)}笔交易:")
                for trade in trades:
                    pnl_str = f"盈亏: ${trade.realized_pnl:,.2f}" if trade.realized_pnl else ""
                    print(f"   {trade.trade_type} {trade.amount} {trade.symbol} @ ${trade.price:,.2f} {pnl_str}")
            else:
                print("   没有交易记录")

            # 7. 查询持仓
            print("\n[7] 查询当前持仓...")
            result = await db.execute(
                select(PortfolioHolding)
                .where(PortfolioHolding.portfolio_id == portfolio.id)
            )
            holdings = result.scalars().all()

            if holdings:
                print(f"✅ 当前持仓 ({len(holdings)}个):")
                # 先遍历并计算总价值，避免后续lazy loading问题
                holdings_data = []
                for holding in holdings:
                    holdings_data.append({
                        'symbol': holding.symbol,
                        'amount': holding.amount,
                        'avg_buy_price': holding.avg_buy_price,
                        'market_value': holding.market_value,
                        'unrealized_pnl': holding.unrealized_pnl,
                        'unrealized_pnl_percent': holding.unrealized_pnl_percent,
                    })

                # 打印持仓信息
                holdings_value = 0.0
                for data in holdings_data:
                    print(f"   {data['symbol']}: {data['amount']} @ 均价${data['avg_buy_price']:,.2f}")
                    print(f"      当前价值: ${data['market_value']:,.2f}, 盈亏: ${data['unrealized_pnl']:,.2f} ({data['unrealized_pnl_percent']:.2f}%)")
                    holdings_value += float(data['market_value'])
            else:
                print("   没有持仓")
                holdings_value = 0.0

            # 8. 刷新Portfolio数据
            await db.refresh(portfolio)

            print("\n[8] Portfolio最新状态:")
            print(f"   总价值: ${portfolio.total_value:,.2f}")
            print(f"   现金余额: ${portfolio.current_balance:,.2f}")
            print(f"   持仓价值: ${holdings_value:,.2f}")
            print(f"   总盈亏: ${portfolio.total_pnl:,.2f} ({portfolio.total_pnl_percent:.2f}%)")

            print("\n" + "=" * 60)
            print("✅ 测试完成！")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_strategy_execution())
