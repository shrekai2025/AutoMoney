"""OCO Order Manager - OCO订单管理器(模拟)

在Paper Trading环境中模拟OCO订单的止损止盈机制
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models import Portfolio, PortfolioHolding, Trade
from app.schemas.strategy import TradeType

logger = logging.getLogger(__name__)


class OCOOrderManager:
    """
    OCO订单管理器
    
    功能:
    - 记录每笔交易的止损止盈价格
    - 在价格更新时检查是否触发
    - 自动执行止损/止盈
    """
    
    # 使用PortfolioHolding的metadata字段存储OCO信息
    # 格式: {
    #   "oco_order": {
    #       "stop_loss_price": 42000.0,
    #       "take_profit_price": 45000.0,
    #       "entry_price": 43000.0,
    #       "side": "LONG",
    #       "created_at": "2024-01-01T00:00:00"
    #   }
    # }
    
    async def attach_oco_to_holding(
        self,
        db: AsyncSession,
        portfolio_id: str,
        symbol: str,
        oco_data: dict
    ):
        """
        将OCO订单信息附加到持仓
        
        Args:
            portfolio_id: 组合ID
            symbol: 币种
            oco_data: OCO订单数据 {
                "stop_loss_price": float,
                "take_profit_price": float,
                "entry_price": float,
                "side": "LONG"/"SHORT"
            }
        """
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.symbol == symbol,
            )
        )
        holding = result.scalar_one_or_none()
        
        if not holding:
            logger.warning(f"未找到持仓: {portfolio_id} - {symbol}")
            return
        
        # 添加时间戳
        oco_data["created_at"] = datetime.utcnow().isoformat()
        
        # 更新metadata
        if holding.metadata is None:
            holding.metadata = {}
        
        holding.metadata["oco_order"] = oco_data
        
        await db.commit()
        
        logger.info(f"✅ OCO订单已附加到持仓: {symbol}")
        logger.info(f"   止损: {oco_data['stop_loss_price']:.2f}")
        logger.info(f"   止盈: {oco_data['take_profit_price']:.2f}")
    
    async def check_and_execute_oco(
        self,
        db: AsyncSession,
        portfolio: Portfolio,
        symbol: str,
        current_price: Decimal,
        paper_engine  # 避免循环导入,使用duck typing
    ) -> Optional[str]:
        """
        检查并执行OCO订单
        
        Args:
            db: 数据库会话
            portfolio: 组合对象
            symbol: 币种
            current_price: 当前价格
            paper_engine: PaperTradingEngine实例
        
        Returns:
            执行类型: "STOP_LOSS" / "TAKE_PROFIT" / None
        """
        # 获取持仓
        result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio.id,
                PortfolioHolding.symbol == symbol,
            )
        )
        holding = result.scalar_one_or_none()
        
        if not holding:
            return None
        
        # 检查是否有OCO订单
        if not holding.metadata or "oco_order" not in holding.metadata:
            return None
        
        oco = holding.metadata["oco_order"]
        stop_loss_price = Decimal(str(oco["stop_loss_price"]))
        take_profit_price = Decimal(str(oco["take_profit_price"]))
        side = oco["side"]
        
        # 判断是否触发
        triggered_type = None
        
        if side == "LONG":
            # 做多: 价格跌破止损 或 突破止盈
            if current_price <= stop_loss_price:
                triggered_type = "STOP_LOSS"
                execution_price = stop_loss_price
            elif current_price >= take_profit_price:
                triggered_type = "TAKE_PROFIT"
                execution_price = take_profit_price
        else:  # SHORT
            # 做空: 价格突破止损 或 跌破止盈
            if current_price >= stop_loss_price:
                triggered_type = "STOP_LOSS"
                execution_price = stop_loss_price
            elif current_price <= take_profit_price:
                triggered_type = "TAKE_PROFIT"
                execution_price = take_profit_price
        
        if not triggered_type:
            return None
        
        # 执行平仓
        logger.info(f"🔔 OCO订单触发: {symbol} {triggered_type} @ {execution_price}")
        
        try:
            await paper_engine.execute_trade(
                db=db,
                portfolio_id=portfolio.id,
                symbol=symbol,
                trade_type=TradeType.SELL,  # 平仓都是卖出
                amount=holding.amount,
                price=execution_price,
                reason=f"OCO {triggered_type} 触发 @ {execution_price}"
            )
            
            logger.info(f"✅ {triggered_type} 执行成功")
            
            return triggered_type
            
        except Exception as e:
            logger.error(f"OCO订单执行失败: {e}", exc_info=True)
            return None
    
    async def check_all_holdings(
        self,
        db: AsyncSession,
        portfolio_id: str,
        current_prices: dict,  # {symbol: price}
        paper_engine
    ) -> List[dict]:
        """
        检查组合所有持仓的OCO订单
        
        Args:
            portfolio_id: 组合ID
            current_prices: 当前价格字典 {"BTC": 43000, "ETH": 2300, ...}
            paper_engine: PaperTradingEngine实例
        
        Returns:
            触发记录列表: [{"symbol": "BTC", "type": "STOP_LOSS"}, ...]
        """
        # 获取组合
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()
        
        if not portfolio:
            logger.warning(f"未找到组合: {portfolio_id}")
            return []
        
        # 获取所有持仓
        holdings_result = await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id
            )
        )
        holdings = holdings_result.scalars().all()
        
        triggered = []
        
        for holding in holdings:
            symbol = holding.symbol
            if symbol not in current_prices:
                continue
            
            current_price = Decimal(str(current_prices[symbol]))
            
            trigger_type = await self.check_and_execute_oco(
                db=db,
                portfolio=portfolio,
                symbol=symbol,
                current_price=current_price,
                paper_engine=paper_engine
            )
            
            if trigger_type:
                triggered.append({
                    "symbol": symbol,
                    "type": trigger_type,
                    "price": float(current_price)
                })
        
        return triggered


# 全局实例
oco_order_manager = OCOOrderManager()

