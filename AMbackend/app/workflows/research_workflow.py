"""ResearchWorkflow - Orchestrates Research Chat multi-agent workflow"""

from typing import Dict, Any, List, AsyncGenerator, Optional
import asyncio
import json
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.super_agent import super_agent
from app.agents.planning_agent import planning_agent
from app.agents.general_analysis_agent import general_analysis_agent
from app.agents.macro_agent import macro_agent
from app.agents.ta_agent import ta_agent
from app.agents.onchain_agent import OnChainAgent
from app.agents.registry import agent_registry
from app.services.data_collectors.manager import data_manager
from app.services.agents.execution_recorder import agent_execution_recorder
from app.schemas.research import DecisionType


class ResearchWorkflow:
    """
    Orchestrates the Research Chat workflow

    Flow:
    1. SuperAgent: Route question (direct answer or planning)
    2. PlanningAgent: Create execution plan (if routed)
    3. Business Agents: Execute analysis in parallel
    4. GeneralAnalysisAgent: Synthesize results into final answer
    """

    def __init__(self):
        """Initialize ResearchWorkflow"""
        self.agent_map = {
            "macro_agent": macro_agent,
            "ta_agent": ta_agent,
            "onchain_agent": OnChainAgent(),  # Instantiate OnChainAgent
        }

    async def process_question(
        self,
        user_message: str,
        chat_history: List[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process user question through Research Chat workflow

        Yields SSE-style events for real-time frontend updates

        Args:
            user_message: User's question
            chat_history: Recent chat history (optional)
            db: Database session for recording agent executions (optional)
            user_id: User ID for tracking (optional)
            conversation_id: Conversation ID for tracking (optional)

        Yields:
            Dict events with type and data for SSE streaming
        """
        chat_history = chat_history or []

        try:
            # Step 1: SuperAgent Routing
            yield {
                "type": "status",
                "data": {
                    "stage": "routing",
                    "message": "任务识别",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            routing_result = await super_agent.route(user_message, chat_history)

            # Only show SuperAgent decision if it's DIRECT_ANSWER
            # For COMPLEX_ANALYSIS, we go straight to planning
            if routing_result.decision == DecisionType.DIRECT_ANSWER:
                yield {
                    "type": "super_agent_decision",
                    "data": {
                        "decision": routing_result.decision.value,
                        "reasoning": routing_result.reasoning,
                        "confidence": routing_result.confidence,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }

            # If direct answer, return immediately
            if routing_result.decision == DecisionType.DIRECT_ANSWER:
                yield {
                    "type": "final_answer",
                    "data": {
                        "answer": routing_result.direct_answer,
                        "source": "super_agent",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }
                return

            # Step 2: PlanningAgent Planning
            yield {
                "type": "status",
                "data": {
                    "stage": "planning",
                    "message": "规划分析任务...",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            plan = await planning_agent.plan(user_message, chat_history)

            yield {
                "type": "planning_result",
                "data": {
                    "task_breakdown": {
                        "analysis_phase": [
                            {
                                "agent": p.agent,
                                "reason": p.reason,
                                "priority": p.priority,
                                "data_required": p.data_required,
                            }
                            for p in plan.task_breakdown.analysis_phase
                        ],
                        "decision_phase": plan.task_breakdown.decision_phase,
                    },
                    "execution_strategy": {
                        "parallel_agents": plan.execution_strategy.parallel_agents,
                        "sequential_after": plan.execution_strategy.sequential_after,
                        "estimated_time": plan.execution_strategy.estimated_time,
                    },
                    "reasoning": plan.reasoning,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            # Step 3: Collect Market Data (silently, no event)
            yield {
                "type": "status",
                "data": {
                    "stage": "data_collection",
                    "message": "收集市场数据...",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            # Collect data for all agents
            market_data = await data_manager.collect_all()

            # Convert Pydantic model to dict if needed
            if hasattr(market_data, 'dict'):
                market_data_dict = market_data.dict()
            else:
                market_data_dict = market_data

            # Calculate technical indicators for TAAgent if needed
            from app.services.indicators.calculator import IndicatorCalculator
            if market_data_dict.get("btc_ohlcv"):
                indicators = IndicatorCalculator.calculate_all(market_data.btc_ohlcv)
                market_data_dict["indicators"] = indicators

            # Step 4: Execute Business Agents in Parallel
            yield {
                "type": "status",
                "data": {
                    "stage": "analysis",
                    "message": "执行多维度分析...",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            agent_outputs = await self._execute_business_agents(
                plan.execution_strategy.parallel_agents,
                market_data_dict,
                user_message,
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )

            # Yield each agent's result
            for agent_name, output in agent_outputs.items():
                result_data = {
                    "agent_name": agent_name,
                    "signal": output.signal.value,
                    "confidence": output.confidence,
                    "reasoning": output.reasoning,  # 显示完整内容
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Add agent-specific data
                if agent_name == "ta_agent":
                    # Add technical indicators for TAAgent
                    result_data["technical_indicators"] = output.technical_indicators
                    result_data["support_levels"] = output.support_levels
                    result_data["resistance_levels"] = output.resistance_levels
                    result_data["trend_analysis"] = output.trend_analysis
                    result_data["key_patterns"] = output.key_patterns
                elif agent_name == "macro_agent":
                    # Add macro indicators for MacroAgent
                    result_data["macro_indicators"] = output.macro_indicators
                    result_data["key_factors"] = output.key_factors
                    result_data["risk_assessment"] = output.risk_assessment

                    # Add market data context for MacroAgent
                    btc_price_obj = market_data_dict.get("btc_price", {})
                    macro_data = market_data_dict.get("macro", {})
                    fear_greed_data = market_data_dict.get("fear_greed", {})

                    result_data["market_context"] = {
                        "btc_price": btc_price_obj.get("price") if isinstance(btc_price_obj, dict) else btc_price_obj,
                        "price_change_24h": btc_price_obj.get("price_change_24h") if isinstance(btc_price_obj, dict) else None,
                        "dxy_index": macro_data.get("dxy_index"),
                        "fed_rate": macro_data.get("fed_rate_prob"),
                        "m2_growth": macro_data.get("m2_growth"),
                        "treasury_yield": macro_data.get("treasury_yield_10y"),
                        "fear_greed_value": fear_greed_data.get("value"),
                        "fear_greed_classification": fear_greed_data.get("classification"),
                    }
                elif agent_name == "onchain_agent":
                    # Add on-chain metrics for OnChainAgent
                    result_data["onchain_metrics"] = output.onchain_metrics
                    result_data["network_health"] = output.network_health
                    result_data["key_observations"] = output.key_observations

                yield {
                    "type": "agent_result",
                    "data": result_data,
                }

            # Step 5: GeneralAnalysisAgent Synthesis
            yield {
                "type": "status",
                "data": {
                    "stage": "synthesis",
                    "message": "整合分析结果...",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            final_analysis = await general_analysis_agent.synthesize(
                user_message, agent_outputs, chat_history
            )

            yield {
                "type": "final_answer",
                "data": {
                    "answer": final_analysis.answer,
                    "summary": final_analysis.summary,
                    "key_insights": final_analysis.key_insights,
                    "confidence": final_analysis.confidence,
                    "sources": final_analysis.sources,
                    "metadata": final_analysis.metadata,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"❌ Workflow error: {e}")
            print(f"Traceback:\n{error_traceback}")

            yield {
                "type": "error",
                "data": {
                    "error": str(e),
                    "message": "分析过程中发生错误，请稍后重试",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

    async def _execute_business_agents(
        self,
        agent_names: List[str],
        market_data: Dict[str, Any],
        user_message: str = "",
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute business agents in parallel

        Args:
            agent_names: List of agent names to execute
            market_data: Market data collected
            user_message: User's original question (for context)
            db: Database session for recording executions
            user_id: User ID for tracking
            conversation_id: Conversation ID for tracking

        Returns:
            Dictionary of agent outputs {agent_name: output}
        """
        tasks = []
        valid_agent_names = []

        for agent_name in agent_names:
            # Check if agent is available
            if not agent_registry.is_agent_available(agent_name):
                print(f"⚠️  Agent {agent_name} not available, skipping")
                continue

            # Get agent instance
            agent = self.agent_map.get(agent_name)
            if not agent:
                print(f"⚠️  Agent {agent_name} not in agent_map, skipping")
                continue

            # Create task
            tasks.append(
                self._run_agent(
                    agent,
                    agent_name,
                    market_data,
                    user_message,
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )
            )
            valid_agent_names.append(agent_name)

        # Execute all agents in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build output dictionary
        agent_outputs = {}
        for agent_name, result in zip(valid_agent_names, results):
            if isinstance(result, Exception):
                print(f"❌ Error running {agent_name}: {result}")
                continue

            agent_outputs[agent_name] = result

        return agent_outputs

    async def _run_agent(
        self,
        agent: Any,
        agent_name: str,
        market_data: Dict[str, Any],
        user_message: str = "",
        db: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
    ) -> Any:
        """
        Run a single business agent

        Args:
            agent: Agent instance
            agent_name: Agent name
            market_data: Market data snapshot (dict)
            user_message: User's original question (for context)
            db: Database session for recording
            user_id: User ID for tracking
            conversation_id: Conversation ID for tracking

        Returns:
            Agent output
        """
        start_time = time.time()

        try:
            # Prepare agent-specific data and execute
            output = None
            agent_data = {}

            if agent_name == "macro_agent":
                # MacroAgent needs specific data format
                btc_price_obj = market_data.get("btc_price", {})
                agent_data = {
                    "btc_price": btc_price_obj.get("price") if isinstance(btc_price_obj, dict) else btc_price_obj,
                    "price_change_24h": btc_price_obj.get("price_change_24h") if isinstance(btc_price_obj, dict) else 0,
                    "macro": market_data.get("macro"),
                    "fear_greed": market_data.get("fear_greed"),
                }
                output = await agent.analyze(agent_data)

            elif agent_name == "ta_agent":
                # TAAgent needs technical indicators
                btc_price_obj = market_data.get("btc_price", {})
                agent_data = {
                    "btc_price": btc_price_obj.get("price") if isinstance(btc_price_obj, dict) else btc_price_obj,
                    "price_change_24h": btc_price_obj.get("price_change_24h") if isinstance(btc_price_obj, dict) else 0,
                    "indicators": market_data.get("indicators"),
                }
                output = await agent.analyze(agent_data)

            elif agent_name == "onchain_agent":
                # OnChainAgent needs on-chain data from free APIs
                onchain_data = await data_manager.collect_for_onchain_agent()
                output = await agent.analyze(user_message, onchain_data)
                agent_data = onchain_data  # For recording

            else:
                # Generic fallback
                output = await agent.analyze(market_data)
                agent_data = market_data

            # Calculate execution duration
            execution_duration_ms = int((time.time() - start_time) * 1000)

            # Record agent execution to database (if db session provided)
            if db and output:
                try:
                    # Prepare LLM info (from agent's last LLM call if available)
                    llm_info = {
                        "provider": getattr(agent, "last_llm_provider", "tuzi"),
                        "model": getattr(agent, "last_llm_model", "claude-sonnet-4-5"),
                        "prompt": getattr(agent, "last_llm_prompt", None),
                        "response": getattr(agent, "last_llm_response", None),
                        "tokens_used": getattr(agent, "last_tokens_used", None),
                        "cost": getattr(agent, "last_llm_cost", None),
                    }

                    # Record based on agent type
                    if agent_name == "macro_agent":
                        await agent_execution_recorder.record_macro_agent(
                            db=db,
                            output=output,
                            market_data=market_data,
                            llm_info=llm_info,
                            caller_type="research_chat",
                            caller_id=conversation_id,
                            user_id=user_id,
                            execution_duration_ms=execution_duration_ms,
                        )
                    elif agent_name == "ta_agent":
                        await agent_execution_recorder.record_ta_agent(
                            db=db,
                            output=output,
                            market_data=market_data,
                            llm_info=llm_info,
                            caller_type="research_chat",
                            caller_id=conversation_id,
                            user_id=user_id,
                            execution_duration_ms=execution_duration_ms,
                        )
                    elif agent_name == "onchain_agent":
                        await agent_execution_recorder.record_onchain_agent(
                            db=db,
                            output=output,
                            market_data=market_data,
                            llm_info=llm_info,
                            caller_type="research_chat",
                            caller_id=conversation_id,
                            user_id=user_id,
                            execution_duration_ms=execution_duration_ms,
                        )

                    print(f"✅ Recorded {agent_name} execution to database")

                except Exception as record_error:
                    # Don't fail the workflow if recording fails
                    print(f"⚠️  Failed to record {agent_name} execution: {record_error}")

            return output

        except Exception as e:
            print(f"Error in {agent_name}: {e}")
            raise


# Global workflow instance
research_workflow = ResearchWorkflow()
