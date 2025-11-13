"""手动执行交易脚本"""
import asyncio
import sys
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.models.portfolio import Portfolio, PortfolioHolding, Trade
from app.core.config import settings


async def execute_trade(
    portfolio_id: str,
    price: float,
    usdt_amount: float,
):
    """执行买入交易

    Args:
        portfolio_id: 投资组合ID
        price: BTC价格 (USDT)
        usdt_amount: 购买金额 (USDT)
    """
    # 创建数据库连接
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # 1. 查询投资组合
            result = await db.execute(
                select(Portfolio).where(Portfolio.id == UUID(portfolio_id))
            )
            portfolio = result.scalar_one_or_none()

            if not portfolio:
                print(f"❌ 投资组合不存在: {portfolio_id}")
                return

            print(f"\n📊 投资组合: {portfolio.name}")
            print(f"   当前余额: ${portfolio.current_balance:,.2f} USDT")
            print(f"   总价值: ${portfolio.total_value:,.2f} USDT")

            # 2. 检查余额
            if portfolio.current_balance < Decimal(str(usdt_amount)):
                print(f"❌ 余额不足! 需要 ${usdt_amount:,.2f}, 当前余额 ${portfolio.current_balance:,.2f}")
                return

            # 3. 计算交易参数
            fee_percent = Decimal("0.001")  # 0.1% 手续费
            total_cost = Decimal(str(usdt_amount))
            fee = total_cost * fee_percent
            net_amount = total_cost - fee
            btc_amount = net_amount / Decimal(str(price))

            print(f"\n💰 交易详情:")
            print(f"   BTC价格: ${price:,.2f} USDT")
            print(f"   购买金额: ${usdt_amount:,.2f} USDT")
            print(f"   手续费 (0.1%): ${fee:,.2f} USDT")
            print(f"   净购买金额: ${net_amount:,.2f} USDT")
            print(f"   获得BTC: {btc_amount:.8f} BTC")

            # 4. 查询或创建持仓
            holding_result = await db.execute(
                select(PortfolioHolding).where(
                    PortfolioHolding.portfolio_id == UUID(portfolio_id),
                    PortfolioHolding.symbol == "BTC"
                )
            )
            holding = holding_result.scalar_one_or_none()

            holding_before = float(holding.amount) if holding else 0.0

            if holding:
                # 更新现有持仓
                old_cost_basis = holding.cost_basis
                old_amount = holding.amount

                # 计算新的平均买入价
                new_cost_basis = old_cost_basis + net_amount
                new_amount = old_amount + btc_amount
                new_avg_price = new_cost_basis / new_amount

                holding.amount = new_amount
                holding.avg_buy_price = new_avg_price
                holding.cost_basis = new_cost_basis
                holding.current_price = Decimal(str(price))
                holding.market_value = new_amount * Decimal(str(price))
                holding.unrealized_pnl = holding.market_value - new_cost_basis
                holding.unrealized_pnl_percent = (holding.unrealized_pnl / new_cost_basis) * 100 if new_cost_basis > 0 else Decimal(0)
                holding.last_updated = datetime.utcnow()

                if not holding.first_buy_time:
                    holding.first_buy_time = datetime.utcnow()
            else:
                # 创建新持仓
                holding = PortfolioHolding(
                    portfolio_id=UUID(portfolio_id),
                    symbol="BTC",
                    amount=btc_amount,
                    avg_buy_price=Decimal(str(price)),
                    current_price=Decimal(str(price)),
                    market_value=btc_amount * Decimal(str(price)),
                    cost_basis=net_amount,
                    unrealized_pnl=Decimal(0),
                    unrealized_pnl_percent=Decimal(0),
                    first_buy_time=datetime.utcnow(),
                    last_updated=datetime.utcnow(),
                )
                db.add(holding)

            # 5. 更新投资组合余额
            balance_before = float(portfolio.current_balance)
            portfolio.current_balance -= total_cost
            balance_after = float(portfolio.current_balance)

            # 更新总价值 (余额 + 持仓市值)
            portfolio.total_value = portfolio.current_balance + holding.market_value

            # 更新交易统计
            portfolio.total_trades = (portfolio.total_trades or 0) + 1

            # 6. 创建交易记录
            trade = Trade(
                portfolio_id=UUID(portfolio_id),
                execution_id=None,  # 手动交易没有 execution_id
                symbol="BTC",
                trade_type="BUY",
                amount=float(btc_amount),
                price=Decimal(str(price)),
                total_value=total_cost,
                fee=fee,
                fee_percent=fee_percent,
                balance_before=Decimal(str(balance_before)),
                balance_after=Decimal(str(balance_after)),
                holding_before=Decimal(str(holding_before)),
                holding_after=holding.amount,
                realized_pnl=None,  # 买入没有实现盈亏
                realized_pnl_percent=None,
                conviction_score=None,
                signal_strength=None,
                reason="手动交易 - 用户指定买入",
                executed_at=datetime.utcnow(),
            )
            db.add(trade)

            # 7. 提交事务
            await db.commit()
            await db.refresh(portfolio)
            await db.refresh(holding)
            await db.refresh(trade)

            print(f"\n✅ 交易成功!")
            print(f"\n📈 交易后状态:")
            print(f"   余额: ${portfolio.current_balance:,.2f} USDT (变化: ${balance_after - balance_before:,.2f})")
            print(f"   BTC持仓: {holding.amount:.8f} BTC (变化: +{btc_amount:.8f})")
            print(f"   持仓市值: ${holding.market_value:,.2f} USDT")
            print(f"   总价值: ${portfolio.total_value:,.2f} USDT")
            print(f"   交易ID: {trade.id}")

        except Exception as e:
            await db.rollback()
            print(f"\n❌ 交易失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    portfolio_id = "484ceb4f-a6bb-4cde-8fc9-86b8735a5464"
    price = 102112.48  # BTC价格
    usdt_amount = 10000.0  # 购买金额

    print(f"🚀 开始执行手动交易...")
    print(f"   投资组合ID: {portfolio_id}")
    print(f"   交易类型: 买入 BTC")
    print(f"   价格: ${price:,.2f} USDT")
    print(f"   金额: ${usdt_amount:,.2f} USDT")

    asyncio.run(execute_trade(portfolio_id, price, usdt_amount))
