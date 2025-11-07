"""Agent Execution Recorder - 业务Agent工作成果记录服务"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.agent_execution import AgentExecution
from app.schemas.agents import (
    MacroAnalysisOutput,
    TechnicalAnalysisOutput,
    OnChainAnalysisOutput
)


class AgentExecutionRecorder:
    """统一记录和查询业务Agent执行结果"""

    # Agent显示名称映射
    DISPLAY_NAMES = {
        'macro_agent': 'The Oracle',
        'ta_agent': 'Momentum Scout',
        'onchain_agent': 'Data Warden',
    }

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
            return AgentExecutionRecorder._serialize_for_json(obj.dict())
        elif isinstance(obj, dict):
            return {k: AgentExecutionRecorder._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [AgentExecutionRecorder._serialize_for_json(item) for item in obj]
        elif isinstance(obj, tuple):
            return [AgentExecutionRecorder._serialize_for_json(item) for item in obj]
        else:
            return obj

    async def record_macro_agent(
        self,
        db: AsyncSession,
        output: MacroAnalysisOutput,
        market_data: Dict[str, Any],
        llm_info: Dict[str, Any],
        caller_type: Optional[str] = None,
        caller_id: Optional[str] = None,
        strategy_execution_id: Optional[str] = None,
        user_id: Optional[int] = None,  # 🔧 修复: Integer 类型，与 user.id 一致
        execution_duration_ms: Optional[int] = None,
    ) -> AgentExecution:
        """记录MacroAgent执行结果

        Args:
            db: 数据库会话
            output: MacroAgent分析输出
            market_data: 市场数据快照
            llm_info: LLM调用信息 (provider, model, prompt, response, tokens_used, cost)
            caller_type: 调用方类型 ('research_chat', 'strategy_system', 'manual')
            caller_id: 调用方ID (conversation_id)
            strategy_execution_id: 策略执行ID (策略系统专用)
            user_id: 触发用户ID
            execution_duration_ms: 执行耗时(毫秒)

        Returns:
            AgentExecution: 保存的执行记录
        """
        # 序列化 market_data 以确保可以存储到 JSONB
        serialized_market_data = self._serialize_for_json(market_data)

        execution = AgentExecution(
            agent_name='macro_agent',
            agent_display_name=self.DISPLAY_NAMES['macro_agent'],
            executed_at=datetime.utcnow(),
            execution_duration_ms=execution_duration_ms,
            status='success',

            # 标准化输出
            signal=output.signal.value,
            confidence=output.confidence,
            score=None,  # MacroAgent不输出score
            reasoning=output.reasoning,

            # Agent专属数据
            agent_specific_data={
                'macro_indicators': output.macro_indicators,
                'risk_assessment': output.risk_assessment,
            },
            market_data_snapshot=serialized_market_data,

            # LLM信息
            llm_provider=llm_info.get('provider'),
            llm_model=llm_info.get('model'),
            llm_prompt=llm_info.get('prompt'),
            llm_response=llm_info.get('response'),
            tokens_used=llm_info.get('tokens_used'),
            llm_cost=llm_info.get('cost'),

            # 调用方关联
            caller_type=caller_type,
            caller_id=caller_id,
            strategy_execution_id=strategy_execution_id,
            user_id=user_id,
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        return execution

    async def record_ta_agent(
        self,
        db: AsyncSession,
        output: TechnicalAnalysisOutput,
        market_data: Dict[str, Any],
        llm_info: Dict[str, Any],
        caller_type: Optional[str] = None,
        caller_id: Optional[str] = None,
        strategy_execution_id: Optional[str] = None,
        user_id: Optional[int] = None,  # 🔧 修复: Integer 类型，与 user.id 一致
        execution_duration_ms: Optional[int] = None,
    ) -> AgentExecution:
        """记录TAAgent执行结果

        Args:
            db: 数据库会话
            output: TAAgent分析输出
            market_data: 市场数据快照
            llm_info: LLM调用信息
            caller_type: 调用方类型
            caller_id: 调用方ID
            strategy_execution_id: 策略执行ID
            user_id: 触发用户ID
            execution_duration_ms: 执行耗时(毫秒)

        Returns:
            AgentExecution: 保存的执行记录
        """
        # 序列化 market_data 以确保可以存储到 JSONB
        serialized_market_data = self._serialize_for_json(market_data)

        execution = AgentExecution(
            agent_name='ta_agent',
            agent_display_name=self.DISPLAY_NAMES['ta_agent'],
            executed_at=datetime.utcnow(),
            execution_duration_ms=execution_duration_ms,
            status='success',

            # 标准化输出
            signal=output.signal.value,
            confidence=output.confidence,
            score=None,
            reasoning=output.reasoning,

            # Agent专属数据
            agent_specific_data={
                'technical_indicators': output.technical_indicators,
                'support_levels': output.support_levels,
                'resistance_levels': output.resistance_levels,
                'trend_analysis': output.trend_analysis,
                'key_patterns': output.key_patterns,
            },
            market_data_snapshot=serialized_market_data,

            # LLM信息
            llm_provider=llm_info.get('provider'),
            llm_model=llm_info.get('model'),
            llm_prompt=llm_info.get('prompt'),
            llm_response=llm_info.get('response'),
            tokens_used=llm_info.get('tokens_used'),
            llm_cost=llm_info.get('cost'),

            # 调用方关联
            caller_type=caller_type,
            caller_id=caller_id,
            strategy_execution_id=strategy_execution_id,
            user_id=user_id,
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        return execution

    async def record_onchain_agent(
        self,
        db: AsyncSession,
        output: OnChainAnalysisOutput,
        market_data: Dict[str, Any],
        llm_info: Dict[str, Any],
        caller_type: Optional[str] = None,
        caller_id: Optional[str] = None,
        strategy_execution_id: Optional[str] = None,
        user_id: Optional[int] = None,  # 🔧 修复: Integer 类型，与 user.id 一致
        execution_duration_ms: Optional[int] = None,
    ) -> AgentExecution:
        """记录OnChainAgent执行结果

        Args:
            db: 数据库会话
            output: OnChainAgent分析输出
            market_data: 市场数据快照
            llm_info: LLM调用信息
            caller_type: 调用方类型
            caller_id: 调用方ID
            strategy_execution_id: 策略执行ID
            user_id: 触发用户ID
            execution_duration_ms: 执行耗时(毫秒)

        Returns:
            AgentExecution: 保存的执行记录
        """
        # 序列化 market_data 以确保可以存储到 JSONB
        serialized_market_data = self._serialize_for_json(market_data)

        execution = AgentExecution(
            agent_name='onchain_agent',
            agent_display_name=self.DISPLAY_NAMES['onchain_agent'],
            executed_at=datetime.utcnow(),
            execution_duration_ms=execution_duration_ms,
            status='success',

            # 标准化输出
            signal=output.signal.value,
            confidence=output.confidence,
            score=None,
            reasoning=output.reasoning,

            # Agent专属数据
            agent_specific_data={
                'onchain_metrics': output.onchain_metrics,
                'network_health': output.network_health,
                'key_observations': output.key_observations,
            },
            market_data_snapshot=serialized_market_data,

            # LLM信息
            llm_provider=llm_info.get('provider'),
            llm_model=llm_info.get('model'),
            llm_prompt=llm_info.get('prompt'),
            llm_response=llm_info.get('response'),
            tokens_used=llm_info.get('tokens_used'),
            llm_cost=llm_info.get('cost'),

            # 调用方关联
            caller_type=caller_type,
            caller_id=caller_id,
            strategy_execution_id=strategy_execution_id,
            user_id=user_id,
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        return execution

    async def get_latest_executions(
        self,
        db: AsyncSession,
        agent_names: Optional[List[str]] = None,
    ) -> Dict[str, AgentExecution]:
        """获取最新的Agent执行结果（用于Mind Hub显示）

        Args:
            agent_names: Agent名称列表，默认查询所有业务Agent

        Returns:
            {
                'macro_agent': AgentExecution(...),
                'ta_agent': AgentExecution(...),
                'onchain_agent': AgentExecution(...)
            }
        """
        if agent_names is None:
            agent_names = ['macro_agent', 'ta_agent', 'onchain_agent']

        results = {}

        for agent_name in agent_names:
            result = await db.execute(
                select(AgentExecution)
                .where(
                    and_(
                        AgentExecution.agent_name == agent_name,
                        AgentExecution.status == 'success'
                    )
                )
                .order_by(desc(AgentExecution.executed_at))
                .limit(1)
            )

            execution = result.scalar_one_or_none()
            if execution:
                results[agent_name] = execution

        return results

    async def get_executions_by_caller(
        self,
        db: AsyncSession,
        caller_type: str,
        caller_id: str,
    ) -> List[AgentExecution]:
        """按调用方查询Agent执行结果（用于追溯分析）

        Args:
            caller_type: 'research_chat' 或 'strategy_system'
            caller_id: conversation_id 或 strategy_execution_id

        Returns:
            AgentExecution列表，按执行时间排序
        """
        result = await db.execute(
            select(AgentExecution)
            .where(
                and_(
                    AgentExecution.caller_type == caller_type,
                    AgentExecution.caller_id == caller_id
                )
            )
            .order_by(AgentExecution.executed_at)
        )

        return result.scalars().all()

    async def get_executions_by_strategy(
        self,
        db: AsyncSession,
        strategy_execution_id: str,
    ) -> List[AgentExecution]:
        """按策略执行ID查询Agent执行结果（策略系统专用）

        Args:
            strategy_execution_id: 策略执行ID

        Returns:
            AgentExecution列表，按执行时间排序
        """
        result = await db.execute(
            select(AgentExecution)
            .where(AgentExecution.strategy_execution_id == strategy_execution_id)
            .order_by(AgentExecution.executed_at)
        )

        return result.scalars().all()

    async def get_executions_by_time_range(
        self,
        db: AsyncSession,
        agent_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[AgentExecution]:
        """按时间范围查询Agent执行历史（用于趋势分析）

        Args:
            agent_name: Agent名称
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            AgentExecution列表，按执行时间排序
        """
        result = await db.execute(
            select(AgentExecution)
            .where(
                and_(
                    AgentExecution.agent_name == agent_name,
                    AgentExecution.executed_at >= start_time,
                    AgentExecution.executed_at <= end_time,
                    AgentExecution.status == 'success'
                )
            )
            .order_by(AgentExecution.executed_at)
        )

        return result.scalars().all()


# 全局实例
agent_execution_recorder = AgentExecutionRecorder()
