"""Real Agent Execution Service

整合已有的 macro_agent、ta_agent、onchain_agent 为策略系统提供真实的 Agent 分析
"""

import asyncio
import time
from typing import Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.macro_agent import macro_agent
from app.agents.ta_agent import ta_agent
from app.agents.onchain_agent import OnChainAgent
from app.services.data_collectors.manager import data_manager
from app.services.indicators.calculator import IndicatorCalculator
from app.services.agents.execution_recorder import agent_execution_recorder


class RealAgentExecutor:
    """真实 Agent 执行服务

    集成系统中已有的 macro_agent、ta_agent、onchain_agent，
    为策略系统提供真实的多维度分析
    """

    def __init__(self):
        """初始化 Agent 执行器"""
        self.onchain_agent = OnChainAgent()

    async def execute_all_agents(
        self,
        market_data: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        strategy_execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行所有 Agent 分析

        Args:
            market_data: 市场数据快照（包含 btc_price, macro, fear_greed, indicators 等）
            db: 数据库会话（可选，用于记录 Agent 执行）
            user_id: 用户 ID
            strategy_execution_id: 策略执行 ID（用于关联记录）

        Returns:
            Dict 包含所有 Agent 的输出，格式：
            {
                "macro": {"signal": "BULLISH", "confidence": 0.75, ...},
                "ta": {"signal": "NEUTRAL", "confidence": 0.60, ...},
                "onchain": {"signal": "BULLISH", "confidence": 0.70, ...},
            }
        """
        # 并行执行所有 Agent
        tasks = [
            self._run_macro_agent(market_data, db, user_id, strategy_execution_id),
            self._run_ta_agent(market_data, db, user_id, strategy_execution_id),
            self._run_onchain_agent(market_data, db, user_id, strategy_execution_id),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 构建输出字典
        agent_outputs = {}
        agent_names = ["macro", "ta", "onchain"]

        for agent_name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                print(f"❌ Error running {agent_name}_agent: {result}")
                # 如果某个 Agent 失败，使用默认值
                agent_outputs[agent_name] = {
                    "signal": "HOLD",
                    "confidence": 0.5,
                }
            else:
                agent_outputs[agent_name] = result

        return agent_outputs

    async def _run_macro_agent(
        self,
        market_data: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        strategy_execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """运行宏观分析 Agent"""
        start_time = time.time()

        try:
            # 准备 MacroAgent 需要的数据格式
            btc_price_obj = market_data.get("btc_price", {})
            agent_data = {
                "btc_price": btc_price_obj.get("price") if isinstance(btc_price_obj, dict) else btc_price_obj,
                "price_change_24h": btc_price_obj.get("price_change_24h") if isinstance(btc_price_obj, dict) else 0,
                "macro": market_data.get("macro"),
                "fear_greed": market_data.get("fear_greed"),
            }

            # 执行分析
            output = await macro_agent.analyze(agent_data)

            # 计算执行时长
            execution_duration_ms = int((time.time() - start_time) * 1000)

            # 记录到数据库（如果提供了 db session）
            if db and output:
                try:
                    llm_info = {
                        "provider": getattr(macro_agent, "last_llm_provider", "tuzi"),
                        "model": getattr(macro_agent, "last_llm_model", "claude-sonnet-4-5"),
                        "prompt": getattr(macro_agent, "last_llm_prompt", None),
                        "response": getattr(macro_agent, "last_llm_response", None),
                        "tokens_used": getattr(macro_agent, "last_tokens_used", None),
                        "cost": getattr(macro_agent, "last_llm_cost", None),
                    }

                    await agent_execution_recorder.record_macro_agent(
                        db=db,
                        output=output,
                        market_data=market_data,
                        llm_info=llm_info,
                        caller_type="strategy_execution",
                        caller_id=None,  # Not used for strategy system
                        strategy_execution_id=strategy_execution_id,  # Fix: use strategy_execution_id parameter
                        user_id=user_id,
                        execution_duration_ms=execution_duration_ms,
                    )
                    print(f"✅ Recorded macro_agent execution to database")

                except Exception as record_error:
                    print(f"⚠️  Failed to record macro_agent execution: {record_error}")

            # 转换为策略系统需要的格式
            return {
                "signal": output.signal.value,
                "confidence": output.confidence,
                "reasoning": output.reasoning,
                "macro_indicators": output.macro_indicators if hasattr(output, "macro_indicators") else None,
                "key_factors": output.key_factors if hasattr(output, "key_factors") else None,
                "risk_assessment": output.risk_assessment if hasattr(output, "risk_assessment") else None,
            }

        except Exception as e:
            print(f"Error in macro_agent: {e}")
            raise

    async def _run_ta_agent(
        self,
        market_data: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        strategy_execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """运行技术分析 Agent"""
        start_time = time.time()

        try:
            # 准备 TAAgent 需要的数据格式
            btc_price_obj = market_data.get("btc_price", {})
            agent_data = {
                "btc_price": btc_price_obj.get("price") if isinstance(btc_price_obj, dict) else btc_price_obj,
                "price_change_24h": btc_price_obj.get("price_change_24h") if isinstance(btc_price_obj, dict) else 0,
                "indicators": market_data.get("indicators"),
            }

            # 执行分析
            output = await ta_agent.analyze(agent_data)

            # 计算执行时长
            execution_duration_ms = int((time.time() - start_time) * 1000)

            # 记录到数据库
            if db and output:
                try:
                    llm_info = {
                        "provider": getattr(ta_agent, "last_llm_provider", "tuzi"),
                        "model": getattr(ta_agent, "last_llm_model", "claude-sonnet-4-5"),
                        "prompt": getattr(ta_agent, "last_llm_prompt", None),
                        "response": getattr(ta_agent, "last_llm_response", None),
                        "tokens_used": getattr(ta_agent, "last_tokens_used", None),
                        "cost": getattr(ta_agent, "last_llm_cost", None),
                    }

                    await agent_execution_recorder.record_ta_agent(
                        db=db,
                        output=output,
                        market_data=market_data,
                        llm_info=llm_info,
                        caller_type="strategy_execution",
                        caller_id=None,  # Not used for strategy system
                        strategy_execution_id=strategy_execution_id,  # Fix: use strategy_execution_id parameter
                        user_id=user_id,
                        execution_duration_ms=execution_duration_ms,
                    )
                    print(f"✅ Recorded ta_agent execution to database")

                except Exception as record_error:
                    print(f"⚠️  Failed to record ta_agent execution: {record_error}")

            # 转换为策略系统需要的格式
            return {
                "signal": output.signal.value,
                "confidence": output.confidence,
                "reasoning": output.reasoning,
                "technical_indicators": output.technical_indicators if hasattr(output, "technical_indicators") else None,
                "support_levels": output.support_levels if hasattr(output, "support_levels") else None,
                "resistance_levels": output.resistance_levels if hasattr(output, "resistance_levels") else None,
                "trend_analysis": output.trend_analysis if hasattr(output, "trend_analysis") else None,
                "key_patterns": output.key_patterns if hasattr(output, "key_patterns") else None,
            }

        except Exception as e:
            print(f"Error in ta_agent: {e}")
            raise

    async def _run_onchain_agent(
        self,
        market_data: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        strategy_execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """运行链上数据分析 Agent"""
        start_time = time.time()

        try:
            # 收集链上数据
            onchain_data = await data_manager.collect_for_onchain_agent()

            # 执行分析（OnChainAgent 需要 user_message 参数）
            user_message = "分析当前比特币市场状况，提供交易建议"
            output = await self.onchain_agent.analyze(user_message, onchain_data)

            # 计算执行时长
            execution_duration_ms = int((time.time() - start_time) * 1000)

            # 记录到数据库
            if db and output:
                try:
                    llm_info = {
                        "provider": getattr(self.onchain_agent, "last_llm_provider", "tuzi"),
                        "model": getattr(self.onchain_agent, "last_llm_model", "claude-sonnet-4-5"),
                        "prompt": getattr(self.onchain_agent, "last_llm_prompt", None),
                        "response": getattr(self.onchain_agent, "last_llm_response", None),
                        "tokens_used": getattr(self.onchain_agent, "last_tokens_used", None),
                        "cost": getattr(self.onchain_agent, "last_llm_cost", None),
                    }

                    await agent_execution_recorder.record_onchain_agent(
                        db=db,
                        output=output,
                        market_data=market_data,
                        llm_info=llm_info,
                        caller_type="strategy_execution",
                        caller_id=None,  # Not used for strategy system
                        strategy_execution_id=strategy_execution_id,  # Fix: use strategy_execution_id parameter
                        user_id=user_id,
                        execution_duration_ms=execution_duration_ms,
                    )
                    print(f"✅ Recorded onchain_agent execution to database")

                except Exception as record_error:
                    print(f"⚠️  Failed to record onchain_agent execution: {record_error}")

            # 转换为策略系统需要的格式
            return {
                "signal": output.signal.value,
                "confidence": output.confidence,
                "reasoning": output.reasoning,
                "onchain_metrics": output.onchain_metrics if hasattr(output, "onchain_metrics") else None,
                "network_health": output.network_health if hasattr(output, "network_health") else None,
                "key_observations": output.key_observations if hasattr(output, "key_observations") else None,
            }

        except Exception as e:
            print(f"Error in onchain_agent: {e}")
            raise


# 全局实例
real_agent_executor = RealAgentExecutor()
