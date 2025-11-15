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

from apscheduler.schedulers.background import BackgroundScheduler
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
        self.scheduler = None  # 延迟初始化
        self.engine = None
        self.SessionLocal = None

    def _run_async_job(self, coro_func, *args, **kwargs):
        """在新事件循环中运行异步函数(用于BackgroundScheduler)

        CRITICAL: 为新事件循环创建新的数据库会话工厂,避免AsyncPG连接绑定到旧事件循环
        """
        logger.info(f"[Scheduler] _run_async_job called: {coro_func.__name__}")
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 🔧 为新事件循环创建新的数据库引擎和会话工厂
                # AsyncPG连接必须在创建它们的事件循环中使用
                from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
                from app.core.config import settings

                temp_engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=False,
                    pool_pre_ping=True,
                )

                temp_session_factory = async_sessionmaker(
                    temp_engine,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False,
                )

                # 临时替换SessionLocal,让调度任务使用新的会话工厂
                original_session_local = self.SessionLocal
                self.SessionLocal = temp_session_factory

                try:
                    result = loop.run_until_complete(coro_func(*args, **kwargs))
                    logger.info(f"[Scheduler] _run_async_job completed: {coro_func.__name__}")
                    return result
                finally:
                    # 恢复原始SessionLocal
                    self.SessionLocal = original_session_local
                    # 关闭临时引擎
                    loop.run_until_complete(temp_engine.dispose())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"[Scheduler] _run_async_job error in {coro_func.__name__}: {e}", exc_info=True)
            raise

    async def initialize(self):
        """初始化数据库连接和调度器"""
        # 创建调度器（使用后台线程）
        if self.scheduler is None:
            self.scheduler = BackgroundScheduler(timezone="UTC")

        # 初始化数据库连接
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
        logger.info("[Scheduler] 开始启动调度器...")
        await self.initialize()
        logger.info("[Scheduler] 调度器初始化完成")

        # 添加全局定时任务
        logger.info("[Scheduler] 添加全局定时任务...")
        self._add_global_jobs()

        # 为所有活跃策略添加独立任务
        logger.info("[Scheduler] 添加策略定时任务...")
        await self._add_all_portfolio_jobs()

        # 启动调度器
        logger.info("[Scheduler] 启动调度器线程...")
        self.scheduler.start()
        logger.info("[Scheduler] ✓ 策略调度器已启动(BackgroundScheduler)")

        # 打印所有已注册的任务及其下次执行时间
        jobs = self.scheduler.get_jobs()
        logger.info(f"[Scheduler] 已注册 {len(jobs)} 个任务:")
        for job in jobs:
            logger.info(f"[Scheduler]   - {job.id}: {job.name}")
            logger.info(f"[Scheduler]     下次执行: {job.next_run_time}")
            logger.info(f"[Scheduler]     触发器: {job.trigger}")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("策略调度器已停止")

    def _add_global_jobs(self):
        """添加全局定时任务"""

        # Job 1: 市场数据采集 (每30秒)
        self.scheduler.add_job(
            lambda: self._run_async_job(self.collect_market_data_job),
            trigger=IntervalTrigger(seconds=30),
            id="market_data_collection",
            name="市场数据采集",
            replace_existing=True,
            max_instances=1,
        )

        # Job 3: 组合快照 (每10分钟)
        self.scheduler.add_job(
            lambda: self._run_async_job(self.create_portfolio_snapshots_job),
            trigger=IntervalTrigger(minutes=10),
            id="portfolio_snapshots",
            name="组合快照",
            replace_existing=True,
            max_instances=1,
        )

        logger.info("全局定时任务已添加（市场数据+组合快照）")

    async def _add_all_portfolio_jobs(self):
        """
        为每个策略模板添加独立的批量执行任务

        优化说明：
        - 按strategy_definition_id分组
        - 每个模板创建一个定时任务，使用模板的rebalance_period_minutes
        - 同一模板的所有实例共享Agent分析结果
        """
        try:
            print(f"[Scheduler] 开始添加策略模板批量执行任务...")

            async with self.SessionLocal() as db:
                # 1. 获取所有活跃的Portfolio及其strategy_definition
                result = await db.execute(
                    select(Portfolio)
                    .options(selectinload(Portfolio.strategy_definition))
                    .where(Portfolio.is_active == True)
                )
                portfolios = result.scalars().all()

                if not portfolios:
                    logger.info("没有活跃的策略实例")
                    return

                # 2. 按strategy_definition_id分组
                from collections import defaultdict
                from app.models.strategy_definition import StrategyDefinition

                portfolios_by_definition = defaultdict(list)
                for portfolio in portfolios:
                    if portfolio.strategy_definition_id:
                        portfolios_by_definition[portfolio.strategy_definition_id].append(portfolio)

                logger.info(
                    f"找到 {len(portfolios)} 个活跃实例，"
                    f"分为 {len(portfolios_by_definition)} 个策略模板组"
                )

                # 3. 为每个模板组创建定时任务
                for definition_id, group_portfolios in portfolios_by_definition.items():
                    definition = group_portfolios[0].strategy_definition
                    if not definition:
                        logger.warning(f"策略模板 {definition_id} 不存在，跳过")
                        continue

                    # 从模板获取执行周期
                    period_minutes = definition.default_params.get("rebalance_period_minutes", 10)

                    # 创建定时任务(使用包装器运行异步函数)
                    job_id = f"strategy_template_{definition_id}"
                    logger.info(f"[Scheduler] 正在添加任务: {job_id}, 周期={period_minutes}分钟")
                    self.scheduler.add_job(
                        lambda def_id=definition_id: self._run_async_job(self.batch_execute_by_template, def_id),
                        trigger=IntervalTrigger(minutes=period_minutes),
                        id=job_id,
                        name=f"策略模板执行: {definition.display_name}",
                        replace_existing=True,
                        max_instances=1,
                    )
                    logger.info(f"[Scheduler] 任务已添加: {job_id}")

                    logger.info(
                        f"✓ 添加模板任务: {definition.display_name} "
                        f"(ID={definition_id}, 周期={period_minutes}分钟, 实例数={len(group_portfolios)})"
                    )
                    print(
                        f"[Scheduler] ✓ {definition.display_name}: "
                        f"{period_minutes}分钟周期, {len(group_portfolios)}个实例共享Agent分析"
                    )

        except Exception as e:
            logger.error(f"添加策略模板任务失败: {e}", exc_info=True)
            print(f"[Scheduler] ❌ 添加任务失败: {e}")

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

    async def batch_execute_by_template(self, definition_id: int):
        """
        按策略模板批量执行 - 新的按模板分组执行方法

        工作流程:
        1. 获取指定模板的所有活跃实例
        2. 执行一次Agent分析（所有实例共享）
        3. 为每个实例执行决策和交易

        Args:
            definition_id: 策略模板ID

        成本优化:
        - 同一模板的所有实例共享Agent分析结果
        - LLM调用次数: 1次/周期（无论有多少实例）
        """
        logger.info(f"[Scheduler] Executing strategy template {definition_id}")
        try:
            async with self.SessionLocal() as db:
                # 1. 获取指定模板的所有活跃Portfolio
                result = await db.execute(
                    select(Portfolio)
                    .options(
                        selectinload(Portfolio.holdings),
                        selectinload(Portfolio.strategy_definition)
                    )
                    .where(
                        Portfolio.strategy_definition_id == definition_id,
                        Portfolio.is_active == True
                    )
                )
                portfolios = result.scalars().all()

                if not portfolios:
                    logger.info(f"策略模板 {definition_id} 没有活跃实例，跳过执行")
                    return

                definition = portfolios[0].strategy_definition
                if not definition:
                    logger.error(f"策略模板 {definition_id} 不存在")
                    return

                logger.info(
                    f"\n{'='*60}\n"
                    f"执行策略模板: {definition.display_name} (ID={definition_id})\n"
                    f"实例数: {len(portfolios)}\n"
                    f"业务Agent: {definition.business_agents}\n"
                    f"{'='*60}"
                )

                # 2. 生成批次ID（用于关联本次批量执行的所有记录）
                import uuid
                batch_id = uuid.uuid4()
                logger.info(f"批次ID: {batch_id}")

            # 3. 采集市场数据(with错误追踪)
            try:
                market_data = await self._fetch_market_data()
            except Exception as e:
                logger.error(f"市场数据采集失败: {e}")
                # 记录错误到数据库
                from app.services.monitoring.error_tracker import error_tracker
                await error_tracker.track_exception(
                    db=db,
                    exception=e,
                    error_type="data_collection",
                    component="Scheduler._fetch_market_data",
                    severity="critical",
                    context={
                        "definition_id": definition_id,
                        "definition_name": definition.name,
                        "portfolio_count": len(portfolios),
                    }
                )
                # 继续抛出异常,让上层处理
                raise

            # 4. 根据策略定义动态执行Agent分析（所有实例共享）
            logger.info(f"执行Agent分析（{len(portfolios)} 个实例共享）")

            # 🆕 根据策略定义选择Agent执行器
            # 🔧 创建新的数据库会话用于Agent执行（避免事件循环冲突）
            async with self.SessionLocal() as agent_db:
                if definition.business_agents:
                    # 使用动态Agent执行器(新策略)
                    from app.services.strategy.dynamic_agent_executor import dynamic_agent_executor

                    logger.info(f"使用动态Agent执行器: {definition.business_agents}")
                    agent_outputs, agent_errors = await dynamic_agent_executor.execute_agents(
                        agent_names=definition.business_agents,  # ✅ 从策略定义读取
                        market_data=market_data,
                        db=agent_db,  # ✅ 使用新的数据库会话
                        user_id=portfolios[0].user_id,
                        strategy_execution_id=None,
                        template_execution_batch_id=batch_id,
                    )
                    logger.info(f"✅ 动态Agent执行完成: {list(agent_outputs.keys())}")
                else:
                    # 使用默认Agent执行器(旧策略,向后兼容)
                    from app.services.strategy.real_agent_executor import RealAgentExecutor
                    agent_executor = RealAgentExecutor()

                    logger.info("使用默认Agent执行器(旧策略)")
                    agent_outputs, agent_errors = await agent_executor.execute_all_agents(
                        market_data=market_data,
                        db=agent_db,  # ✅ 使用新的数据库会话
                        user_id=portfolios[0].user_id,
                        strategy_execution_id=None,
                        template_execution_batch_id=batch_id,
                    )
                    logger.info(f"✅ 默认Agent执行完成")

            # 5. 为每个Portfolio执行决策和交易
            success_count = 0
            failure_count = 0

            async with self.SessionLocal() as db:
                for portfolio in portfolios:
                    try:
                        logger.info(
                            f"执行实例: {portfolio.instance_name} (ID: {portfolio.id})"
                        )

                        # 使用共享的agent_outputs执行策略
                        execution = await strategy_orchestrator.execute_strategy(
                            db=db,
                            user_id=portfolio.user_id,
                            portfolio_id=str(portfolio.id),
                            market_data=market_data,
                            agent_outputs=agent_outputs,  # 共享的分析结果
                            template_execution_batch_id=batch_id,  # 🆕 传递批次ID
                        )

                        # 更新执行时间
                        portfolio.last_execution_time = datetime.utcnow()
                        await db.commit()

                        success_count += 1
                        logger.info(
                            f"✅ 实例执行完成 - {portfolio.instance_name}, "
                            f"信号: {execution.signal}, 状态: {execution.status}"
                        )

                    except Exception as e:
                        failure_count += 1
                        logger.error(
                            f"❌ 实例执行失败: {portfolio.instance_name} - {e}",
                            exc_info=True
                        )

                        # 记录错误
                        from app.services.monitoring.error_tracker import error_tracker
                        await error_tracker.track_exception(
                            db=db,
                            exception=e,
                            error_type="strategy_execution",
                            component="Scheduler.batch_execute_by_template",
                            severity="error",
                            context={
                                "portfolio_id": str(portfolio.id),
                                "portfolio_name": portfolio.instance_name,
                                "strategy_name": definition.name,
                            },
                            user_id=portfolio.user_id,
                            portfolio_id=str(portfolio.id),
                            strategy_name=definition.name,
                        )
                        # ⚠️ 重要：不要rollback！
                        # strategy_orchestrator的异常处理已经更新了execution状态并commit了
                        # 如果这里rollback，会回滚execution的状态更新，导致记录卡在RUNNING状态
                        # 只需要刷新session状态，继续下一个实例
                        await db.refresh(portfolio) if portfolio else None
                        # 继续下一个实例

            logger.info(
                f"\n{'='*60}\n"
                f"模板 {definition.display_name} 执行完成:\n"
                f"  - 成功: {success_count}\n"
                f"  - 失败: {failure_count}\n"
                f"  - Agent调用: 1次（节省 {len(portfolios) - 1} 次）\n"
                f"{'='*60}"
            )

        except Exception as e:
            logger.error(f"模板 {definition_id} 批量执行失败: {e}", exc_info=True)

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

    async def reload_template_schedule(self, definition_id: int):
        """
        动态重新加载指定策略模板的调度任务

        当admin修改策略模板的执行周期时调用此方法，立即生效

        Args:
            definition_id: 策略模板ID
        """
        try:
            logger.info(f"[Scheduler] 开始重新加载策略模板 {definition_id} 的调度任务")

            # 1. 移除旧的调度任务
            job_id = f"strategy_template_{definition_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"[Scheduler] 已移除旧任务: {job_id}")

            # 2. 从数据库重新读取最新配置
            async with self.SessionLocal() as db:
                from app.models.strategy_definition import StrategyDefinition

                result = await db.execute(
                    select(StrategyDefinition).where(
                        StrategyDefinition.id == definition_id
                    )
                )
                definition = result.scalar_one_or_none()

                if not definition:
                    logger.warning(f"[Scheduler] 策略模板 {definition_id} 不存在")
                    return

                # 3. 获取使用此模板的所有激活实例
                result = await db.execute(
                    select(Portfolio).where(
                        Portfolio.strategy_definition_id == definition_id,
                        Portfolio.is_active == True
                    )
                )
                portfolios = result.scalars().all()

            # 4. 如果没有激活实例，不创建任务
            if not portfolios:
                logger.info(
                    f"[Scheduler] 策略模板 '{definition.display_name}' "
                    f"无激活实例，不创建调度任务"
                )
                return

            # 5. 读取最新的执行周期配置
            period_minutes = definition.default_params.get("rebalance_period_minutes", 10)

            # 6. 创建新的调度任务
            self.scheduler.add_job(
                self.batch_execute_by_template,
                trigger=IntervalTrigger(minutes=period_minutes),
                id=job_id,
                name=f"策略模板执行: {definition.display_name}",
                args=[definition_id],
                replace_existing=True,
                max_instances=1,
            )

            logger.info(
                f"[Scheduler] ✓ 重新加载完成: {definition.display_name} "
                f"(ID={definition_id}, 新周期={period_minutes}分钟, 实例数={len(portfolios)})"
            )

        except Exception as e:
            logger.error(f"[Scheduler] 重新加载任务失败: {e}", exc_info=True)
            raise

    async def _fetch_market_data(self) -> dict:
        """
        采集真实市场数据并转换为Agent期望的格式

        使用真实的市场数据 API（CoinGecko, Binance, Alternative.me, FRED）

        返回格式:
        {
            "assets": {
                "BTC": {
                    "current_price": 43250.0,
                    "price_change_24h": 3.5,
                    "ohlcv_15m": [...],
                    "ohlcv_60m": [...],
                    "funding_rate": 0.0001,
                    "open_interest_change_24h": 5.2,
                    "futures_premium": 0.5,
                    ...
                },
                "ETH": {...},
                "SOL": {...}
            },
            "macro": {
                "dxy": 103.5,
                "fed_rate": 3.87,
                ...
            },
            "sentiment": {
                "fear_greed_value": 65,
                ...
            },
            "onchain": {
                "btc_mvrv_zscore": 2.5
            }
        }
        """
        try:
            logger.info("📊 开始采集市场数据...")

            # 1. 获取原始市场数据
            raw_snapshot = await real_market_data_service.get_complete_market_snapshot()
            logger.info(f"✅ 原始数据采集成功: BTC ${raw_snapshot['btc_price']:.2f}")

            # 2. 收集 OHLCV 数据
            all_data = await data_manager.collect_all()
            logger.info("✅ OHLCV数据采集完成")

            # 3. 转换为Agent期望的格式
            logger.info("🔄 开始转换数据格式...")

            # 3.1 构建 assets 结构
            assets = {}

            # BTC 数据
            btc_asset = {
                "current_price": float(raw_snapshot["btc_price"]),
                "price_change_24h": raw_snapshot["btc_price_change_24h"],
                "volume_24h": raw_snapshot.get("btc_volume_24h", 0),
            }

            # 添加 OHLCV K线数据
            if hasattr(all_data, "btc_ohlcv") and all_data.btc_ohlcv:
                # 15分钟K线 (最近100根)
                btc_asset["ohlcv_15m"] = all_data.btc_ohlcv[-100:] if len(all_data.btc_ohlcv) > 100 else all_data.btc_ohlcv
                # 60分钟K线 (从15分钟聚合,取每4根)
                btc_asset["ohlcv_60m"] = all_data.btc_ohlcv[-400::4] if len(all_data.btc_ohlcv) > 400 else all_data.btc_ohlcv[::4]
                logger.info(f"  ✅ BTC K线数据: 15m={len(btc_asset['ohlcv_15m'])}根, 60m={len(btc_asset['ohlcv_60m'])}根")
            else:
                logger.warning("  ⚠️  BTC OHLCV数据缺失,使用空数组")
                btc_asset["ohlcv_15m"] = []
                btc_asset["ohlcv_60m"] = []

            # 添加衍生品数据 (TODO: 从真实API获取,暂时使用合理的模拟值)
            btc_asset["funding_rate"] = 0.0001  # 0.01% - 典型的正常资金费率
            btc_asset["open_interest_change_24h"] = 2.5  # 2.5% - 温和增长
            btc_asset["futures_premium"] = 0.3  # 0.3% - 健康的期货溢价
            logger.info(f"  📈 BTC衍生品数据(Mock): funding={btc_asset['funding_rate']:.4f}, OI_change={btc_asset['open_interest_change_24h']:.1f}%")

            assets["BTC"] = btc_asset

            # ETH 数据
            if raw_snapshot.get("eth_price"):
                eth_asset = {
                    "current_price": float(raw_snapshot["eth_price"]),
                    "price_change_24h": raw_snapshot.get("eth_price_change_24h", 0),
                    "volume_24h": 0,
                    "ohlcv_15m": [],  # TODO: 添加ETH K线
                    "ohlcv_60m": [],
                    "funding_rate": 0.0001,
                    "open_interest_change_24h": 2.0,
                    "futures_premium": 0.25,
                }
                assets["ETH"] = eth_asset
                logger.info(f"  ✅ ETH数据: ${eth_asset['current_price']:.2f}")
            else:
                logger.warning("  ⚠️  ETH数据缺失")

            # SOL 数据 (TODO: 添加SOL数据采集)
            assets["SOL"] = {
                "current_price": 100.0,  # Mock
                "price_change_24h": 1.5,
                "volume_24h": 0,
                "ohlcv_15m": [],
                "ohlcv_60m": [],
                "funding_rate": 0.00015,
                "open_interest_change_24h": 3.0,
                "futures_premium": 0.4,
            }
            logger.info("  ⚠️  SOL数据使用Mock值")

            # 3.2 构建 macro 结构 (重命名字段以匹配agent期望)
            macro = {
                "dxy": raw_snapshot["macro"].get("dxy_index", 103.0),
                "fed_rate": raw_snapshot["macro"].get("fed_funds_rate", 5.5),
                "m2_growth": raw_snapshot["macro"].get("m2_growth", 2.5),
                "treasury_10y": raw_snapshot["macro"].get("treasury_10y", 4.5),
                "vix": raw_snapshot["macro"].get("vix", 15.0),
            }
            logger.info(f"  📊 宏观数据: DXY={macro['dxy']:.1f}, Fed={macro['fed_rate']:.2f}%")

            # 3.3 构建 sentiment 结构 (重命名字段)
            sentiment = {
                "fear_greed_value": raw_snapshot["fear_greed"].get("value", 50),
                "fear_greed_classification": raw_snapshot["fear_greed"].get("classification", "Neutral"),
            }
            logger.info(f"  😰 情绪指标: Fear&Greed={sentiment['fear_greed_value']}")

            # 3.4 构建 onchain 结构 (TODO: 添加真实链上数据)
            onchain = {
                "btc_mvrv_zscore": 1.8,  # Mock - MVRV Z-Score (1-3为健康区间)
            }
            logger.info(f"  ⛓️  链上数据(Mock): MVRV={onchain['btc_mvrv_zscore']:.1f}")

            # 4. 组装最终数据结构
            market_data = {
                "assets": assets,
                "macro": macro,
                "sentiment": sentiment,
                "onchain": onchain,
                "timestamp": raw_snapshot.get("timestamp"),
                "last_updated": raw_snapshot.get("last_updated"),
            }

            logger.info(f"✅ 市场数据格式转换完成 - 包含 {len(assets)} 个资产")
            logger.info(f"   - BTC: ${assets['BTC']['current_price']:.2f} ({assets['BTC']['price_change_24h']:+.2f}%)")
            logger.info(f"   - Fear&Greed: {sentiment['fear_greed_value']}")
            logger.info(f"   - DXY: {macro['dxy']:.1f}, Fed Rate: {macro['fed_rate']:.2f}%")

            return market_data

        except Exception as e:
            logger.error(f"❌ 市场数据采集失败: {e}", exc_info=True)
            raise  # 失败时抛出异常，不再返回模拟数据


# 全局实例
strategy_scheduler = StrategyScheduler()
