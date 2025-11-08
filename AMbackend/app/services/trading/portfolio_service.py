"""Portfolio Service - 投资组合CRUD

管理用户的投资组合，包括创建、查询、更新投资组合价值
"""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Portfolio, PortfolioHolding, Trade
from app.schemas.strategy import PortfolioCreate


class PortfolioService:
    """投资组合服务"""

    async def create_portfolio(
        self,
        db: AsyncSession,
        user_id: int,
        portfolio_data: PortfolioCreate
    ) -> Portfolio:
        """创建投资组合"""
        portfolio = Portfolio(
            user_id=user_id,
            name=portfolio_data.name,
            initial_balance=portfolio_data.initial_balance,
            current_balance=portfolio_data.initial_balance,
            total_value=portfolio_data.initial_balance,
            strategy_name=portfolio_data.strategy_name,
            is_active=True,
        )

        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)

        return portfolio

    async def get_portfolio(
        self,
        db: AsyncSession,
        portfolio_id: str
    ) -> Optional[Portfolio]:
        """获取投资组合"""
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        return result.scalar_one_or_none()

    async def get_user_portfolios(
        self,
        db: AsyncSession,
        user_id: int,
        active_only: bool = True
    ) -> List[Portfolio]:
        """获取用户的所有组合"""
        query = select(Portfolio).where(Portfolio.user_id == user_id)

        if active_only:
            query = query.where(Portfolio.is_active == True)

        result = await db.execute(query)
        return result.scalars().all()

    async def update_portfolio_value(
        self,
        db: AsyncSession,
        portfolio: Portfolio,
        current_btc_price: Decimal,
        current_eth_price: Optional[Decimal] = None
    ):
        """更新投资组合总价值"""
        # 获取所有持仓
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio.id
            )
        )
        holdings = result.scalars().all()

        # 计算持仓市值
        holdings_value = Decimal("0")
        for holding in holdings:
            if holding.symbol == "BTC":
                holding.current_price = current_btc_price
            elif holding.symbol == "ETH" and current_eth_price:
                holding.current_price = current_eth_price

            holding.market_value = holding.amount * holding.current_price
            holding.unrealized_pnl = holding.market_value - holding.cost_basis
            holding.unrealized_pnl_percent = (
                float(holding.unrealized_pnl / holding.cost_basis * 100)
                if holding.cost_basis > 0 else 0
            )

            holdings_value += holding.market_value

        # 更新组合总价值和盈亏
        portfolio.total_value = portfolio.current_balance + holdings_value
        # Total P&L = 当前总价值 - 初始资金（已包含所有手续费和盈亏）
        portfolio.total_pnl = portfolio.total_value - portfolio.initial_balance
        portfolio.total_pnl_percent = (
            float(portfolio.total_pnl / portfolio.initial_balance * 100)
            if portfolio.initial_balance > 0 else 0
        )

        await db.commit()


# 全局实例
portfolio_service = PortfolioService()
