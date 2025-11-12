"""Strategy Orchestrator - 策略编排器

完整的策略执行流程:
1. 采集市场数据
2. 执行业务Agent (根据策略定义)
3. 动态加载决策Agent
4. 生成交易决策
5. 执行 Paper Trading
6. 记录策略执行结果
"""

from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import logging
import importlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import StrategyExecution, Portfolio, StrategyDefinition
from app.schemas.strategy import TradeType, StrategyStatus, TradeSignal
from app.services.trading.paper_engine import paper_engine
from app.services.trading.portfolio_service import portfolio_service
from app.services.strategy.real_agent_executor import real_agent_executor
from app.agents.general_analysis_agent import general_analysis_agent

logger = logging.getLogger(__name__)


class StrategyOrchestrator:
    """
    策略编排器（重构版）

    负责完整的策略执行流程，支持：
    - 从strategy_definition动态加载决策Agent
    - 从instance_params读取策略参数
    - 支持多种策略模板
    """

    def __init__(self):
        pass  # 不再持有固定的calculator和generator
    
    def _load_decision_agent(self, strategy_definition: StrategyDefinition):
        """
        动态加载决策Agent
        
        Args:
            strategy_definition: 策略模板
            
        Returns:
            决策Agent实例
        """
        try:
            module = importlib.import_module(strategy_definition.decision_agent_module)
            agent_class = getattr(module, strategy_definition.decision_agent_class)
            return agent_class()
        except Exception as e:
            logger.error(
                f"加载决策Agent失败: {strategy_definition.decision_agent_module}."
                f"{strategy_definition.decision_agent_class}, 错误: {e}"
            )
            raise ValueError(f"Failed to load decision agent: {str(e)}")

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
            # 获取投资组合 (with eager loading of holdings and strategy_definition)
            result = await db.execute(
                select(Portfolio)
                .options(
                    selectinload(Portfolio.holdings),
                    selectinload(Portfolio.strategy_definition)
                )
                .where(Portfolio.id == portfolio_id)
            )
            portfolio = result.scalar_one_or_none()

            if not portfolio:
                raise ValueError(f"投资组合不存在: {portfolio_id}")
            
            if not portfolio.strategy_definition:
                raise ValueError(f"投资组合{portfolio_id}未关联策略模板")
            
            strategy_definition = portfolio.strategy_definition
            logger.info(f"执行策略: {strategy_definition.display_name} (实例: {portfolio.instance_name})")

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
            agent_errors = {}
            if not agent_outputs:
                logger.info("开始执行真实 Agent 分析")
                try:
                    agent_outputs, agent_errors = await real_agent_executor.execute_all_agents(
                        market_data=market_data,
                        db=db,
                        user_id=user_id,
                        strategy_execution_id=strategy_execution_id,
                    )
                    logger.info(f"✅ Agent 执行成功: {agent_outputs.keys()}")
                except Exception as e:
                    logger.error(f"❌ Agent 执行失败: {e}", exc_info=True)
                    # Agent工作错误 - 不继续执行策略
                    strategy_execution.status = StrategyStatus.FAILED.value
                    strategy_execution.error_message = f"Agent工作错误: {str(e)}"

                    # 记录详细的错误信息
                    from app.services.strategy.real_agent_executor import AgentExecutionError
                    if isinstance(e, AgentExecutionError):
                        strategy_execution.error_details = {
                            "error_type": "agent_execution_failed",
                            "failed_agent": e.agent_name,
                            "error_message": e.error_message,
                            "retry_count": e.retry_count,
                        }
                    else:
                        strategy_execution.error_details = {
                            "error_type": "unknown_error",
                            "error_message": str(e),
                        }

                    await db.commit()
                    return strategy_execution

            # Step 3: 加载决策Agent（动态）
            decision_agent = self._load_decision_agent(strategy_definition)
            logger.info(f"已加载决策Agent: {strategy_definition.decision_agent_class}")

            # Step 4: 计算当前仓位
            current_position = await self._calculate_position_ratio(portfolio, market_data)

            # Step 5: 准备portfolio运行时状态
            portfolio_state = {
                "consecutive_bullish_count": portfolio.consecutive_bullish_count or 0,
                "consecutive_bearish_count": portfolio.consecutive_bearish_count or 0,
                "last_conviction_score": portfolio.last_conviction_score,
            }

            # Step 6: 使用决策Agent生成决策（整合了信念分数计算和信号生成）
            decision_result = decision_agent.decide(
                agent_outputs=agent_outputs,
                market_data=market_data,
                instance_params=portfolio.instance_params,  # 从instance_params读取参数
                portfolio_state=portfolio_state,
                current_position=current_position,
            )
            
            conviction_score = decision_result["conviction_score"]
            signal = decision_result["signal"]
            signal_strength = decision_result["signal_strength"]
            position_size = decision_result["position_size"]
            risk_level = decision_result["risk_level"]
            should_execute = decision_result["should_execute"]
            reasons = decision_result["reasons"]
            warnings = decision_result["warnings"]
            
            logger.info(
                f"决策完成: signal={signal}, conviction={conviction_score:.2f}, "
                f"position_size={position_size:.4f}, should_execute={should_execute}"
            )

            # Step 7: 更新连续信号计数器
            await self._update_consecutive_signals(
                portfolio=portfolio,
                conviction_score=conviction_score,
                signal=signal,
            )

            # Step 8: 更新策略执行记录的信号信息
            strategy_execution.conviction_score = conviction_score
            strategy_execution.signal = signal.value if hasattr(signal, 'value') else str(signal)
            strategy_execution.signal_strength = signal_strength
            strategy_execution.position_size = position_size
            strategy_execution.risk_level = risk_level.value if hasattr(risk_level, 'value') else str(risk_level)

            # Step 9: 执行交易（如果需要）
            trade = None
            if should_execute and signal != TradeSignal.HOLD:
                try:
                    # 构建signal_result结构（为了兼容_execute_trade）
                    class SignalResult:
                        def __init__(self, signal, position_size, signal_strength, reasons):
                            self.signal = signal
                            self.position_size = position_size
                            self.signal_strength = signal_strength
                            self.reasons = reasons
                    
                    signal_result = SignalResult(signal, position_size, signal_strength, reasons)
                    
                    trade = await self._execute_trade(
                        db=db,
                        portfolio=portfolio,
                        signal_result=signal_result,
                        market_data=market_data,
                        strategy_execution_id=str(strategy_execution.id),
                        conviction_score=conviction_score,
                    )

                except Exception as e:
                    logger.error(f"交易执行失败: {e}")
                    strategy_execution.error_message = str(e)
                    strategy_execution.status = StrategyStatus.FAILED.value

            # Step 10: 更新组合价值
            btc_price = Decimal(str(market_data.get("btc_price", 0)))
            if btc_price > 0:
                await portfolio_service.update_portfolio_value(
                    db=db,
                    portfolio=portfolio,
                    current_btc_price=btc_price,
                )

            # Step 10.5: 生成LLM总结
            try:
                # 构建详细的问题描述，让LLM生成专业的市场分析总结
                signal_str = signal.value if hasattr(signal, 'value') else str(signal)
                summary_question = (
                    f"As the squad manager of this trading strategy, provide a comprehensive market outlook "
                    f"based on our latest analysis. Our conviction score is {conviction_score:.1f}% "
                    f"with a {signal_str} signal. Synthesize the insights from all agents "
                    f"into a professional, actionable market summary for our investors (3-5 sentences). "
                    f"Focus on key market drivers, risk factors, and our strategic positioning."
                )

                # 调用general_analysis_agent生成总结
                synthesis_result = await general_analysis_agent.synthesize(
                    user_message=summary_question,
                    agent_outputs=agent_outputs,
                    chat_history=[]
                )

                # 保存LLM生成的详细总结（使用answer字段，更专业）
                strategy_execution.llm_summary = synthesis_result.answer
                logger.info(f"LLM总结生成成功: {synthesis_result.answer[:100]}...")

            except Exception as e:
                logger.warning(f"LLM总结生成失败: {e}，使用默认消息")
                # 如果LLM调用失败，生成专业的默认消息
                signal_str = signal.value if hasattr(signal, 'value') else str(signal)
                signal_desc = "bullish" if signal_str == "BUY" else "bearish" if signal_str == "SELL" else "neutral"
                conviction_desc = "high" if conviction_score > 70 else "moderate" if conviction_score > 40 else "low"

                strategy_execution.llm_summary = (
                    f"Our squad analysis indicates a {signal_desc} outlook with {conviction_desc} conviction "
                    f"({conviction_score:.1f}%). Signal: {signal_str}. "
                    f"All agents have completed their analysis. Please check individual agent insights "
                    f"for detailed market perspectives."
                )

            # Step 11: 完成策略执行
            if strategy_execution.status == StrategyStatus.RUNNING.value:
                strategy_execution.status = StrategyStatus.COMPLETED.value

            # 计算执行时间
            execution_duration = (datetime.utcnow() - execution_start).total_seconds() * 1000
            strategy_execution.execution_duration_ms = int(execution_duration)

            await db.commit()
            await db.refresh(strategy_execution)

            logger.info(
                f"策略执行完成 - ID: {strategy_execution.id}, "
                f"信号: {signal_str}, "
                f"信念分数: {conviction_score:.2f}"
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

    async def _update_consecutive_signals(
        self,
        portfolio: Portfolio,
        conviction_score: float,
        signal: TradeSignal,
    ) -> None:
        """
        更新组合的连续信号计数器

        逻辑:
        - 看涨: conviction >= 70, signal = BUY
        - 看跌: conviction < 40, signal = SELL
        - 中性: 其他情况 (不计数)
        """
        threshold = portfolio.consecutive_signal_threshold or 30

        # 更新上次信念分数
        portfolio.last_conviction_score = conviction_score

        # 判断当前信号类型（使用新阈值）
        is_bullish = signal == TradeSignal.BUY and conviction_score >= SignalGenerator.BUY_THRESHOLD
        is_bearish = signal == TradeSignal.SELL and conviction_score < SignalGenerator.FULL_SELL_THRESHOLD

        # 更新看涨计数
        if is_bullish:
            # 连续看涨信号
            if portfolio.consecutive_bullish_count == 0:
                portfolio.consecutive_bullish_since = datetime.utcnow()

            portfolio.consecutive_bullish_count = (portfolio.consecutive_bullish_count or 0) + 1
            # 重置看跌计数
            portfolio.consecutive_bearish_count = 0
            portfolio.consecutive_bearish_since = None

            logger.info(
                f"连续看涨信号 +1: {portfolio.consecutive_bullish_count} "
                f"(阈值: {threshold}, conviction: {conviction_score:.1f}%)"
            )

        # 更新看跌计数
        elif is_bearish:
            # 连续看跌信号
            if portfolio.consecutive_bearish_count == 0:
                portfolio.consecutive_bearish_since = datetime.utcnow()

            portfolio.consecutive_bearish_count = (portfolio.consecutive_bearish_count or 0) + 1
            # 重置看涨计数
            portfolio.consecutive_bullish_count = 0
            portfolio.consecutive_bullish_since = None

            logger.info(
                f"连续看跌信号 +1: {portfolio.consecutive_bearish_count} "
                f"(conviction: {conviction_score:.1f}%)"
            )

        # 中性信号 - 重置所有计数
        else:
            if portfolio.consecutive_bullish_count > 0 or portfolio.consecutive_bearish_count > 0:
                logger.info(
                    f"中性信号, 重置计数器 "
                    f"(bullish: {portfolio.consecutive_bullish_count}, "
                    f"bearish: {portfolio.consecutive_bearish_count}, "
                    f"conviction: {conviction_score:.1f}%)"
                )

            portfolio.consecutive_bullish_count = 0
            portfolio.consecutive_bullish_since = None
            portfolio.consecutive_bearish_count = 0
            portfolio.consecutive_bearish_since = None


# 全局实例
strategy_orchestrator = StrategyOrchestrator()
