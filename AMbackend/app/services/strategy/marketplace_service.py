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
    StrategyParameters,
    PerformanceMetrics,
    StrategyExecutionDetail,
    AgentExecutionDetail,
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
    ) -> StrategyMarketplaceListResponse:
        """获取策略市场列表"""
        try:
            # 查询所有活跃的投资组合
            stmt = select(Portfolio).where(Portfolio.is_active == True)

            # 如果指定用户，只返回该用户的组合
            if user_id:
                stmt = stmt.where(Portfolio.user_id == user_id)

            result = await db.execute(stmt)
            portfolios = result.scalars().all()

            strategies = []
            for portfolio in portfolios:
                # 计算天数
                days = (datetime.now() - portfolio.created_at).days
                if days < 1:
                    days = 1

                # 计算年化收益
                annualized_return = self._calculate_annualized_return(
                    portfolio.initial_balance, portfolio.total_value, days
                )

                # 映射风险等级
                mapped_risk_level = self._map_risk_level(portfolio.max_drawdown)

                # 风险等级过滤
                if risk_level and mapped_risk_level != risk_level:
                    continue

                # 获取历史数据
                history = await self._get_portfolio_history(db, portfolio.id)

                # 生成标签
                tags = self._generate_tags(portfolio)

                strategy_card = StrategyMarketplaceCard(
                    id=str(portfolio.id),
                    name=portfolio.name,
                    subtitle=portfolio.strategy_name or "Multi-Agent Strategy",
                    description=f"Elite AI squad combining macro, onchain and technical analysis",
                    tags=tags,
                    annualized_return=annualized_return,
                    max_drawdown=portfolio.max_drawdown,
                    sharpe_ratio=portfolio.sharpe_ratio or 0.0,
                    pool_size=float(portfolio.total_value),
                    squad_size=3,  # 固定3个Agent
                    risk_level=mapped_risk_level,
                    history=history,
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
            # 查询投资组合
            stmt = (
                select(Portfolio)
                .options(selectinload(Portfolio.holdings))
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

            # Squad agents（固定配置）
            squad_agents = [SquadAgent(**agent) for agent in self.SQUAD_AGENTS]

            # 获取性能历史数据
            performance_history = await self._get_performance_history(db, portfolio_id)

            # 获取最近操作记录
            recent_activities = await self._get_recent_activities(db, portfolio_id)

            # 策略参数（使用真实的重平衡周期值）
            strategy_params = dict(self.STRATEGY_PARAMETERS)
            strategy_params["rebalance_period"] = self._format_rebalance_period(
                portfolio.rebalance_period_minutes
            )
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
                philosophy=self.STRATEGY_PHILOSOPHY,
                holdings=holdings_info,
                total_unrealized_pnl=float(total_unrealized_pnl),
                current_balance=float(portfolio.current_balance),
            )

        except Exception as e:
            logger.error(f"获取策略详情失败: {e}", exc_info=True)
            raise

    async def _get_conviction_summary(
        self, db: AsyncSession, user_id: int
    ) -> ConvictionSummary:
        """获取最新的Conviction摘要"""
        # 查询最新的策略执行记录
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
            # 生成简单的摘要消息
            score = execution.conviction_score
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
        """获取性能历史数据（vs BTC/ETH）"""
        # 获取快照数据
        stmt = (
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioSnapshot.snapshot_time.asc())
            .limit(16)
        )
        result = await db.execute(stmt)
        snapshots = result.scalars().all()

        if not snapshots:
            return PerformanceHistory(
                strategy=[], btc_benchmark=[], eth_benchmark=[], dates=[]
            )

        # 归一化数据
        initial_portfolio_value = float(snapshots[0].total_value)
        initial_btc_price = float(snapshots[0].btc_price) if snapshots[0].btc_price else 1.0
        initial_eth_price = float(snapshots[0].eth_price) if snapshots[0].eth_price else 1.0

        strategy_values = []
        btc_values = []
        eth_values = []
        dates = []

        for snapshot in snapshots:
            # Portfolio归一化
            portfolio_normalized = (
                float(snapshot.total_value) / initial_portfolio_value
            ) * 100

            # BTC归一化
            btc_price = float(snapshot.btc_price) if snapshot.btc_price else initial_btc_price
            btc_normalized = (btc_price / initial_btc_price) * 100

            # ETH归一化
            eth_price = float(snapshot.eth_price) if snapshot.eth_price else initial_eth_price
            eth_normalized = (eth_price / initial_eth_price) * 100

            strategy_values.append(round(portfolio_normalized, 2))
            btc_values.append(round(btc_normalized, 2))
            eth_values.append(round(eth_normalized, 2))
            dates.append(snapshot.snapshot_time.strftime("%Y-%m"))

        return PerformanceHistory(
            strategy=strategy_values,
            btc_benchmark=btc_values,
            eth_benchmark=eth_values,
            dates=dates,
        )

    async def _get_recent_activities(
        self, db: AsyncSession, portfolio_id: str, limit: int = 5
    ) -> List[RecentActivity]:
        """获取最近操作记录 - 基于策略执行记录"""
        # 查询该投资组合的用户ID
        result = await db.execute(
            select(Portfolio.user_id).where(Portfolio.id == portfolio_id)
        )
        user_id = result.scalar_one_or_none()

        if not user_id:
            return []

        # 查询最近的策略执行记录
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == user_id)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        executions = result.scalars().all()

        activities = []
        for execution in executions:
            # 信号
            signal = execution.signal or "HOLD"

            # 生成动作描述
            if signal == "BUY":
                action = f"Increased BTC position (conviction: {execution.conviction_score:.1f}%)"
            elif signal == "SELL":
                action = f"Reduced BTC position (conviction: {execution.conviction_score:.1f}%)"
            else:  # HOLD
                action = f"Held position (conviction: {execution.conviction_score:.1f}%)"

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

            activity = RecentActivity(
                date=execution.execution_time.replace(tzinfo=timezone.utc).isoformat(),
                signal=signal,
                action=action,
                result=result_str,
                agent=agent,
                execution_id=str(execution.id),  # 始终包含 execution_id
            )
            activities.append(activity)

        return activities


    async def get_execution_detail(
        self, db: AsyncSession, execution_id: str
    ) -> StrategyExecutionDetail:
        """获取策略执行详情，包括所有agent调用过程"""
        try:
            # 查询策略执行记录
            stmt = (
                select(StrategyExecution)
                .options(selectinload(StrategyExecution.agent_executions))
                .where(StrategyExecution.id == execution_id)
            )
            result = await db.execute(stmt)
            execution = result.scalar_one_or_none()

            if not execution:
                raise ValueError(f"Execution {execution_id} not found")

            # 构建agent执行详情列表
            agent_executions = []
            for agent_exec in execution.agent_executions:
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
                agent_executions=agent_executions,
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
        rebalance_period_minutes: int,
    ) -> dict:
        """
        更新策略参数设置

        Args:
            db: 数据库会话
            portfolio_id: 投资组合ID
            user_id: 用户ID
            rebalance_period_minutes: 策略执行周期（分钟）

        Returns:
            dict: 更新结果
        """
        try:
            # 获取投资组合
            result = await db.execute(
                select(Portfolio).where(
                    Portfolio.id == portfolio_id,
                    Portfolio.user_id == user_id,
                )
            )
            portfolio = result.scalar_one_or_none()

            if not portfolio:
                raise ValueError(f"投资组合不存在或无权限访问: {portfolio_id}")

            # 保存旧周期值
            old_period = portfolio.rebalance_period_minutes

            # 更新策略参数
            portfolio.rebalance_period_minutes = rebalance_period_minutes
            portfolio.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(portfolio)

            logger.info(
                f"更新策略设置成功 - 组合: {portfolio.name}, "
                f"执行周期: {old_period} -> {rebalance_period_minutes} 分钟"
            )

            # 如果策略是活跃的,更新调度任务
            if portfolio.is_active:
                # 动态导入以避免循环依赖
                from app.services.strategy.scheduler import strategy_scheduler

                strategy_scheduler.update_portfolio_job(
                    portfolio_id=str(portfolio.id),
                    portfolio_name=portfolio.name,
                    period_minutes=rebalance_period_minutes,
                )
                logger.info(f"已更新活跃策略的调度任务: {portfolio.name}")

            return {
                "success": True,
                "message": f"Strategy settings updated successfully",
                "portfolio_id": str(portfolio.id),
                "rebalance_period_minutes": rebalance_period_minutes,
            }

        except ValueError as e:
            raise
        except Exception as e:
            logger.error(f"更新策略设置失败: {e}", exc_info=True)
            raise


# 创建全局实例
marketplace_service = MarketplaceService()
