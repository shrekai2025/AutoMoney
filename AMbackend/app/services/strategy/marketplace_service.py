"""Strategy Marketplace Service - 提供策略市场相关功能"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.portfolio import Portfolio, PortfolioSnapshot, Trade
from app.models.strategy_execution import StrategyExecution
from app.models.agent_execution import AgentExecution
from app.schemas.strategy import (
    StrategyMarketplaceCard,
    StrategyMarketplaceListResponse,
    StrategyDetailResponse,
    HistoryPoint,
    SquadAgent,
    ConvictionSummary,
    PerformanceHistory,
    RecentActivity,
    AgentContribution,
    StrategyParameters,
    PerformanceMetrics,
    StrategyExecutionDetail,
    AgentExecutionDetail,
    TradeResponse,
)

logger = logging.getLogger(__name__)


class MarketplaceService:
    """策略市场服务"""

    # Squad配置（固定）
    SQUAD_AGENTS = [
        {"name": "The Oracle", "role": "MacroAgent", "weight": "40%"},
        {"name": "Data Warden", "role": "OnChainAgent", "weight": "40%"},
        {"name": "Momentum Scout", "role": "TAAgent", "weight": "20%"},
    ]

    # 策略参数（固定）
    STRATEGY_PARAMETERS = {
        "assets": "BTC 60% / ETH 40%",
        "rebalance_period": "Every 4 Hours",
        "risk_level": "Low-Medium Risk",
        "min_investment": "100 USDT",
        "lockup_period": "No Lock-up",
        "management_fee": "2% Annual",
        "performance_fee": "20% on Excess Returns",
    }

    # 策略哲学（固定模板）
    STRATEGY_PHILOSOPHY = """The HODL-Wave Squad is an elite team of AI agents working in perfect synchronization to capture long-term value in the crypto market.

Squad Composition:
• The Oracle (MacroAgent 40%): Monitors global liquidity, inflation expectations, and Fed policy
• Data Warden (OnChainAgent 40%): Analyzes holder distribution, exchange flows, and network metrics
• Momentum Scout (TAAgent 20%): Tracks technical trends, RSI, and chart patterns

Mission Strategy:
Our squad employs a disciplined approach to building positions during macro-favorable conditions while maintaining strict risk controls. Maximum drawdown is kept within 20% through coordinated squad decision-making.

Ideal For:
Investors seeking long-term stable returns who trust in the fundamental value proposition of Bitcoin and Ethereum."""

    @staticmethod
    def _calculate_annualized_return(
        initial_value: Decimal, current_value: Decimal, days: int
    ) -> float:
        """计算年化收益率"""
        if days < 1 or initial_value <= 0:
            return 0.0

        growth_factor = float(current_value / initial_value)
        if growth_factor <= 0:
            return 0.0

        annualized = (growth_factor ** (365.0 / days) - 1) * 100
        return round(annualized, 2)

    @staticmethod
    def _map_risk_level(max_drawdown: float) -> str:
        """根据最大回撤映射风险等级"""
        if max_drawdown < 10:
            return "low"
        elif max_drawdown < 20:
            return "medium"
        elif max_drawdown < 30:
            return "medium-high"
        else:
            return "high"

    @staticmethod
    def _format_risk_level(risk_level: str) -> str:
        """格式化风险等级为可读字符串"""
        risk_mapping = {
            "low": "Low Risk",
            "medium": "Medium Risk",
            "high": "High Risk"
        }
        return risk_mapping.get(risk_level.lower(), "Medium Risk")

    @staticmethod
    def _format_rebalance_period(minutes: int) -> str:
        """格式化重平衡周期为可读字符串"""
        if minutes < 60:
            return f"Every {minutes} Minute{'s' if minutes != 1 else ''}"
        elif minutes % 60 == 0:
            hours = minutes // 60
            return f"Every {hours} Hour{'s' if hours != 1 else ''}"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"Every {hours}h {remaining_minutes}m"

    @staticmethod
    def _generate_tags(portfolio: Portfolio) -> List[str]:
        """生成策略标签"""
        tags = ["Macro-Driven", "BTC/ETH", "Multi-Agent"]

        # 根据风险等级添加标签
        if portfolio.max_drawdown < 15:
            tags.append("Low-Medium Risk")
        elif portfolio.max_drawdown < 25:
            tags.append("Medium Risk")
        else:
            tags.append("High Risk")

        # 根据策略名称添加标签
        if "HODL" in portfolio.name:
            tags.append("Long-Term")

        return tags

    @staticmethod
    async def _get_portfolio_history(
        db: AsyncSession, portfolio_id: str, limit: int = 16
    ) -> List[HistoryPoint]:
        """获取投资组合历史数据（归一化到100）"""
        stmt = (
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioSnapshot.snapshot_time.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        snapshots = result.scalars().all()

        if not snapshots:
            return []

        # 归一化到100基准
        initial_value = float(snapshots[0].total_value)
        if initial_value <= 0:
            return []

        history = []
        for snapshot in snapshots:
            normalized_value = (float(snapshot.total_value) / initial_value) * 100
            history.append(
                HistoryPoint(
                    date=snapshot.snapshot_time.strftime("%Y-%m"),
                    value=round(normalized_value, 2),
                )
            )

        return history

    async def get_marketplace_list(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        risk_level: Optional[str] = None,
        sort_by: str = "return",
        current_user_id: Optional[int] = None,
    ) -> StrategyMarketplaceListResponse:
        """获取策略市场列表（显示所有激活的策略实例）"""
        try:
            # 查询所有激活的策略实例（新系统：is_active=True表示运行中的实例）
            stmt = select(Portfolio).where(Portfolio.is_active == True)

            # 如果指定用户，只返回该用户的策略实例
            if user_id:
                stmt = stmt.where(Portfolio.user_id == user_id)

            result = await db.execute(stmt)
            portfolios = result.scalars().all()

            strategies = []
            for portfolio in portfolios:
                # 新系统：每个portfolio都是独立的策略实例，直接使用
                data_portfolio = portfolio

                # 计算天数
                days = (datetime.now() - data_portfolio.created_at).days
                if days < 1:
                    days = 1

                # 计算年化收益
                annualized_return = self._calculate_annualized_return(
                    data_portfolio.initial_balance, data_portfolio.total_value, days
                )

                # 使用数据库中的风险等级（优先级：数据库risk_level > 根据max_drawdown映射）
                if data_portfolio.risk_level:
                    mapped_risk_level = data_portfolio.risk_level
                else:
                    mapped_risk_level = self._map_risk_level(data_portfolio.max_drawdown)

                # 风险等级过滤
                if risk_level and mapped_risk_level != risk_level:
                    continue

                # 获取历史数据
                history = await self._get_portfolio_history(db, data_portfolio.id)

                # 生成标签
                tags = self._generate_tags(data_portfolio)

                strategy_card = StrategyMarketplaceCard(
                    id=str(data_portfolio.id),  # 使用实例ID
                    name=data_portfolio.name or data_portfolio.instance_name,
                    subtitle=data_portfolio.instance_name or "Multi-Agent Strategy",
                    description=data_portfolio.instance_description or "Elite AI squad combining macro, onchain and technical analysis",
                    tags=tags,
                    annualized_return=annualized_return,
                    max_drawdown=data_portfolio.max_drawdown,
                    sharpe_ratio=data_portfolio.sharpe_ratio or 0.0,
                    pool_size=float(data_portfolio.total_value),
                    total_pnl=float(data_portfolio.total_pnl),
                    squad_size=3,  # 固定3个Agent
                    risk_level=mapped_risk_level,
                    history=history,
                    is_active=data_portfolio.is_active,
                    initial_balance=float(data_portfolio.initial_balance) if data_portfolio.initial_balance else None,
                    deployed_at=data_portfolio.created_at.isoformat(),
                    user_activated=data_portfolio.user_id == current_user_id if current_user_id else False,  # 是否是当前用户的策略
                    activated_portfolio_id=str(data_portfolio.id) if data_portfolio.user_id == current_user_id else None,  # 策略实例ID
                )
                strategies.append(strategy_card)

            # 排序
            if sort_by == "return":
                strategies.sort(key=lambda x: x.annualized_return, reverse=True)
            elif sort_by == "risk":
                strategies.sort(key=lambda x: x.max_drawdown)
            elif sort_by == "tvl":
                strategies.sort(key=lambda x: x.pool_size, reverse=True)
            elif sort_by == "sharpe":
                strategies.sort(key=lambda x: x.sharpe_ratio, reverse=True)

            return StrategyMarketplaceListResponse(strategies=strategies)

        except Exception as e:
            logger.error(f"获取策略市场列表失败: {e}", exc_info=True)
            raise

    async def get_strategy_detail(
        self, db: AsyncSession, portfolio_id: str
    ) -> StrategyDetailResponse:
        """获取策略详情"""
        try:
            # 查询投资组合（eager load holdings和strategy_definition）
            stmt = (
                select(Portfolio)
                .options(
                    selectinload(Portfolio.holdings),
                    selectinload(Portfolio.strategy_definition)
                )
                .where(Portfolio.id == portfolio_id)
            )
            result = await db.execute(stmt)
            portfolio = result.scalar_one_or_none()

            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")

            # 计算性能指标
            days = (datetime.now() - portfolio.created_at).days
            if days < 1:
                days = 1
            annualized_return = self._calculate_annualized_return(
                portfolio.initial_balance, portfolio.total_value, days
            )

            performance_metrics = PerformanceMetrics(
                annualized_return=annualized_return,
                max_drawdown=portfolio.max_drawdown,
                sharpe_ratio=portfolio.sharpe_ratio or 0.0,
                sortino_ratio=None,  # 暂不支持
            )

            # 获取最新的conviction summary
            conviction_summary = await self._get_conviction_summary(db, portfolio.user_id)

            # Squad agents（使用实际的agent_weights配置）
            agent_weights = portfolio.instance_params.get('agent_weights') if portfolio.instance_params else None
            if agent_weights:
                # 使用数据库中保存的权重
                squad_agents = [
                    SquadAgent(
                        name="The Oracle",
                        role="MacroAgent",
                        weight=f"{int(agent_weights.get('macro', 0.4) * 100)}%"
                    ),
                    SquadAgent(
                        name="Data Warden",
                        role="OnChainAgent",
                        weight=f"{int(agent_weights.get('onchain', 0.4) * 100)}%"
                    ),
                    SquadAgent(
                        name="Momentum Scout",
                        role="TAAgent",
                        weight=f"{int(agent_weights.get('ta', 0.2) * 100)}%"
                    ),
                ]
            else:
                # 如果没有配置，使用默认配置
                squad_agents = [SquadAgent(**agent) for agent in self.SQUAD_AGENTS]

            # 获取性能历史数据
            performance_history = await self._get_performance_history(db, portfolio_id)

            # 获取最近操作记录
            recent_activities = await self._get_recent_activities(db, portfolio_id)

            # 策略参数（使用真实的数据库值）
            strategy_params = dict(self.STRATEGY_PARAMETERS)

            # 从策略模板获取真实的rebalance_period（优先级：模板JSONB > 模板字段 > 默认值）
            if portfolio.strategy_definition:
                definition = portfolio.strategy_definition
                rebalance_period = definition.default_params.get('rebalance_period_minutes') if definition.default_params else None
                if not rebalance_period:
                    rebalance_period = definition.rebalance_period_minutes
                if not rebalance_period:
                    rebalance_period = 10
            else:
                rebalance_period = portfolio.instance_params.get('rebalance_period_minutes', 10) if portfolio.instance_params else 10

            strategy_params["rebalance_period"] = self._format_rebalance_period(rebalance_period)

            # 从策略实例获取真实的risk_level
            strategy_params["risk_level"] = self._format_risk_level(portfolio.risk_level or "medium")

            parameters = StrategyParameters(**strategy_params)

            # 生成标签
            tags = self._generate_tags(portfolio)

            # 获取持仓信息和计算总未实现盈亏
            holdings_info = []
            total_unrealized_pnl = Decimal("0")

            for holding in portfolio.holdings:
                unrealized_pnl = holding.market_value - holding.cost_basis
                unrealized_pnl_percent = float(unrealized_pnl / holding.cost_basis * 100) if holding.cost_basis > 0 else 0.0

                holdings_info.append({
                    "symbol": holding.symbol,
                    "amount": float(holding.amount),
                    "avg_buy_price": float(holding.avg_buy_price),
                    "current_price": float(holding.current_price),
                    "market_value": float(holding.market_value),
                    "cost_basis": float(holding.cost_basis),
                    "unrealized_pnl": float(unrealized_pnl),
                    "unrealized_pnl_percent": unrealized_pnl_percent,
                })
                total_unrealized_pnl += unrealized_pnl

            # 计算总交易手续费
            from app.models.portfolio import Trade
            from sqlalchemy import func
            fees_stmt = (
                select(func.coalesce(func.sum(Trade.fee), 0))
                .where(Trade.portfolio_id == portfolio_id)
            )
            fees_result = await db.execute(fees_stmt)
            total_fees = fees_result.scalar() or Decimal("0")

            # 计算已实现盈亏（所有SELL交易的realized_pnl总和，用于展示）
            realized_pnl_stmt = (
                select(func.coalesce(func.sum(Trade.realized_pnl), 0))
                .where(Trade.portfolio_id == portfolio_id)
                .where(Trade.trade_type == "SELL")
            )
            realized_pnl_result = await db.execute(realized_pnl_stmt)
            total_realized_pnl = realized_pnl_result.scalar() or Decimal("0")

            # Total P&L应该使用当前总价值 - 初始资金
            # 这已经包含了所有盈亏（已实现+未实现）和所有成本（手续费）
            total_pnl = portfolio.total_value - portfolio.initial_balance
            total_pnl_percent = float(total_pnl / portfolio.initial_balance * 100) if portfolio.initial_balance > 0 else 0.0

            return StrategyDetailResponse(
                id=str(portfolio.id),
                name=portfolio.name,
                description=f"Elite AI squad combining macro, onchain and technical analysis",
                tags=tags,
                performance_metrics=performance_metrics,
                conviction_summary=conviction_summary,
                squad_agents=squad_agents,
                performance_history=performance_history,
                recent_activities=recent_activities,
                parameters=parameters,
                philosophy=portfolio.strategy_definition.philosophy if portfolio.strategy_definition and portfolio.strategy_definition.philosophy else self.STRATEGY_PHILOSOPHY,
                holdings=holdings_info,
                total_unrealized_pnl=float(total_unrealized_pnl),
                total_realized_pnl=float(total_realized_pnl),
                total_pnl=float(total_pnl),
                total_pnl_percent=total_pnl_percent,
                current_balance=float(portfolio.current_balance),
                initial_balance=float(portfolio.initial_balance),
                total_fees=float(total_fees),
            )

        except Exception as e:
            logger.error(f"获取策略详情失败: {e}", exc_info=True)
            raise

    async def _get_conviction_summary(
        self, db: AsyncSession, user_id: int
    ) -> ConvictionSummary:
        """获取最新的Conviction摘要（只包含成功的执行，排除失败的）"""
        # 查询最新的策略执行记录（排除失败的）
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == user_id)
            .where(StrategyExecution.status == "completed")
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        execution = result.scalar_one_or_none()

        if execution and execution.conviction_score is not None:
            score = execution.conviction_score

            # 优先使用LLM生成的总结
            if execution.llm_summary:
                message = execution.llm_summary
            else:
                # 如果没有LLM总结，使用模板消息（fallback）
                if score > 50:
                    message = f"Market conditions are favorable. Our squad maintains a bullish stance with {score:.0f}% conviction. Recommended position: Accumulate on dips."
                elif score > 0:
                    message = f"We're observing mixed signals across our data feeds. Current conviction at {score:.0f}%. Strategy: Hold current positions and monitor for breakout signals."
                elif score > -50:
                    message = f"Market sentiment is cautiously optimistic. Squad conviction: {score:.0f}%. Strategy execution: Gradual position building over next 48 hours."
                else:
                    message = f"Entering a period of uncertainty. Our conviction has moderated to {score:.0f}%. Risk management protocol activated - maintaining defensive positioning."

            return ConvictionSummary(
                score=score,
                message=message,
                updated_at=execution.execution_time,
            )
        else:
            # 默认值
            return ConvictionSummary(
                score=50.0,
                message="Initializing squad analysis. First conviction score will be available after the next execution cycle.",
                updated_at=datetime.now(),
            )

    async def _get_performance_history(
        self, db: AsyncSession, portfolio_id: str
    ) -> PerformanceHistory:
        """获取账户价值历史数据（最近7天,10分钟粒度）"""
        from datetime import datetime, timedelta

        # 获取Portfolio信息(需要initial_btc_amount)
        portfolio_result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = portfolio_result.scalar_one_or_none()

        if not portfolio:
            return PerformanceHistory(
                strategy=[], btc_benchmark=[], eth_benchmark=[], dates=[]
            )

        # 获取最近7天的快照数据
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        stmt = (
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.portfolio_id == portfolio_id,
                PortfolioSnapshot.snapshot_time >= seven_days_ago
            )
            .order_by(PortfolioSnapshot.snapshot_time.asc())
        )
        result = await db.execute(stmt)
        snapshots = result.scalars().all()

        if not snapshots:
            return PerformanceHistory(
                strategy=[], btc_benchmark=[], eth_benchmark=[], dates=[]
            )

        strategy_values = []
        btc_values = []
        eth_values = []
        dates = []

        for snapshot in snapshots:
            # 策略账户价值 (美元)
            portfolio_value = float(snapshot.total_value)
            strategy_values.append(round(portfolio_value, 2))

            # BTC基准价值 (美元)
            # 如果有initial_btc_amount,计算BTC基准价值
            if portfolio.initial_btc_amount and snapshot.btc_price:
                btc_value = float(portfolio.initial_btc_amount) * float(snapshot.btc_price)
                btc_values.append(round(btc_value, 2))
            else:
                btc_values.append(round(portfolio_value, 2))  # 默认与策略相同

            # ETH暂不使用,填充0
            eth_values.append(0)

            # 日期时间格式 (精确到分钟)
            dates.append(snapshot.snapshot_time.strftime("%m/%d %H:%M"))

        return PerformanceHistory(
            strategy=strategy_values,
            btc_benchmark=btc_values,
            eth_benchmark=eth_values,
            dates=dates,
        )

    async def _get_recent_activities(
        self, db: AsyncSession, portfolio_id: str, limit: int = 3
    ) -> List[RecentActivity]:
        """获取最近操作记录 - 基于策略执行记录"""
        # 查询该投资组合的用户ID和连续信号计数
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            return []

        user_id = portfolio.user_id
        bullish_count = portfolio.consecutive_bullish_count or 0
        bearish_count = portfolio.consecutive_bearish_count or 0

        # 查询最近的策略执行记录 - 只查询当前 portfolio 的记录
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.portfolio_id == portfolio_id)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        executions = result.scalars().all()

        activities = []
        for execution in executions:
            # 信号
            signal = execution.signal or "HOLD"

            # 生成动作描述（不包含 conviction）
            if signal == "BUY":
                action = "Increased BTC position"
            elif signal == "SELL":
                action = "Reduced BTC position"
            else:  # HOLD
                action = "Held position"

            # 查询关联的交易结果
            trade_result = await db.execute(
                select(Trade)
                .where(Trade.execution_id == str(execution.id))
                .order_by(Trade.executed_at.desc())
                .limit(1)
            )
            trade = trade_result.scalar_one_or_none()

            # 计算结果
            if trade and trade.realized_pnl_percent:
                result_str = f"{trade.realized_pnl_percent:+.2f}%"
            else:
                result_str = "0.00%"

            # Agent名称
            agent = "Multi-Agent Squad"

            # 根据信号类型决定显示哪个连续计数
            # 只在看涨(BUY)或看跌(SELL)时显示，HOLD不显示
            consecutive_count = None
            if signal == "BUY" and bullish_count > 0:
                consecutive_count = bullish_count
            elif signal == "SELL" and bearish_count > 0:
                consecutive_count = bearish_count

            # 获取各个Agent的贡献详情（只在成功时获取）
            agent_contributions = None
            if execution.status == "completed":
                agent_contributions = await self._get_agent_contributions(db, str(execution.id))

            activity = RecentActivity(
                date=execution.execution_time.replace(tzinfo=timezone.utc).isoformat(),
                signal=signal,
                action=action,
                result=result_str,
                agent=agent,
                execution_id=str(execution.id),  # 始终包含 execution_id
                conviction_score=execution.conviction_score,  # 添加 conviction_score
                consecutive_count=consecutive_count,  # 根据signal类型显示对应的连续计数
                agent_contributions=agent_contributions,  # 添加各Agent的详细信息
                status=execution.status,  # 执行状态
                error_details=execution.error_details,  # 错误详情（如果失败）
            )
            activities.append(activity)

        return activities

    async def _get_agent_contributions(
        self, db: AsyncSession, execution_id: str
    ) -> List[AgentContribution]:
        """获取策略执行中各个Agent的贡献详情"""

        # 获取策略执行记录和关联的策略定义
        from app.models.strategy_execution import StrategyExecution
        stmt_exec = (
            select(StrategyExecution)
            .options(selectinload(StrategyExecution.portfolio).selectinload(Portfolio.strategy_definition))
            .where(StrategyExecution.id == execution_id)
        )
        result_exec = await db.execute(stmt_exec)
        strategy_exec = result_exec.scalar_one_or_none()

        if not strategy_exec:
            return []

        # 首先尝试通过 template_execution_batch_id 精准查询（批量执行的情况）
        agent_execs = []
        if strategy_exec.template_execution_batch_id:
            stmt = (
                select(AgentExecution)
                .where(AgentExecution.template_execution_batch_id == strategy_exec.template_execution_batch_id)
                .order_by(AgentExecution.executed_at.desc())
            )
            result = await db.execute(stmt)
            agent_execs = result.scalars().all()

        # 如果仍然为空，尝试通过 strategy_execution_id 直接查询（单独执行的情况）
        if not agent_execs:
            stmt = (
                select(AgentExecution)
                .where(AgentExecution.strategy_execution_id == execution_id)
                .order_by(AgentExecution.executed_at.desc())
            )
            result = await db.execute(stmt)
            agent_execs = result.scalars().all()

        # Agent显示名称映射（支持所有agents）
        agent_display_names = {
            # Multi-Agent BTC Strategy agents
            "macro": "The Oracle",
            "macro_agent": "The Oracle",
            "ta": "Momentum Scout",
            "ta_agent": "Momentum Scout",
            "onchain": "Data Warden",
            "onchain_agent": "Data Warden",
            # H.I.M.E. Momentum Strategy agents
            "regime_filter": "Regime Filter",
            "ta_momentum": "TA Momentum",
        }

        # 获取策略定义的business_agents列表（用于过滤和排序）
        expected_agents = []
        if strategy_exec.portfolio and strategy_exec.portfolio.strategy_definition:
            expected_agents = strategy_exec.portfolio.strategy_definition.business_agents or []

        contributions = []
        for agent_exec in agent_execs:
            # 只包含策略定义中声明的agents
            if expected_agents and agent_exec.agent_name not in expected_agents:
                continue

            contribution = AgentContribution(
                agent_name=agent_exec.agent_name,
                display_name=agent_display_names.get(agent_exec.agent_name, agent_exec.agent_display_name or agent_exec.agent_name),
                signal=agent_exec.signal,
                confidence=float(agent_exec.confidence),
                score=float(agent_exec.score),
            )
            contributions.append(contribution)

        # 按expected_agents顺序排序（保持策略定义的顺序）
        if expected_agents:
            agent_order = {name: idx for idx, name in enumerate(expected_agents)}
            contributions.sort(key=lambda x: agent_order.get(x.agent_name, 999))
        else:
            # 如果没有expected_agents，按agent_name字母顺序排序
            contributions.sort(key=lambda x: x.agent_name)

        return contributions


    async def get_execution_detail(
        self, db: AsyncSession, execution_id: str
    ) -> StrategyExecutionDetail:
        """获取策略执行详情，包括所有agent调用过程和交易记录"""
        try:
            # 查询策略执行记录
            stmt = select(StrategyExecution).where(StrategyExecution.id == execution_id)
            result = await db.execute(stmt)
            execution = result.scalar_one_or_none()

            if not execution:
                raise ValueError(f"Execution {execution_id} not found")

            # 🆕 通过 template_execution_batch_id 查询关联的 agent_executions
            from app.models.agent_execution import AgentExecution

            agent_executions_list = []
            if execution.template_execution_batch_id:
                agent_stmt = (
                    select(AgentExecution)
                    .where(AgentExecution.template_execution_batch_id == execution.template_execution_batch_id)
                    .order_by(AgentExecution.executed_at)
                )
                agent_result = await db.execute(agent_stmt)
                agent_executions_list = agent_result.scalars().all()

            # 构建agent执行详情列表
            agent_executions = []
            for agent_exec in agent_executions_list:
                agent_detail = AgentExecutionDetail(
                    id=str(agent_exec.id),
                    agent_name=agent_exec.agent_name,
                    agent_display_name=agent_exec.agent_display_name,
                    executed_at=agent_exec.executed_at,
                    execution_duration_ms=agent_exec.execution_duration_ms,
                    status=agent_exec.status,
                    signal=agent_exec.signal,
                    confidence=float(agent_exec.confidence),
                    score=float(agent_exec.score) if agent_exec.score else None,
                    reasoning=agent_exec.reasoning,
                    agent_specific_data=agent_exec.agent_specific_data or {},
                    market_data_snapshot=agent_exec.market_data_snapshot,
                    llm_provider=agent_exec.llm_provider,
                    llm_model=agent_exec.llm_model,
                    llm_prompt=agent_exec.llm_prompt,
                    llm_response=agent_exec.llm_response,
                    tokens_used=agent_exec.tokens_used,
                    llm_cost=float(agent_exec.llm_cost) if agent_exec.llm_cost else None,
                )
                agent_executions.append(agent_detail)

            # 查询该执行产生的交易记录
            from app.models.portfolio import Trade
            trades_stmt = (
                select(Trade)
                .where(Trade.execution_id == execution_id)
                .order_by(Trade.executed_at)
            )
            trades_result = await db.execute(trades_stmt)
            trades = trades_result.scalars().all()

            # 构建交易响应列表
            trade_responses = []
            for trade in trades:
                trade_response = TradeResponse(
                    id=str(trade.id),
                    symbol=trade.symbol,
                    trade_type=trade.trade_type,
                    amount=trade.amount,
                    price=trade.price,
                    total_value=trade.total_value,
                    fee=trade.fee,
                    balance_before=trade.balance_before,
                    balance_after=trade.balance_after,
                    holding_before=trade.holding_before,
                    holding_after=trade.holding_after,
                    realized_pnl=trade.realized_pnl,
                    realized_pnl_percent=trade.realized_pnl_percent,
                    conviction_score=trade.conviction_score,
                    reason=trade.reason,
                    executed_at=trade.executed_at,
                    created_at=trade.created_at,
                )
                trade_responses.append(trade_response)

            # 构建策略执行详情
            execution_detail = StrategyExecutionDetail(
                id=str(execution.id),
                execution_time=execution.execution_time,
                strategy_name=execution.strategy_name,
                status=execution.status,
                market_snapshot=execution.market_snapshot or {},
                conviction_score=execution.conviction_score,
                signal=execution.signal,
                signal_strength=execution.signal_strength,
                position_size=execution.position_size,
                risk_level=execution.risk_level,
                execution_duration_ms=execution.execution_duration_ms,
                error_message=execution.error_message,
                error_details=execution.error_details,
                agent_executions=agent_executions,
                trades=trade_responses,
            )

            return execution_detail

        except Exception as e:
            logger.error(f"获取策略执行详情失败: {e}", exc_info=True)
            raise

    async def update_strategy_settings(
        self,
        db: AsyncSession,
        portfolio_id: str,
        user_id: int,
        rebalance_period_minutes: Optional[int] = None,
        agent_weights: Optional[Dict[str, float]] = None,
        consecutive_signal_threshold: Optional[int] = None,
        acceleration_multiplier_min: Optional[float] = None,
        acceleration_multiplier_max: Optional[float] = None,
        fg_circuit_breaker_threshold: Optional[int] = None,
        fg_position_adjust_threshold: Optional[int] = None,
        buy_threshold: Optional[float] = None,
        partial_sell_threshold: Optional[float] = None,
        full_sell_threshold: Optional[float] = None,
        is_admin: bool = False,
    ) -> dict:
        """
        更新策略参数设置

        Args:
            db: 数据库会话
            portfolio_id: 投资组合ID
            user_id: 用户ID
            rebalance_period_minutes: 策略执行周期（分钟）(可选)
            agent_weights: Agent权重配置 (可选)
            consecutive_signal_threshold: 连续信号阈值 (可选)
            acceleration_multiplier_min: 加速乘数最小值 (可选)
            acceleration_multiplier_max: 加速乘数最大值 (可选)
            fg_circuit_breaker_threshold: Fear & Greed熔断阈值 (可选)
            fg_position_adjust_threshold: Fear & Greed仓位调整阈值 (可选)
            buy_threshold: 买入阈值 (可选)
            partial_sell_threshold: 部分减仓阈值 (可选)
            full_sell_threshold: 全部清仓阈值 (可选)

        Returns:
            dict: 更新结果
        """
        try:
            logger.info(
                f"开始更新策略设置 - portfolio_id={portfolio_id}, user_id={user_id}, is_admin={is_admin}, "
                f"rebalance_period={rebalance_period_minutes}, agent_weights={agent_weights}"
            )

            # 获取投资组合
            # 如果是管理员，可以修改任何策略；否则只能修改自己的策略
            if is_admin:
                result = await db.execute(
                    select(Portfolio).where(Portfolio.id == portfolio_id)
                )
            else:
                result = await db.execute(
                    select(Portfolio).where(
                        Portfolio.id == portfolio_id,
                        Portfolio.user_id == user_id,
                    )
                )
            portfolio = result.scalar_one_or_none()

            if not portfolio:
                raise ValueError(f"投资组合不存在或无权限访问: {portfolio_id}")

            # 获取当前instance_params
            current_params = portfolio.instance_params or {}

            # 记录更新前的值
            old_period = current_params.get('rebalance_period_minutes')
            old_weights = current_params.get('agent_weights')

            updated_fields = []

            # 更新执行周期（如果提供）
            if rebalance_period_minutes is not None:
                current_params['rebalance_period_minutes'] = rebalance_period_minutes
                updated_fields.append(f"执行周期: {old_period} -> {rebalance_period_minutes}分钟")

            # 更新Agent权重（如果提供）
            if agent_weights is not None:
                current_params['agent_weights'] = agent_weights
                updated_fields.append(f"Agent权重: {old_weights} -> {agent_weights}")

            # 更新连续信号配置（如果提供）
            if consecutive_signal_threshold is not None:
                current_params['consecutive_signal_threshold'] = consecutive_signal_threshold
                updated_fields.append(f"连续信号阈值: {consecutive_signal_threshold}")

            if acceleration_multiplier_min is not None:
                current_params['acceleration_multiplier_min'] = acceleration_multiplier_min
                updated_fields.append(f"加速乘数最小值: {acceleration_multiplier_min}")

            if acceleration_multiplier_max is not None:
                current_params['acceleration_multiplier_max'] = acceleration_multiplier_max
                updated_fields.append(f"加速乘数最大值: {acceleration_multiplier_max}")

            # 更新交易阈值配置（如果提供）
            if fg_circuit_breaker_threshold is not None:
                current_params['fg_circuit_breaker_threshold'] = fg_circuit_breaker_threshold
                updated_fields.append(f"FG熔断阈值: {fg_circuit_breaker_threshold}")

            if fg_position_adjust_threshold is not None:
                current_params['fg_position_adjust_threshold'] = fg_position_adjust_threshold
                updated_fields.append(f"FG仓位调整阈值: {fg_position_adjust_threshold}")

            if buy_threshold is not None:
                current_params['buy_threshold'] = buy_threshold
                updated_fields.append(f"买入阈值: {buy_threshold}")

            if partial_sell_threshold is not None:
                current_params['partial_sell_threshold'] = partial_sell_threshold
                updated_fields.append(f"部分减仓阈值: {partial_sell_threshold}")

            if full_sell_threshold is not None:
                current_params['full_sell_threshold'] = full_sell_threshold
                updated_fields.append(f"全部清仓阈值: {full_sell_threshold}")

            # 更新portfolio的instance_params
            portfolio.instance_params = current_params

            portfolio.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(portfolio)

            logger.info(
                f"更新策略设置成功 - 组合: {portfolio.instance_name or portfolio.name}, "
                f"更新内容: {', '.join(updated_fields) if updated_fields else '无变更'}"
            )

            # 如果策略是活跃的且执行周期有更新,更新调度任务
            if portfolio.is_active and rebalance_period_minutes is not None:
                # 动态导入以避免循环依赖
                from app.services.strategy.scheduler import strategy_scheduler

                strategy_scheduler.update_portfolio_job(
                    portfolio_id=str(portfolio.id),
                    portfolio_name=portfolio.instance_name or portfolio.name or "Unknown",
                    period_minutes=rebalance_period_minutes,
                )
                logger.info(f"已更新活跃策略的调度任务: {portfolio.instance_name or portfolio.name}")

            # 获取更新后的参数
            updated_params = portfolio.instance_params or {}

            return {
                "success": True,
                "message": "策略设置已更新",
                "portfolio_id": str(portfolio.id),
                "rebalance_period_minutes": updated_params.get('rebalance_period_minutes'),
                "agent_weights": updated_params.get('agent_weights'),
                "consecutive_signal_threshold": updated_params.get('consecutive_signal_threshold'),
                "acceleration_multiplier_min": updated_params.get('acceleration_multiplier_min'),
                "acceleration_multiplier_max": updated_params.get('acceleration_multiplier_max'),
                "fg_circuit_breaker_threshold": updated_params.get('fg_circuit_breaker_threshold'),
                "fg_position_adjust_threshold": updated_params.get('fg_position_adjust_threshold'),
                "buy_threshold": updated_params.get('buy_threshold'),
                "partial_sell_threshold": updated_params.get('partial_sell_threshold'),
                "full_sell_threshold": updated_params.get('full_sell_threshold'),
                "updated_fields": updated_fields,
            }

        except ValueError as e:
            raise
        except Exception as e:
            logger.error(f"更新策略设置失败: {e}", exc_info=True)
            raise

    async def get_strategy_executions(
        self, db: AsyncSession, portfolio_id: str, page: int = 1, page_size: int = 50
    ) -> dict:
        """
        获取策略执行历史列表（分页）

        Args:
            db: 数据库会话
            portfolio_id: 投资组合ID
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            dict: 包含执行历史列表和分页信息
        """
        try:
            # 查询该投资组合的用户ID和连续信号计数
            result = await db.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            portfolio = result.scalar_one_or_none()

            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")

            user_id = portfolio.user_id
            bullish_count = portfolio.consecutive_bullish_count or 0
            bearish_count = portfolio.consecutive_bearish_count or 0

            # 计算偏移量
            offset = (page - 1) * page_size

            # 查询总数 - 只查询当前 portfolio 的记录
            count_stmt = (
                select(func.count(StrategyExecution.id))
                .where(StrategyExecution.portfolio_id == portfolio_id)
            )
            total_result = await db.execute(count_stmt)
            total = total_result.scalar_one()

            # 查询策略执行记录（分页） - 只查询当前 portfolio 的记录
            stmt = (
                select(StrategyExecution)
                .where(StrategyExecution.portfolio_id == portfolio_id)
                .order_by(StrategyExecution.execution_time.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await db.execute(stmt)
            executions = result.scalars().all()

            # 转换为响应格式
            items = []
            for exe in executions:
                # 获取对应的交易（如果有）
                trade_stmt = (
                    select(Trade)
                    .where(Trade.execution_id == exe.id)
                    .where(Trade.portfolio_id == portfolio_id)
                )
                trade_result = await db.execute(trade_stmt)
                trade = trade_result.scalar_one_or_none()

                # 构建活动描述
                action = "No action taken"
                result_str = "--"

                if trade:
                    if trade.trade_type == "BUY":
                        action = f"Bought {float(trade.amount):.8f} {trade.symbol}"
                    elif trade.trade_type == "SELL":
                        action = f"Sold {float(trade.amount):.8f} {trade.symbol}"

                    # 计算结果
                    if trade.realized_pnl:
                        result_str = f"+${float(trade.realized_pnl):.2f}" if float(trade.realized_pnl) >= 0 else f"${float(trade.realized_pnl):.2f}"
                    elif trade.trade_type == "BUY":
                        result_str = f"${float(trade.total_value):.2f}"

                # 根据信号类型决定显示哪个连续计数
                # 只在看涨(BUY)或看跌(SELL)时显示，HOLD不显示
                signal = exe.signal or "HOLD"
                consecutive_count = None
                if signal == "BUY" and bullish_count > 0:
                    consecutive_count = bullish_count
                elif signal == "SELL" and bearish_count > 0:
                    consecutive_count = bearish_count

                items.append({
                    "execution_id": str(exe.id),
                    "date": exe.execution_time.replace(tzinfo=timezone.utc).isoformat(),  # 标记为UTC时区
                    "signal": signal,
                    "action": action,
                    "result": result_str,
                    "agent": "Squad",  # 可以根据需要调整
                    "conviction_score": exe.conviction_score,
                    "signal_strength": exe.signal_strength,
                    "consecutive_count": consecutive_count,
                })

            # 计算分页信息
            total_pages = (total + page_size - 1) // page_size

            return {
                "items": items,
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }

        except ValueError as e:
            raise
        except Exception as e:
            logger.error(f"获取策略执行历史失败: {e}", exc_info=True)
            raise

    async def get_portfolio_trades(
        self, db: AsyncSession, portfolio_id: str, page: int = 1, page_size: int = 10
    ) -> dict:
        """
        获取投资组合的交易记录（分页）

        Args:
            db: 数据库会话
            portfolio_id: Portfolio ID
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            分页的交易记录列表
        """
        try:
            from app.models.portfolio import Trade, Portfolio
            from app.schemas.strategy import TradeResponse
            from sqlalchemy import func

            # 验证portfolio存在
            portfolio_result = await db.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            portfolio = portfolio_result.scalar_one_or_none()
            if not portfolio:
                raise ValueError(f"Portfolio not found: {portfolio_id}")

            # 计算总数
            count_stmt = select(func.count()).select_from(Trade).where(
                Trade.portfolio_id == portfolio_id
            )
            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0

            # 计算总页数
            total_pages = (total + page_size - 1) // page_size if total > 0 else 1

            # 获取分页数据
            offset = (page - 1) * page_size
            trades_stmt = (
                select(Trade)
                .where(Trade.portfolio_id == portfolio_id)
                .order_by(Trade.executed_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            trades_result = await db.execute(trades_stmt)
            trades = trades_result.scalars().all()

            # 构建响应
            trade_responses = []
            for trade in trades:
                trade_response = TradeResponse(
                    id=str(trade.id),
                    symbol=trade.symbol,
                    trade_type=trade.trade_type.upper(),  # 转换为大写
                    amount=trade.amount,
                    price=trade.price,
                    total_value=trade.total_value,
                    fee=trade.fee,
                    balance_before=trade.balance_before,
                    balance_after=trade.balance_after,
                    holding_before=trade.holding_before,
                    holding_after=trade.holding_after,
                    realized_pnl=trade.realized_pnl,
                    realized_pnl_percent=trade.realized_pnl_percent,
                    conviction_score=trade.conviction_score,
                    reason=trade.reason,
                    executed_at=trade.executed_at,
                    created_at=trade.created_at,
                )
                trade_responses.append(trade_response)

            return {
                "items": trade_responses,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }

        except ValueError as e:
            raise
        except Exception as e:
            logger.error(f"获取交易记录失败: {e}", exc_info=True)
            raise

    async def deploy_strategy(
        self,
        db: AsyncSession,
        portfolio_id: str,
        user_id: int,
        initial_balance: float,
    ) -> Dict[str, Any]:
        """
        部署资金到策略（克隆策略模板并激活）

        Args:
            db: 数据库会话
            portfolio_id: 策略模板的 Portfolio UUID
            user_id: 用户ID
            initial_balance: 初始资金

        Returns:
            部署结果信息
        """
        try:
            # 1. 查询策略模板（Portfolio）
            stmt = select(Portfolio).where(Portfolio.id == portfolio_id)
            result = await db.execute(stmt)
            template_portfolio = result.scalar_one_or_none()

            if not template_portfolio:
                raise ValueError(f"Strategy template not found: {portfolio_id}")

            # 2. 验证金额（最小100 USDT）
            if initial_balance < 100:
                raise ValueError(f"Minimum deposit amount is 100 USDT")

            # 3. 检查用户是否已经激活过这个策略
            check_stmt = select(Portfolio).where(
                Portfolio.user_id == user_id,
                Portfolio.strategy_name == template_portfolio.instance_name,
                Portfolio.is_active == True
            )
            check_result = await db.execute(check_stmt)
            existing = check_result.scalar_one_or_none()

            if existing:
                raise ValueError(f"You have already activated this strategy")

            # 4. 克隆策略模板创建新的 Portfolio 实例
            import uuid

            # 从模板复制instance_params
            template_params = template_portfolio.instance_params or {}

            new_portfolio = Portfolio(
                id=uuid.uuid4(),
                user_id=user_id,
                name=template_portfolio.name,
                instance_name=template_portfolio.instance_name,
                instance_description=template_portfolio.instance_description,
                strategy_definition_id=template_portfolio.strategy_definition_id,
                instance_params=template_params.copy(),
                initial_balance=Decimal(str(initial_balance)),
                current_balance=Decimal(str(initial_balance)),
                total_value=Decimal(str(initial_balance)),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(new_portfolio)
            await db.commit()
            await db.refresh(new_portfolio)

            # 5. 添加到调度器（启动定时执行）
            try:
                from app.services.strategy.scheduler import strategy_scheduler
                rebalance_period = new_portfolio.instance_params.get('rebalance_period_minutes', 10) if new_portfolio.instance_params else 10
                await strategy_scheduler.add_portfolio_task(new_portfolio.id, rebalance_period)
                logger.info(f"[Deploy] 已将策略 {new_portfolio.id} 添加到调度器")
            except Exception as e:
                logger.warning(f"[Deploy] 添加调度任务失败（非致命错误）: {e}")

            logger.info(
                f"[Deploy] 成功部署策略: template_id={portfolio_id}, "
                f"new_portfolio_id={new_portfolio.id}, user_id={user_id}, initial_balance={initial_balance}"
            )

            return {
                "success": True,
                "message": f"Successfully deployed ${initial_balance} to strategy",
                "portfolio_id": str(new_portfolio.id),
                "amount": initial_balance,
                "is_active": True,
                "deployed_at": new_portfolio.created_at.isoformat(),
            }

        except ValueError as e:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"部署策略失败: {e}", exc_info=True)
            raise


# 创建全局实例
marketplace_service = MarketplaceService()
