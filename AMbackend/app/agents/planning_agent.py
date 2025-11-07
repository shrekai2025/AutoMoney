"""PlanningAgent - Research Task Planning and Orchestration"""

from typing import List, Dict, Any

from app.services.llm.manager import llm_manager
from app.schemas.llm import Message
from app.schemas.research import (
    PlanningAgentOutput,
    TaskBreakdown,
    AgentPlan,
    ExecutionStrategy,
)
from app.agents.registry import agent_registry
from app.utils.json_parser import parse_llm_json, JSONParseError


class PlanningAgent:
    """
    PlanningAgent decomposes complex research questions into tasks

    Uses Claude Sonnet 4.5 Thinking for strategic planning:
    - Analyzes user question and determines required analyses
    - Selects appropriate business agents (MacroAgent, TAAgent, OnChainAgent)
    - Plans execution strategy (parallel vs sequential)
    - Defines data requirements for each agent
    """

    SYSTEM_PROMPT_TEMPLATE = """You are a strategic planning agent for cryptocurrency market research.

Your role is to analyze complex user questions and create a comprehensive research plan by:
1. Breaking down the question into analysis tasks
2. Selecting appropriate specialized agents (ONLY from available agents below)
3. Planning execution strategy (parallel/sequential)
4. Defining data requirements

**CRITICAL**: You can ONLY select agents from the "Available Business Agents" list below.
Do NOT plan for agents that are not listed. If an agent you想要的 is not available, work with what's available.

## Available Business Agents:

{available_agents}

---

### GeneralAnalysisAgent (general_analysis_agent)
**Specialization**: Synthesis and final answer generation
**Always runs in decision_phase** after all business agents complete
**Integrates all agent outputs and provides final answer to user**

## Planning Guidelines:

### Analysis Phase Planning:
1. **Select Agents**: Choose 1-3 business agents based on question type
2. **Set Priority**:
   - high: Critical for answering the question
   - medium: Helpful but not essential
   - low: Nice to have, contextual
3. **Define Data Needs**: List specific data points each agent should analyze
4. **Provide Reasoning**: Explain why each agent is needed

### Execution Strategy:
- **Parallel agents**: Business agents that can run simultaneously (macro_agent, ta_agent, onchain_agent)
- **Sequential after**: Always include general_analysis_agent after business agents complete
- **Estimated time**: Realistic estimate (e.g., "20-30秒" for 2-3 agents)

### Common Question Types:

**Investment Decision** ("现在适合买BTC吗?"):
- macro_agent (high): Macro conditions for risk assets
- ta_agent (high): Technical entry/exit points
- onchain_agent (medium): Whale behavior signals

**Market Analysis** ("分析当前BTC市场"):
- macro_agent (high): Macro drivers
- ta_agent (high): Price action and trends
- onchain_agent (medium): On-chain signals

**Cause Analysis** ("为什么BTC最近下跌?"):
- macro_agent (high): Macro headwinds
- ta_agent (medium): Technical breakdown levels
- onchain_agent (low): On-chain activity changes

**Prediction** ("BTC会涨到多少?"):
- macro_agent (high): Macro tailwinds/headwinds
- ta_agent (high): Technical targets and resistance
- onchain_agent (medium): Accumulation/distribution patterns

## Output Format:

⚠️ CRITICAL OUTPUT REQUIREMENTS:

1. ❌ ABSOLUTELY NO MARKDOWN in JSON string values (no **, ##, -, *, etc.)
2. ❌ NO markdown code blocks (no ```json or ```)
3. ❌ NO extra text before or after the JSON
4. ❌ NO thinking, explanations, or commentary outside JSON
5. ✅ Use plain text in "reasoning" and other string fields
6. ✅ Use \n for line breaks in strings (NOT real newlines)
7. ✅ Start response with {{ and end with }}
8. ✅ Use double quotes for all strings
9. ✅ Escape special characters properly

You MUST respond with ONLY valid JSON (no markdown, no extra text):

Example JSON format (replace with your actual analysis):
{{
    "task_breakdown": {{
        "analysis_phase": [
            {{
                "agent": "macro_agent",
                "reason": "Need to analyze macroeconomic environment (Fed rates, dollar index, market sentiment)",
                "data_required": ["fed_rate", "dxy", "fear_greed", "m2_growth"],
                "priority": "high"
            }}
        ],
        "decision_phase": {{
            "agent": "general_analysis_agent",
            "reason": "Synthesize all analysis and provide clear recommendations based on user's question",
            "synthesis_required": true
        }}
    }},
    "execution_strategy": {{
        "parallel_agents": ["macro_agent"],
        "sequential_after": ["general_analysis_agent"],
        "estimated_time": "10-15 seconds"
    }},
    "reasoning": "This is a typical investment decision question requiring multi-dimensional analysis..."
}}

**CRITICAL**:
- analysis_phase must be an array of agent plans
- Each agent plan must have: agent, reason, data_required, priority
- decision_phase always includes general_analysis_agent
- parallel_agents should list business agents that can run concurrently
- sequential_after should always include ["general_analysis_agent"]

⚠️ FINAL REMINDER: Respond with ONLY the JSON object. NO MARKDOWN formatting in string values. Start with {{{{ and end with }}}}.
"""

    def __init__(self):
        """Initialize PlanningAgent"""
        self.agent_name = "planning_agent"

    async def plan(
        self, user_message: str, chat_history: List[Dict[str, Any]] = None
    ) -> PlanningAgentOutput:
        """
        Create execution plan for complex research question

        Args:
            user_message: User's question
            chat_history: Recent chat history

        Returns:
            PlanningAgentOutput with task breakdown and execution strategy
        """
        # Get available agents dynamically
        available_agents_desc = agent_registry.get_agent_descriptions_for_llm()
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(
            available_agents=available_agents_desc
        )

        # Build planning prompt
        prompt = self._build_planning_prompt(user_message, chat_history or [])

        # Prepend system prompt for Claude Thinking
        full_prompt = f"{system_prompt}\n\n{prompt}"

        # Call LLM (Claude Sonnet 4.5 Thinking)
        messages = [Message(role="user", content=full_prompt)]

        response = await llm_manager.chat_for_agent(
            agent_name=self.agent_name, messages=messages
        )

        # Parse response
        output = self._parse_llm_response(response.content)

        return PlanningAgentOutput(
            task_breakdown=TaskBreakdown(
                analysis_phase=[
                    AgentPlan(**plan) for plan in output["task_breakdown"]["analysis_phase"]
                ],
                decision_phase=output["task_breakdown"]["decision_phase"],
            ),
            execution_strategy=ExecutionStrategy(**output["execution_strategy"]),
            reasoning=output["reasoning"],
        )

    def _build_planning_prompt(
        self, user_message: str, chat_history: List[Dict[str, Any]]
    ) -> str:
        """Build the planning prompt"""
        prompt = f"""**User's Research Question:**
"{user_message}"
"""

        if chat_history:
            prompt += "\n**Recent Chat Context:**\n"
            for msg in chat_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt += f"- {role}: {content[:100]}...\n"

        prompt += """
Analyze the user's question and create a comprehensive research plan.

Consider:
1. What type of question is this? (investment decision, market analysis, prediction, etc.)
2. Which agents are ESSENTIAL to answer this question?
3. Which agents would provide HELPFUL but non-critical context?
4. What specific data should each agent analyze?
5. Can agents run in parallel or must some wait for others?

⚠️ REMINDER: Return ONLY the JSON plan. NO markdown formatting in string values (no **, ##, etc.). Start with {{ and end with }}.
"""

        return prompt

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract planning output

        Args:
            content: Raw LLM response content

        Returns:
            Parsed planning dictionary
        """
        try:
            # Use robust JSON parser
            output = parse_llm_json(
                content,
                expected_fields=["task_breakdown", "execution_strategy", "reasoning"]
            )

            # Validate task_breakdown structure
            task_breakdown = output["task_breakdown"]
            if "analysis_phase" not in task_breakdown:
                raise ValueError("Missing analysis_phase in task_breakdown")
            if "decision_phase" not in task_breakdown:
                raise ValueError("Missing decision_phase in task_breakdown")

            # Validate execution_strategy structure
            exec_strategy = output["execution_strategy"]
            required_exec_fields = ["parallel_agents", "sequential_after", "estimated_time"]
            for field in required_exec_fields:
                if field not in exec_strategy:
                    raise ValueError(f"Missing {field} in execution_strategy")

            return output

        except (JSONParseError, ValueError) as e:
            # Fallback: create a basic plan with available agents only
            print(f"Error parsing PlanningAgent response: {e}")
            print(f"Raw content: {content[:500]}...")

            # Get available agents dynamically
            available_agent_names = agent_registry.get_available_agent_names()

            # Create analysis phase with available agents
            analysis_phase = []
            for agent_name in available_agent_names:
                agent_info = agent_registry.get_agent_info(agent_name)
                analysis_phase.append({
                    "agent": agent_name,
                    "reason": agent_info.description,
                    "data_required": agent_info.data_sources[:3],  # First 3 data sources
                    "priority": agent_info.priority_hint,
                })

            return {
                "task_breakdown": {
                    "analysis_phase": analysis_phase,
                    "decision_phase": {
                        "agent": "general_analysis_agent",
                        "reason": "Synthesize analysis results and generate final response",
                        "synthesis_required": True,
                    },
                },
                "execution_strategy": {
                    "parallel_agents": available_agent_names,
                    "sequential_after": ["general_analysis_agent"],
                    "estimated_time": f"{len(available_agent_names) * 10}-{len(available_agent_names) * 15} seconds",
                },
                "reasoning": f"Failed to parse planning output. Using default plan with available agents. Error: {str(e)}",
            }


# Global PlanningAgent instance
planning_agent = PlanningAgent()
