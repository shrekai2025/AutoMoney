"""Strategy Orchestrator - 策略编排器

完整的策略执行流程:
1. 采集市场数据
2. 执行 3 个 Agent (Macro, OnChain, TA)
3. 计算信念分数
4. 生成交易信号
5. 执行 Paper Trading
6. 记录策略执行结果
"""

from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import StrategyExecution, Portfolio
from app.schemas.strategy import TradeType, StrategyStatus
from app.services.decision.conviction_calculator import (
    ConvictionCalculator,
    ConvictionInput,
)
from app.services.decision.signal_generator import SignalGenerator, TradeSignal
from app.services.trading.paper_engine import paper_engine
from app.services.trading.portfolio_service import portfolio_service
from app.services.strategy.real_agent_executor import real_agent_executor

logger = logging.getLogger(__name__)


class StrategyOrchestrator:
    """
    策略编排器

    负责完整的策略执行流程，整合所有组件
    """

    def __init__(self):
        self.conviction_calculator = ConvictionCalculator()
        self.signal_generator = SignalGenerator()

    @staticmethod
    def _serialize_for_json(obj: Any) -> Any:
        """
        递归序列化对象以便存储到 JSONB

        处理:
        - datetime → ISO 8601 字符串
        - Decimal → float
        - Pydantic models → dict
        - dict/list → 递归处理
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'dict'):  # Pydantic model
            return StrategyOrchestrator._serialize_for_json(obj.dict())
        elif isinstance(obj, dict):
            return {k: StrategyOrchestrator._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [StrategyOrchestrator._serialize_for_json(item) for item in obj]
        elif isinstance(obj, tuple):
            return [StrategyOrchestrator._serialize_for_json(item) for item in obj]
        else:
            return obj

    async def execute_strategy(
        self,
        db: AsyncSession,
        user_id: int,
        portfolio_id: str,
        market_data: Dict[str, Any],
        agent_outputs: Optional[Dict[str, Any]] = None,
    ) -> StrategyExecution:
        """
        执行完整策略流程

        Args:
            db: 数据库会话
            user_id: 用户ID
            portfolio_id: 投资组合ID
            market_data: 市场数据快照
            agent_outputs: Agent 分析输出 (如果为 None，则跳过 Agent 执行步骤)

        Returns:
            StrategyExecution: 策略执行记录
        """
        execution_start = datetime.utcnow()

        try:
            # 获取投资组合 (with eager loading of holdings)
            result = await db.execute(
                select(Portfolio)
                .options(selectinload(Portfolio.holdings))
                .where(Portfolio.id == portfolio_id)
            )
            portfolio = result.scalar_one_or_none()

            if not portfolio:
                raise ValueError(f"投资组合不存在: {portfolio_id}")

            # Step 1: 先创建策略执行记录（占位），获取 ID
            serialized_market_data = self._serialize_for_json(market_data)

            strategy_execution = StrategyExecution(
                user_id=user_id,
                execution_time=execution_start,
                strategy_name="Multi-Agent Strategy",
                market_snapshot=serialized_market_data,
                status=StrategyStatus.RUNNING.value,
            )

            db.add(strategy_execution)
            await db.flush()  # 获取 strategy_execution.id

            strategy_execution_id = str(strategy_execution.id)
            logger.info(f"创建策略执行记录: {strategy_execution_id}")

            # Step 2: 使用提供的 Agent 输出，或执行真实 Agents
            if not agent_outputs:
                logger.info("开始执行真实 Agent 分析")
                try:
                    agent_outputs = await real_agent_executor.execute_all_agents(
                        market_data=market_data,
                        db=db,
                        user_id=user_id,
                        strategy_execution_id=strategy_execution_id,
                    )
                    logger.info(f"Agent 执行成功: {agent_outputs.keys()}")
                except Exception as e:
                    logger.error(f"Agent 执行失败: {e}", exc_info=True)
                    # 使用默认值
                    agent_outputs = {
                        "macro": {"signal": "NEUTRAL", "confidence": 0.5},
                        "onchain": {"signal": "NEUTRAL", "confidence": 0.5},
                        "ta": {"signal": "NEUTRAL", "confidence": 0.5},
                    }

            # Step 3: 计算信念分数
            conviction_input = ConvictionInput(
                macro_output=agent_outputs.get("macro", {}),
                ta_output=agent_outputs.get("ta", {}),
                onchain_output=agent_outputs.get("onchain", {}),
                market_data=market_data,
            )

            conviction_result = self.conviction_calculator.calculate(conviction_input)

            # Step 4: 计算当前仓位
            current_position = await self._calculate_position_ratio(portfolio, market_data)

            # Step 5: 生成交易信号
            signal_result = self.signal_generator.generate_signal(
                conviction_score=conviction_result.score,
                market_data=market_data,
                current_position=current_position,
            )

            # Step 6: 更新策略执行记录的信号信息
            strategy_execution.conviction_score = conviction_result.score
            strategy_execution.signal = signal_result.signal.value
            strategy_execution.signal_strength = signal_result.signal_strength
            strategy_execution.position_size = signal_result.position_size
            strategy_execution.risk_level = signal_result.risk_level.value

            # Step 7: 执行交易（如果需要）
            trade = None
            if signal_result.should_execute and signal_result.signal != TradeSignal.HOLD:
                try:
                    trade = await self._execute_trade(
                        db=db,
                        portfolio=portfolio,
                        signal_result=signal_result,
                        market_data=market_data,
                        strategy_execution_id=str(strategy_execution.id),
                        conviction_score=conviction_result.score,
                    )

                except Exception as e:
                    logger.error(f"交易执行失败: {e}")
                    strategy_execution.error_message = str(e)
                    strategy_execution.status = StrategyStatus.FAILED.value

            # Step 7: 更新组合价值
            btc_price = Decimal(str(market_data.get("btc_price", 0)))
            if btc_price > 0:
                await portfolio_service.update_portfolio_value(
                    db=db,
                    portfolio=portfolio,
                    current_btc_price=btc_price,
                )

            # Step 8: 完成策略执行
            if strategy_execution.status == StrategyStatus.RUNNING.value:
                strategy_execution.status = StrategyStatus.COMPLETED.value

            # 计算执行时间
            execution_duration = (datetime.utcnow() - execution_start).total_seconds() * 1000
            strategy_execution.execution_duration_ms = int(execution_duration)

            await db.commit()
            await db.refresh(strategy_execution)

            logger.info(
                f"策略执行完成 - ID: {strategy_execution.id}, "
                f"信号: {signal_result.signal.value}, "
                f"信念分数: {conviction_result.score:.2f}"
            )

            return strategy_execution

        except Exception as e:
            logger.error(f"策略执行失败: {e}", exc_info=True)

            # 创建失败记录
            # 序列化 market_data 以确保可以存储到 JSONB
            serialized_market_data = self._serialize_for_json(market_data)

            failed_execution = StrategyExecution(
                user_id=user_id,
                execution_time=execution_start,
                strategy_name="Multi-Agent Strategy",
                market_snapshot=serialized_market_data,
                status=StrategyStatus.FAILED.value,
                error_message=str(e),
            )

            db.add(failed_execution)
            await db.commit()
            await db.refresh(failed_execution)

            raise

    async def _calculate_position_ratio(
        self,
        portfolio: Portfolio,
        market_data: Dict[str, Any]
    ) -> float:
        """计算当前仓位比例"""
        if portfolio.total_value == 0:
            return 0.0

        # 假设只持有 BTC
        btc_price = Decimal(str(market_data.get("btc_price", 0)))
        if btc_price == 0:
            return 0.0

        # 计算 BTC 持仓价值
        btc_holdings_value = Decimal("0")
        for holding in portfolio.holdings:
            if holding.symbol == "BTC":
                btc_holdings_value = holding.amount * btc_price
                break

        position_ratio = float(btc_holdings_value / portfolio.total_value)
        return position_ratio

    async def _execute_trade(
        self,
        db: AsyncSession,
        portfolio: Portfolio,
        signal_result: Any,
        market_data: Dict[str, Any],
        strategy_execution_id: str,
        conviction_score: float,
    ):
        """执行交易"""
        btc_price = Decimal(str(market_data.get("btc_price", 0)))

        if btc_price == 0:
            raise ValueError("BTC 价格为 0，无法执行交易")

        # 计算交易数量
        if signal_result.signal == TradeSignal.BUY:
            # 买入: 使用仓位比例 * 总价值
            trade_value = portfolio.total_value * Decimal(str(signal_result.position_size))
            amount = trade_value / btc_price
            trade_type = TradeType.BUY

        else:  # SELL
            # 卖出: 查找当前持仓
            btc_holding = None
            for holding in portfolio.holdings:
                if holding.symbol == "BTC":
                    btc_holding = holding
                    break

            if not btc_holding or btc_holding.amount == 0:
                raise ValueError("没有 BTC 持仓，无法卖出")

            # 卖出比例 * 当前持仓
            amount = btc_holding.amount * Decimal(str(signal_result.position_size))
            trade_type = TradeType.SELL

        # 执行交易
        trade = await paper_engine.execute_trade(
            db=db,
            portfolio_id=str(portfolio.id),
            symbol="BTC",
            trade_type=trade_type,
            amount=amount,
            price=btc_price,
            execution_id=strategy_execution_id,
            conviction_score=conviction_score,
            signal_strength=signal_result.signal_strength,
            reason=", ".join(signal_result.reasons),
        )

        return trade


# 全局实例
strategy_orchestrator = StrategyOrchestrator()
