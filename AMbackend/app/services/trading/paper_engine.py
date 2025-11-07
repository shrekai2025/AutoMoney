"""Paper Trading Engine - 模拟交易引擎

执行买入/卖出操作，更新持仓，计算手续费和盈亏
"""

from typing import Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Portfolio, PortfolioHolding, Trade
from app.schemas.strategy import TradeType


class PaperTradingEngine:
    """
    模拟交易引擎

    功能:
    - 执行买入/卖出
    - 更新持仓
    - 计算手续费
    - 记录交易
    - 更新组合状态
    """

    # 手续费配置
    FEE_RATE = 0.001  # 0.1% (Binance Spot手续费)

    async def execute_trade(
        self,
        db: AsyncSession,
        portfolio_id: str,
        symbol: str,
        trade_type: TradeType,
        amount: Decimal,
        price: Decimal,
        execution_id: Optional[str] = None,
        conviction_score: Optional[float] = None,
        signal_strength: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> Trade:
        """
        执行交易

        Args:
            db: 数据库会话
            portfolio_id: 投资组合ID
            symbol: 交易币种 (BTC/ETH)
            trade_type: 交易类型 (BUY/SELL)
            amount: 交易数量
            price: 交易价格
            execution_id: 策略执行ID
            conviction_score: 信念分数
            signal_strength: 信号强度
            reason: 交易原因

        Returns:
            Trade: 交易记录
        """
        # 获取组合
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one()

        # 计算交易金额和手续费
        total_value = amount * price
        fee = total_value * Decimal(str(self.FEE_RATE))

        # 记录交易前状态
        balance_before = portfolio.current_balance
        holding_before = await self._get_holding_amount(db, portfolio_id, symbol)

        # 执行交易
        if trade_type == TradeType.BUY:
            trade = await self._execute_buy(
                db=db,
                portfolio=portfolio,
                symbol=symbol,
                amount=amount,
                price=price,
                fee=fee,
            )
        else:  # SELL
            trade = await self._execute_sell(
                db=db,
                portfolio=portfolio,
                symbol=symbol,
                amount=amount,
                price=price,
                fee=fee,
            )

        # 记录交易后状态
        balance_after = portfolio.current_balance
        holding_after = await self._get_holding_amount(db, portfolio_id, symbol)

        # 创建交易记录
        trade_record = Trade(
            portfolio_id=portfolio_id,
            execution_id=execution_id,
            symbol=symbol,
            trade_type=trade_type.value,
            amount=amount,
            price=price,
            total_value=total_value,
            fee=fee,
            fee_percent=float(self.FEE_RATE * 100),
            balance_before=balance_before,
            balance_after=balance_after,
            holding_before=holding_before,
            holding_after=holding_after,
            realized_pnl=trade.get("realized_pnl"),
            realized_pnl_percent=trade.get("realized_pnl_percent"),
            conviction_score=conviction_score,
            signal_strength=signal_strength,
            reason=reason,
            executed_at=datetime.utcnow(),
        )

        db.add(trade_record)

        # 更新组合统计
        portfolio.total_trades += 1
        if trade_record.realized_pnl and trade_record.realized_pnl > 0:
            portfolio.winning_trades += 1
        elif trade_record.realized_pnl and trade_record.realized_pnl < 0:
            portfolio.losing_trades += 1

        if portfolio.total_trades > 0:
            portfolio.win_rate = (
                float(portfolio.winning_trades / portfolio.total_trades * 100)
            )

        await db.commit()
        await db.refresh(trade_record)

        return trade_record

    async def _execute_buy(
        self,
        db: AsyncSession,
        portfolio: Portfolio,
        symbol: str,
        amount: Decimal,
        price: Decimal,
        fee: Decimal,
    ) -> dict:
        """执行买入"""
        total_cost = amount * price + fee

        # 检查余额
        if portfolio.current_balance < total_cost:
            raise ValueError(f"余额不足: 需要 {total_cost}, 但只有 {portfolio.current_balance}")

        # 扣除余额
        portfolio.current_balance -= total_cost

        # 更新或创建持仓
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio.id,
                PortfolioHolding.symbol == symbol,
            )
        )
        holding = result.scalar_one_or_none()

        if holding:
            # 更新现有持仓
            old_cost = holding.amount * holding.avg_buy_price
            new_cost = amount * price
            total_cost_basis = old_cost + new_cost
            holding.amount += amount
            holding.avg_buy_price = total_cost_basis / holding.amount
            holding.cost_basis = total_cost_basis
        else:
            # 创建新持仓
            holding = PortfolioHolding(
                portfolio_id=portfolio.id,
                symbol=symbol,
                amount=amount,
                avg_buy_price=price,
                current_price=price,
                market_value=amount * price,
                cost_basis=amount * price,
                first_buy_time=datetime.utcnow(),
            )
            db.add(holding)

        return {"realized_pnl": None, "realized_pnl_percent": None}

    async def _execute_sell(
        self,
        db: AsyncSession,
        portfolio: Portfolio,
        symbol: str,
        amount: Decimal,
        price: Decimal,
        fee: Decimal,
    ) -> dict:
        """执行卖出"""
        # 获取持仓
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio.id,
                PortfolioHolding.symbol == symbol,
            )
        )
        holding = result.scalar_one_or_none()

        if not holding:
            raise ValueError(f"没有 {symbol} 持仓")

        if holding.amount < amount:
            raise ValueError(
                f"持仓不足: 需要卖出 {amount}, 但只有 {holding.amount}"
            )

        # 计算已实现盈亏
        sell_value = amount * price - fee
        cost = amount * holding.avg_buy_price
        realized_pnl = sell_value - cost
        realized_pnl_percent = float(realized_pnl / cost * 100) if cost > 0 else 0

        # 增加余额
        portfolio.current_balance += sell_value

        # 更新持仓
        holding.amount -= amount
        holding.cost_basis -= cost

        if holding.amount == Decimal("0"):
            # 清空持仓
            await db.delete(holding)

        return {
            "realized_pnl": realized_pnl,
            "realized_pnl_percent": realized_pnl_percent,
        }

    async def _get_holding_amount(
        self,
        db: AsyncSession,
        portfolio_id: str,
        symbol: str
    ) -> Decimal:
        """获取持仓数量"""
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.symbol == symbol,
            )
        )
        holding = result.scalar_one_or_none()
        return holding.amount if holding else Decimal("0")


# 全局实例
paper_engine = PaperTradingEngine()
