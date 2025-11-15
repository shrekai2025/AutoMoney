"""Dynamic Agent Executor - 动态Agent执行器

根据策略定义的business_agents字段,动态执行不同的Agent
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.execution_recorder import agent_execution_recorder

logger = logging.getLogger(__name__)


class DynamicAgentExecutor:
    """
    动态Agent执行器
    
    根据strategy_definition.business_agents列表动态执行Agent
    支持:
    - macro: MacroAgent (旧策略)
    - ta: TAAgent (旧策略)
    - onchain: OnChainAgent (旧策略)
    - regime_filter: RegimeFilterAgent (动量策略)
    - ta_momentum: TAMomentumAgent (动量策略)
    """
    
    def __init__(self):
        """初始化Agent注册表"""
        self._agent_registry = {}
        self._init_agent_registry()
    
    def _init_agent_registry(self):
        """注册所有可用的Agent"""
        try:
            # 旧策略Agent
            from app.agents.macro_agent import macro_agent
            from app.agents.ta_agent import ta_agent
            from app.agents.onchain_agent import OnChainAgent
            
            self._agent_registry["macro"] = macro_agent
            self._agent_registry["ta"] = ta_agent
            self._agent_registry["onchain"] = OnChainAgent()  # 实例化
            
            logger.info("✅ 已注册旧策略Agent: macro, ta, onchain")
        except ImportError as e:
            logger.warning(f"旧策略Agent导入失败: {e}")
        
        try:
            # 动量策略Agent
            from app.agents.regime_filter_agent import regime_filter_agent
            from app.agents.ta_momentum_agent import ta_momentum_agent
            
            self._agent_registry["regime_filter"] = regime_filter_agent
            self._agent_registry["ta_momentum"] = ta_momentum_agent
            
            logger.info("✅ 已注册动量策略Agent: regime_filter, ta_momentum")
        except ImportError as e:
            logger.warning(f"动量策略Agent导入失败: {e}")
    
    async def execute_agents(
        self,
        agent_names: List[str],
        market_data: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        strategy_execution_id: Optional[str] = None,
        template_execution_batch_id: Optional[Any] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        根据agent_names动态执行Agent
        
        Args:
            agent_names: 要执行的Agent名称列表,如 ["regime_filter", "ta_momentum"]
            market_data: 市场数据
            db: 数据库会话
            user_id: 用户ID
            strategy_execution_id: 策略执行ID
            template_execution_batch_id: 批次ID
        
        Returns:
            (agent_outputs, agent_errors)
        """
        logger.info(f"开始执行Agent: {agent_names}")
        
        # 验证Agent是否可用
        unavailable_agents = []
        for agent_name in agent_names:
            if agent_name not in self._agent_registry:
                unavailable_agents.append(agent_name)
        
        if unavailable_agents:
            error_msg = f"以下Agent不可用: {unavailable_agents}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 并行执行所有Agent
        logger.info(f"🎯 准备并行执行 {len(agent_names)} 个Agent: {agent_names}")
        print(f"🎯 准备并行执行 {len(agent_names)} 个Agent: {agent_names}")

        tasks = []
        for agent_name in agent_names:
            agent = self._agent_registry[agent_name]
            logger.info(f"📦 创建Agent任务: {agent_name}")
            print(f"📦 创建Agent任务: {agent_name}")
            task = self._run_agent(
                agent_name=agent_name,
                agent=agent,
                market_data=market_data,
                db=db,
                user_id=user_id,
                strategy_execution_id=strategy_execution_id,
                template_execution_batch_id=template_execution_batch_id,
            )
            tasks.append(task)

        logger.info(f"⏳ 开始并行执行所有Agent...")
        print(f"⏳ 开始并行执行所有Agent...")
        # 执行并收集结果
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"✅ Agent并行执行完成,获得 {len(results)} 个结果")
        print(f"✅ Agent并行执行完成,获得 {len(results)} 个结果")
        
        # 整理输出
        agent_outputs = {}
        agent_errors = {}
        
        for agent_name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                logger.error(f"❌ Agent {agent_name} 执行失败: {result}")
                agent_errors[agent_name] = {
                    "error": str(result),
                    "type": type(result).__name__,
                }
                agent_outputs[agent_name] = None
            else:
                logger.info(f"✅ Agent {agent_name} 执行成功")
                agent_outputs[agent_name] = result
        
        # 检查是否有失败的Agent
        failed_agents = [name for name in agent_names if agent_outputs.get(name) is None]
        if failed_agents:
            logger.warning(f"部分Agent执行失败: {failed_agents}")
            # 不抛出异常,允许部分Agent失败
        
        return agent_outputs, agent_errors
    
    async def _run_agent(
        self,
        agent_name: str,
        agent: Any,
        market_data: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        strategy_execution_id: Optional[str] = None,
        template_execution_batch_id: Optional[Any] = None,
    ) -> Any:
        """
        执行单个Agent

        Args:
            agent_name: Agent名称
            agent: Agent实例
            market_data: 市场数据
            db: 数据库会话
            user_id: 用户ID
            strategy_execution_id: 策略执行ID
            template_execution_batch_id: 批次ID

        Returns:
            Agent输出
        """
        start_time = time.time()

        try:
            logger.info(f"🚀 开始执行 {agent_name}... (agent实例类型: {type(agent).__name__})")
            print(f"🚀 开始执行 {agent_name}... (agent实例类型: {type(agent).__name__})")
            
            # 根据Agent类型调用不同的方法
            if agent_name in ["macro", "ta", "onchain"]:
                # 旧策略Agent: 使用analyze方法（只接受market_data参数）
                if asyncio.iscoroutinefunction(agent.analyze):
                    output = await agent.analyze(market_data=market_data)
                else:
                    output = agent.analyze(market_data=market_data)
            
            elif agent_name == "regime_filter":
                # RegimeFilterAgent: 使用analyze方法
                logger.info(f"💡 调用 {agent_name}.analyze(market_data=..., custom_weights=None)")
                print(f"💡 调用 {agent_name}.analyze(market_data=..., custom_weights=None)")
                output = await agent.analyze(
                    market_data=market_data,
                    custom_weights=None,  # 使用默认权重
                )
                logger.info(f"✅ {agent_name} 执行完成, output keys: {list(output.keys()) if isinstance(output, dict) else type(output)}")
                print(f"✅ {agent_name} 执行完成, output keys: {list(output.keys()) if isinstance(output, dict) else type(output)}")

            elif agent_name == "ta_momentum":
                # TAMomentumAgent: 使用analyze方法
                logger.info(f"💡 调用 {agent_name}.analyze(market_data=...)")
                print(f"💡 调用 {agent_name}.analyze(market_data=...)")
                output = await agent.analyze(
                    market_data=market_data,
                )
                logger.info(f"✅ {agent_name} 执行完成, output keys: {list(output.keys()) if isinstance(output, dict) else type(output)}")
                print(f"✅ {agent_name} 执行完成, output keys: {list(output.keys()) if isinstance(output, dict) else type(output)}")

            else:
                raise ValueError(f"未知的Agent类型: {agent_name}")

            # 计算执行时长
            execution_duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录新Agent的执行（旧Agent在自己的analyze方法中已经记录）
            if agent_name in ["regime_filter", "ta_momentum"] and db:
                try:
                    # 转换Pydantic模型为dict（如果output是Pydantic对象）
                    if hasattr(output, 'dict'):
                        output_dict = output.dict()
                    elif hasattr(output, 'model_dump'):
                        output_dict = output.model_dump()
                    else:
                        output_dict = output
                    
                    await agent_execution_recorder.record_generic_agent(
                        db=db,
                        agent_name=agent_name,
                        output=output_dict,
                        market_data=market_data,
                        llm_info=None,  # 动量策略Agent暂不使用LLM
                        caller_type="strategy_execution",
                        caller_id=None,
                        strategy_execution_id=strategy_execution_id,
                        user_id=user_id,
                        execution_duration_ms=execution_duration_ms,
                        template_execution_batch_id=template_execution_batch_id,
                    )
                    logger.info(f"✅ {agent_name} 执行记录已保存")
                except Exception as record_error:
                    logger.warning(f"⚠️  {agent_name} 执行记录保存失败: {record_error}")
            
            logger.info(f"✅ {agent_name} 执行完成")
            return output
        
        except Exception as e:
            logger.error(f"❌ {agent_name} 执行异常: {e}", exc_info=True)
            raise
    
    def is_agent_available(self, agent_name: str) -> bool:
        """检查Agent是否可用"""
        return agent_name in self._agent_registry
    
    def get_available_agents(self) -> List[str]:
        """获取所有可用的Agent名称"""
        return list(self._agent_registry.keys())


# 全局单例
dynamic_agent_executor = DynamicAgentExecutor()

