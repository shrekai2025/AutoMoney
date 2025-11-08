"""Strategy Scheduler - 策略调度器

定时任务:
1. 策略执行 Job (独立周期,每个策略可配置)
2. 市场数据采集 Job (每30秒)
3. 组合快照 Job (每天0点)
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from decimal import Decimal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import User, Portfolio, PortfolioSnapshot
from app.services.strategy.strategy_orchestrator import strategy_orchestrator
from app.services.trading.portfolio_service import portfolio_service
from app.services.market.real_market_data import real_market_data_service
from app.services.strategy.real_agent_executor import real_agent_executor
from app.services.indicators.calculator import IndicatorCalculator
from app.services.data_collectors.manager import data_manager

logger = logging.getLogger(__name__)


class StrategyScheduler:
    """
    策略调度器

    管理所有定时任务,支持每个策略独立周期
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.engine = None
        self.SessionLocal = None

    async def initialize(self):
        """初始化数据库连接"""
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
        )

        self.SessionLocal = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("策略调度器数据库连接已初始化")

    async def start(self):
        """启动调度器"""
        await self.initialize()

        # 添加全局定时任务
        self._add_global_jobs()

        # 为所有活跃策略添加独立任务
        await self._add_all_portfolio_jobs()

        # 启动调度器
        self.scheduler.start()
        logger.info("策略调度器已启动")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("策略调度器已停止")

    def _add_global_jobs(self):
        """添加全局定时任务"""

        # Job 1: 市场数据采集 (每30秒)
        self.scheduler.add_job(
            self.collect_market_data_job,
            trigger=IntervalTrigger(seconds=30),
            id="market_data_collection",
            name="市场数据采集",
            replace_existing=True,
            max_instances=1,
        )

        # Job 2: 批量策略执行 (每10分钟) - 成本优化版
        self.scheduler.add_job(
            self.batch_execute_strategies_job,
            trigger=IntervalTrigger(minutes=10),
            id="batch_strategies",
            name="批量策略执行（共享Agent分析）",
            replace_existing=True,
            max_instances=1,
        )

        # Job 3: 组合快照 (每10分钟)
        self.scheduler.add_job(
            self.create_portfolio_snapshots_job,
            trigger=IntervalTrigger(minutes=10),
            id="portfolio_snapshots",
            name="组合快照",
            replace_existing=True,
            max_instances=1,
        )

        logger.info("全局定时任务已添加（包括批量执行模式）")

    async def _add_all_portfolio_jobs(self):
        """
        为所有活跃策略添加统一的批量执行任务

        优化说明：
        - 所有Portfolio共享同一个定时任务（而不是每个Portfolio一个任务）
        - 每次执行时，先运行一次Agent分析，然后所有Portfolio共享这个分析结果
        - 大幅降低LLM调用成本（从 N次 降低到 1次）
        """
        try:
            print(f"[Scheduler] 开始添加批量策略执行任务...")

            # 注意：这里不再为每个Portfolio单独创建任务
            # 而是使用统一的批量执行任务（在 _add_global_jobs 中已添加）

            async with self.SessionLocal() as db:
                result = await db.execute(
                    select(Portfolio).where(Portfolio.is_active == True)
                )
                portfolios = result.scalars().all()
                print(f"[Scheduler] 找到 {len(portfolios)} 个活跃策略，将使用批量执行模式")

                logger.info(f"批量执行模式：{len(portfolios)} 个Portfolio将共享Agent分析结果")
                print(f"[Scheduler] ✓ 批量执行模式已启用，成本优化：Agent调用从 {len(portfolios)}次/周期 降至 1次/周期")

        except Exception as e:
            logger.error(f"检查活跃策略失败: {e}", exc_info=True)
            print(f"[Scheduler] ❌ 检查活跃策略失败: {e}")

    def add_portfolio_job(
        self, portfolio_id: str, portfolio_name: str, period_minutes: int
    ):
        """
        为单个策略添加独立的定时任务

        Args:
            portfolio_id: 策略ID
            portfolio_name: 策略名称
            period_minutes: 执行周期(分钟)
        """
        job_id = f"portfolio_{portfolio_id}"

        try:
            # 如果任务已存在,先移除
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

            # 添加新任务
            self.scheduler.add_job(
                self.execute_single_portfolio,
                trigger=IntervalTrigger(minutes=period_minutes),
                id=job_id,
                name=f"策略执行: {portfolio_name}",
                args=[portfolio_id],
                replace_existing=True,
                max_instances=1,  # 防止并发执行
            )

            logger.info(
                f"已添加策略任务: {portfolio_name} (ID: {portfolio_id}, "
                f"周期: {period_minutes}分钟)"
            )
            print(
                f"[Scheduler]   ✓ 添加任务: {portfolio_name} (周期: {period_minutes}分钟)"
            )

        except Exception as e:
            logger.error(
                f"添加策略任务失败: {portfolio_name} (ID: {portfolio_id}) - {e}",
                exc_info=True,
            )
            print(
                f"[Scheduler]   ❌ 添加任务失败: {portfolio_name} - {e}"
            )

    def remove_portfolio_job(self, portfolio_id: str):
        """
        移除策略的定时任务

        Args:
            portfolio_id: 策略ID
        """
        job_id = f"portfolio_{portfolio_id}"

        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"已移除策略任务: {portfolio_id}")
            else:
                logger.warning(f"策略任务不存在: {portfolio_id}")

        except Exception as e:
            logger.error(f"移除策略任务失败: {portfolio_id} - {e}", exc_info=True)

    def update_portfolio_job(
        self, portfolio_id: str, portfolio_name: str, period_minutes: int
    ):
        """
        更新策略的定时任务周期

        Args:
            portfolio_id: 策略ID
            portfolio_name: 策略名称
            period_minutes: 新的执行周期(分钟)
        """
        logger.info(
            f"更新策略任务: {portfolio_name} (ID: {portfolio_id}, "
            f"新周期: {period_minutes}分钟)"
        )

        # 移除旧任务并添加新任务
        self.remove_portfolio_job(portfolio_id)
        self.add_portfolio_job(portfolio_id, portfolio_name, period_minutes)

    async def execute_single_portfolio(self, portfolio_id: str):
        """
        执行单个策略

        Args:
            portfolio_id: 策略ID
        """
        logger.info(f"开始执行策略: {portfolio_id}")

        try:
            async with self.SessionLocal() as db:
                # 1. 获取投资组合
                result = await db.execute(
                    select(Portfolio).where(
                        Portfolio.id == portfolio_id, Portfolio.is_active == True
                    )
                )
                portfolio = result.scalar_one_or_none()

                if not portfolio:
                    logger.warning(f"策略不存在或已停用: {portfolio_id}")
                    # 移除任务
                    self.remove_portfolio_job(portfolio_id)
                    return

                # 2. 采集市场数据
                market_data = await self._fetch_market_data()

                # 3. 执行策略
                try:
                    logger.info(
                        f"为组合执行策略: {portfolio.name} (ID: {portfolio.id})"
                    )

                    # 执行策略（让 orchestrator 自己执行 agents 并记录）
                    execution = await strategy_orchestrator.execute_strategy(
                        db=db,
                        user_id=portfolio.user_id,
                        portfolio_id=str(portfolio.id),
                        market_data=market_data,
                        agent_outputs=None,  # 让 orchestrator 自己执行 agents
                    )

                    # 4. 更新 last_execution_time
                    portfolio.last_execution_time = datetime.utcnow()
                    await db.commit()

                    logger.info(
                        f"策略执行完成 - 组合: {portfolio.name}, "
                        f"信号: {execution.signal}, "
                        f"状态: {execution.status}"
                    )

                except Exception as e:
                    logger.error(
                        f"组合策略执行失败: {portfolio.name} - {e}", exc_info=True
                    )

        except Exception as e:
            logger.error(f"策略执行 Job 失败: {portfolio_id} - {e}", exc_info=True)

    async def batch_execute_strategies_job(self):
        """
        批量执行所有活跃策略 - 成本优化版本

        工作流程:
        1. 获取所有活跃Portfolio
        2. 执行一次Agent分析（所有Portfolio共享）
        3. 为每个Portfolio应用分析结果并执行交易

        成本优化:
        - LLM调用次数: 从 N次 降至 1次 (N = Portfolio数量)
        - 适用场景: 所有Portfolio使用相同的策略配置
        """
        logger.info("开始批量执行策略（共享Agent分析）")

        try:
            async with self.SessionLocal() as db:
                # 1. 获取所有活跃的Portfolio
                result = await db.execute(
                    select(Portfolio)
                    .options(selectinload(Portfolio.holdings))
                    .where(Portfolio.is_active == True)
                )
                portfolios = result.scalars().all()

                if not portfolios:
                    logger.info("没有活跃的Portfolio，跳过批量执行")
                    return

                logger.info(f"找到 {len(portfolios)} 个活跃Portfolio，开始共享执行")

                # 2. 采集市场数据（所有Portfolio共享）
                market_data = await self._fetch_market_data()

                # 3. 执行一次Agent分析（关键优化点！）
                logger.info("执行Agent分析（所有Portfolio共享此结果）")
                from app.services.strategy.real_agent_executor import RealAgentExecutor
                agent_executor = RealAgentExecutor()

                # 使用第一个Portfolio的配置执行Agent（因为所有Portfolio配置相同）
                first_portfolio = portfolios[0]
                agent_outputs, agent_errors = await agent_executor.execute_all_agents(
                    market_data=market_data,
                    db=db,
                    user_id=first_portfolio.user_id,
                )

                logger.info(f"Agent分析完成，开始为 {len(portfolios)} 个Portfolio应用结果")

                # 4. 为每个Portfolio应用Agent分析结果
                for portfolio in portfolios:
                    try:
                        logger.info(f"为Portfolio执行策略: {portfolio.name} (ID: {portfolio.id})")

                        # 使用共享的agent_outputs执行策略
                        execution = await strategy_orchestrator.execute_strategy(
                            db=db,
                            user_id=portfolio.user_id,
                            portfolio_id=str(portfolio.id),
                            market_data=market_data,
                            agent_outputs=agent_outputs,  # 使用共享的分析结果
                        )

                        # 更新执行时间
                        portfolio.last_execution_time = datetime.utcnow()
                        await db.commit()

                        logger.info(
                            f"Portfolio执行完成 - {portfolio.name}, "
                            f"信号: {execution.signal}, 状态: {execution.status}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Portfolio执行失败: {portfolio.name} - {e}",
                            exc_info=True
                        )
                        await db.rollback()

                logger.info(
                    f"批量执行完成 - 共 {len(portfolios)} 个Portfolio, "
                    f"Agent调用: 1次 (节省 {len(portfolios)-1} 次LLM调用)"
                )

        except Exception as e:
            logger.error(f"批量策略执行Job失败: {e}", exc_info=True)

    async def collect_market_data_job(self):
        """
        市场数据采集 Job

        定期更新所有组合的市场价值
        """
        logger.info("开始采集市场数据")

        try:
            async with self.SessionLocal() as db:
                # 1. 采集市场数据
                market_data = await self._fetch_market_data()

                btc_price = Decimal(str(market_data.get("btc_price", 0)))
                if btc_price == 0:
                    logger.warning("BTC 价格为 0，跳过组合价值更新")
                    return

                # 2. 获取所有活跃组合 (with eager loading)
                result = await db.execute(
                    select(Portfolio)
                    .options(selectinload(Portfolio.holdings))
                    .where(Portfolio.is_active == True)
                )
                portfolios = result.scalars().all()

                # 3. 更新组合价值
                for portfolio in portfolios:
                    try:
                        await portfolio_service.update_portfolio_value(
                            db=db,
                            portfolio=portfolio,
                            current_btc_price=btc_price,
                        )

                    except Exception as e:
                        logger.error(f"更新组合价值失败: {portfolio.name} - {e}")

                logger.info(
                    f"市场数据采集完成 - BTC: ${btc_price}, "
                    f"更新了 {len(portfolios)} 个组合"
                )

        except Exception as e:
            logger.error(f"市场数据采集 Job 失败: {e}", exc_info=True)

    async def create_portfolio_snapshots_job(self):
        """
        组合快照 Job

        每天创建所有组合的快照
        """
        logger.info("开始创建组合快照")

        try:
            async with self.SessionLocal() as db:
                # 1. 采集市场数据
                market_data = await self._fetch_market_data()

                btc_price = Decimal(str(market_data.get("btc_price", 0)))
                snapshot_time = datetime.utcnow()

                # 2. 获取所有活跃组合 (with eager loading)
                result = await db.execute(
                    select(Portfolio)
                    .options(selectinload(Portfolio.holdings))
                    .where(Portfolio.is_active == True)
                )
                portfolios = result.scalars().all()

                # 3. 为每个组合创建快照
                for portfolio in portfolios:
                    try:
                        # 如果是第一次快照,计算并保存 initial_btc_amount
                        if portfolio.initial_btc_amount is None and btc_price > 0:
                            portfolio.initial_btc_amount = portfolio.initial_balance / btc_price
                            logger.info(
                                f"初始化 BTC 基准: {portfolio.name}, "
                                f"初始余额: ${portfolio.initial_balance}, "
                                f"BTC 价格: ${btc_price}, "
                                f"BTC 数量: {portfolio.initial_btc_amount}"
                            )

                        # 计算持仓价值
                        holdings_value = Decimal("0")
                        holdings_data = {}

                        for holding in portfolio.holdings:
                            holdings_value += holding.market_value
                            holdings_data[holding.symbol] = {
                                "amount": float(holding.amount),
                                "avg_buy_price": float(holding.avg_buy_price),
                                "current_price": float(holding.current_price),
                                "market_value": float(holding.market_value),
                                "unrealized_pnl": float(holding.unrealized_pnl),
                            }

                        # 创建快照
                        snapshot = PortfolioSnapshot(
                            portfolio_id=portfolio.id,
                            snapshot_time=snapshot_time,
                            total_value=portfolio.total_value,
                            balance=portfolio.current_balance,
                            holdings_value=holdings_value,
                            total_pnl=portfolio.total_pnl,
                            total_pnl_percent=portfolio.total_pnl_percent,
                            btc_price=btc_price,
                            holdings=holdings_data,
                        )

                        db.add(snapshot)

                        logger.info(
                            f"创建组合快照: {portfolio.name}, "
                            f"总价值: ${portfolio.total_value}"
                        )

                    except Exception as e:
                        logger.error(f"创建组合快照失败: {portfolio.name} - {e}")

                await db.commit()

                logger.info(f"组合快照创建完成 - 共 {len(portfolios)} 个组合")

        except Exception as e:
            logger.error(f"组合快照 Job 失败: {e}", exc_info=True)

    async def _fetch_market_data(self) -> dict:
        """
        采集真实市场数据

        使用真实的市场数据 API（CoinGecko, Binance, Alternative.me, FRED）
        """
        try:
            # 使用真实市场数据服务
            market_snapshot = (
                await real_market_data_service.get_complete_market_snapshot()
            )

            # 添加技术指标
            # 收集 OHLCV 数据用于技术指标计算
            all_data = await data_manager.collect_all()
            if hasattr(all_data, "btc_ohlcv") and all_data.btc_ohlcv:
                indicators = IndicatorCalculator.calculate_all(all_data.btc_ohlcv)
                market_snapshot["indicators"] = indicators

            logger.info(f"市场数据采集成功: BTC ${market_snapshot['btc_price']:.2f}")

            return market_snapshot

        except Exception as e:
            logger.error(f"市场数据采集失败: {e}", exc_info=True)
            raise  # 失败时抛出异常，不再返回模拟数据


# 全局实例
strategy_scheduler = StrategyScheduler()
