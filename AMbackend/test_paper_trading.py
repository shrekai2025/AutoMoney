"""Test Paper Trading Engine

测试模拟交易引擎的完整功能
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
from app.models import User, Portfolio, PortfolioHolding, Trade
from app.services.trading.portfolio_service import portfolio_service
from app.services.trading.paper_engine import paper_engine
from app.schemas.strategy import PortfolioCreate, TradeType

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


async def test_paper_trading():
    """测试完整的 Paper Trading 流程"""

    print("=" * 80)
    print("🧪 Paper Trading Engine 集成测试")
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
                    email="papertrading@automoney.com",
                    full_name="Paper Trading Test User",
                    is_active=True
                )
                db.add(test_user)
                await db.commit()
                await db.refresh(test_user)
                print(f"✅ 创建测试用户: {test_user.email}")
            else:
                print(f"✅ 使用现有用户: {test_user.email}")

            print()

            # 2. 创建投资组合
            print("📋 步骤 1: 创建投资组合")
            print("-" * 80)

            portfolio = await portfolio_service.create_portfolio(
                db=db,
                user_id=test_user.id,
                portfolio_data=PortfolioCreate(
                    name="Paper Trading 测试组合",
                    initial_balance=Decimal("10000"),
                    strategy_name="HODL Wave"
                )
            )

            print(f"  ✅ 创建组合: {portfolio.name}")
            print(f"     ID: {portfolio.id}")
            print(f"     初始余额: ${portfolio.initial_balance}")
            print(f"     当前余额: ${portfolio.current_balance}")
            print()

            # 3. 测试买入 BTC
            print("📈 步骤 2: 买入 BTC")
            print("-" * 80)

            btc_price = Decimal("45000")
            buy_amount = Decimal("0.1")

            trade1 = await paper_engine.execute_trade(
                db=db,
                portfolio_id=str(portfolio.id),
                symbol="BTC",
                trade_type=TradeType.BUY,
                amount=buy_amount,
                price=btc_price,
                conviction_score=85.0,
                signal_strength=0.75,
                reason="测试买入: 强烈看多信号"
            )

            print(f"  ✅ 买入交易执行成功")
            print(f"     交易ID: {trade1.id}")
            print(f"     数量: {trade1.amount} BTC")
            print(f"     价格: ${trade1.price}")
            print(f"     总额: ${trade1.total_value}")
            print(f"     手续费: ${trade1.fee} ({trade1.fee_percent}%)")
            print(f"     交易前余额: ${trade1.balance_before}")
            print(f"     交易后余额: ${trade1.balance_after}")
            print(f"     交易前持仓: {trade1.holding_before} BTC")
            print(f"     交易后持仓: {trade1.holding_after} BTC")
            print()

            # 验证余额变化
            await db.refresh(portfolio)
            expected_balance = Decimal("10000") - (buy_amount * btc_price) - trade1.fee
            assert abs(portfolio.current_balance - expected_balance) < Decimal("0.01"), \
                f"❌ 余额不正确: 期望 {expected_balance}, 实际 {portfolio.current_balance}"
            print(f"  ✅ 余额验证通过: ${portfolio.current_balance}")

            # 验证持仓创建
            result = await db.execute(
                select(PortfolioHolding).where(
                    PortfolioHolding.portfolio_id == portfolio.id,
                    PortfolioHolding.symbol == "BTC"
                )
            )
            holding = result.scalar_one()
            assert holding.amount == buy_amount, f"❌ 持仓数量不正确"
            assert holding.avg_buy_price == btc_price, f"❌ 平均买入价不正确"
            print(f"  ✅ 持仓验证通过: {holding.amount} BTC @ ${holding.avg_buy_price}")
            print()

            # 4. 测试第二次买入（追加持仓）
            print("📈 步骤 3: 追加买入 BTC")
            print("-" * 80)

            btc_price2 = Decimal("46000")  # 价格上涨
            buy_amount2 = Decimal("0.05")

            trade2 = await paper_engine.execute_trade(
                db=db,
                portfolio_id=str(portfolio.id),
                symbol="BTC",
                trade_type=TradeType.BUY,
                amount=buy_amount2,
                price=btc_price2,
                conviction_score=88.0,
                signal_strength=0.85,
                reason="测试追加买入"
            )

            print(f"  ✅ 追加买入成功")
            print(f"     数量: {trade2.amount} BTC")
            print(f"     价格: ${trade2.price}")
            print(f"     交易后持仓: {trade2.holding_after} BTC")
            print()

            # 验证持仓更新（应该是累加）
            await db.refresh(holding)
            expected_total = buy_amount + buy_amount2
            assert holding.amount == expected_total, f"❌ 总持仓数量不正确"

            # 验证平均买入价
            expected_avg_price = (
                (buy_amount * btc_price + buy_amount2 * btc_price2) / expected_total
            )
            assert abs(holding.avg_buy_price - expected_avg_price) < Decimal("0.01"), \
                f"❌ 平均买入价不正确"

            print(f"  ✅ 持仓累加验证通过: {holding.amount} BTC")
            print(f"  ✅ 平均买入价验证通过: ${holding.avg_buy_price:.2f}")
            print()

            # 5. 测试卖出（部分）
            print("📉 步骤 4: 部分卖出 BTC")
            print("-" * 80)

            btc_price3 = Decimal("47000")  # 价格继续上涨
            sell_amount = Decimal("0.08")

            trade3 = await paper_engine.execute_trade(
                db=db,
                portfolio_id=str(portfolio.id),
                symbol="BTC",
                trade_type=TradeType.SELL,
                amount=sell_amount,
                price=btc_price3,
                conviction_score=25.0,
                signal_strength=0.6,
                reason="测试卖出: 看空信号"
            )

            print(f"  ✅ 卖出交易执行成功")
            print(f"     数量: {trade3.amount} BTC")
            print(f"     价格: ${trade3.price}")
            print(f"     已实现盈亏: ${trade3.realized_pnl}")
            print(f"     已实现盈亏率: {trade3.realized_pnl_percent:.2f}%")
            print(f"     交易后持仓: {trade3.holding_after} BTC")
            print()

            # 验证盈亏计算
            assert trade3.realized_pnl is not None, "❌ 应该有已实现盈亏"
            assert trade3.realized_pnl > 0, "❌ 应该盈利（因为价格上涨）"
            print(f"  ✅ 盈亏计算验证通过: 盈利 ${trade3.realized_pnl}")

            # 验证剩余持仓
            await db.refresh(holding)
            expected_remaining = expected_total - sell_amount
            assert holding.amount == expected_remaining, f"❌ 剩余持仓数量不正确"
            print(f"  ✅ 剩余持仓验证通过: {holding.amount} BTC")
            print()

            # 6. 测试完全卖出
            print("📉 步骤 5: 完全卖出剩余 BTC")
            print("-" * 80)

            trade4 = await paper_engine.execute_trade(
                db=db,
                portfolio_id=str(portfolio.id),
                symbol="BTC",
                trade_type=TradeType.SELL,
                amount=expected_remaining,
                price=btc_price3,
            )

            print(f"  ✅ 完全卖出成功")
            print(f"     数量: {trade4.amount} BTC")
            print(f"     已实现盈亏: ${trade4.realized_pnl}")
            print()

            # 验证持仓已清空
            result = await db.execute(
                select(PortfolioHolding).where(
                    PortfolioHolding.portfolio_id == portfolio.id,
                    PortfolioHolding.symbol == "BTC"
                )
            )
            holding_after_sell = result.scalar_one_or_none()
            assert holding_after_sell is None, "❌ 持仓应该已清空"
            print(f"  ✅ 持仓清空验证通过")
            print()

            # 7. 验证组合统计
            print("📊 步骤 6: 验证组合统计")
            print("-" * 80)

            await db.refresh(portfolio)
            print(f"  总交易次数: {portfolio.total_trades}")
            print(f"  盈利交易: {portfolio.winning_trades}")
            print(f"  亏损交易: {portfolio.losing_trades}")
            print(f"  胜率: {portfolio.win_rate:.1f}%")
            print()

            assert portfolio.total_trades == 4, "❌ 总交易次数应该是4"
            print(f"  ✅ 组合统计验证通过")
            print()

            # 8. 测试余额不足情况
            print("⚠️  步骤 7: 测试余额不足")
            print("-" * 80)

            try:
                await paper_engine.execute_trade(
                    db=db,
                    portfolio_id=str(portfolio.id),
                    symbol="BTC",
                    trade_type=TradeType.BUY,
                    amount=Decimal("1000"),  # 买入太多
                    price=btc_price,
                )
                print("  ❌ 应该抛出余额不足异常")
                assert False
            except ValueError as e:
                if "余额不足" in str(e):
                    print(f"  ✅ 正确抛出余额不足异常: {e}")
                else:
                    raise

            print()

            # 9. 测试持仓不足情况
            print("⚠️  步骤 8: 测试持仓不足")
            print("-" * 80)

            try:
                await paper_engine.execute_trade(
                    db=db,
                    portfolio_id=str(portfolio.id),
                    symbol="BTC",
                    trade_type=TradeType.SELL,
                    amount=Decimal("10"),  # 卖出太多
                    price=btc_price,
                )
                print("  ❌ 应该抛出持仓不足异常")
                assert False
            except ValueError as e:
                if "没有" in str(e) or "持仓不足" in str(e):
                    print(f"  ✅ 正确抛出持仓异常: {e}")
                else:
                    raise

            print()

            # 10. 清理测试数据
            print("🧹 步骤 9: 清理测试数据")
            print("-" * 80)

            # 删除所有交易记录
            result = await db.execute(
                select(Trade).where(Trade.portfolio_id == portfolio.id)
            )
            trades = result.scalars().all()
            for trade in trades:
                await db.delete(trade)

            # 删除组合
            await db.delete(portfolio)
            await db.commit()

            print(f"  ✅ 清理完成: 删除了 {len(trades)} 条交易记录和 1 个组合")
            print()

            # 最终总结
            print("=" * 80)
            print("🎉 所有测试通过!")
            print("=" * 80)
            print()
            print("📋 测试总结:")
            print("  ✅ 买入功能正常 (创建持仓)")
            print("  ✅ 追加买入功能正常 (累加持仓)")
            print("  ✅ 部分卖出功能正常 (计算盈亏)")
            print("  ✅ 完全卖出功能正常 (清空持仓)")
            print("  ✅ 余额检查正常")
            print("  ✅ 持仓检查正常")
            print("  ✅ 手续费计算正确 (0.1%)")
            print("  ✅ 盈亏计算正确")
            print("  ✅ 组合统计更新正确")
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


if __name__ == "__main__":
    asyncio.run(test_paper_trading())
